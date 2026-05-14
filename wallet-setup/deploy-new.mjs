// deploy-new.mjs
//
// Deploys AMM + Vault + Registry contracts to Arc Testnet via Circle SDK.
// Run AFTER deploy.mjs (which deploys the synthetic assets).
//
// Usage: node --env-file=../.env deploy-new.mjs

import crypto from "crypto";
import fs from "fs";
import path from "path";

const API_KEY = process.env.CIRCLE_API_KEY;
const ENTITY_SECRET = process.env.CIRCLE_ENTITY_SECRET;
const WALLET_ID = process.env.WALLET_ID;
const WALLET_ADDRESS = process.env.WALLET_ADDRESS;

if (!API_KEY || !ENTITY_SECRET || !WALLET_ID || !WALLET_ADDRESS) {
  console.error("ERROR: Need CIRCLE_API_KEY, CIRCLE_ENTITY_SECRET, WALLET_ID, WALLET_ADDRESS");
  process.exit(1);
}

const OUT_DIR = path.resolve(import.meta.dirname, "../contracts/out");
const USDC = "0x3600000000000000000000000000000000000000";
const API = "https://api.circle.com/v1/w3s";

// ─── Helpers ────────────────────────────────────────────────────────

let ciphertextCache = null;

async function getCiphertext() {
  if (ciphertextCache) return ciphertextCache;
  const pkRes = await fetch(`${API}/config/entity/publicKey`, {
    headers: { Authorization: `Bearer ${API_KEY}`, Accept: "application/json" },
  });
  const { data } = await pkRes.json();
  const pub = crypto.createPublicKey({ key: data.publicKey, format: "pem" });
  ciphertextCache = crypto.publicEncrypt(
    { key: pub, padding: crypto.constants.RSA_PKCS1_OAEP_PADDING, oaepHash: "sha256" },
    Buffer.from(ENTITY_SECRET, "hex")
  ).toString("base64");
  return ciphertextCache;
}

function loadArtifact(name) {
  const f = path.join(OUT_DIR, `${name}.sol`, `${name}.json`);
  const a = JSON.parse(fs.readFileSync(f, "utf8"));
  const bc = a.bytecode.object;
  return { abi: a.abi, bytecode: bc.startsWith("0x") ? bc : "0x" + bc };
}

function wait(ms) { return new Promise(r => setTimeout(r, ms)); }

async function apiPost(endpoint, body) {
  const res = await fetch(`${API}${endpoint}`, {
    method: "POST",
    headers: { Authorization: `Bearer ${API_KEY}`, "Content-Type": "application/json", Accept: "application/json" },
    body: JSON.stringify(body),
  });
  const data = await res.json();
  if (res.status >= 400) throw new Error(`API ${res.status}: ${JSON.stringify(data)}`);
  return data;
}

async function deployContract(name, artifact, constructorParams) {
  ciphertextCache = null;
  const entitySecretCiphertext = await getCiphertext();
  console.log(`  Deploying ${name}...`);
  const res = await apiPost("/contracts/deploy", {
    idempotencyKey: crypto.randomUUID(),
    name,
    walletId: WALLET_ID,
    blockchain: "ARC-TESTNET",
    abiJson: JSON.stringify(artifact.abi),
    bytecode: artifact.bytecode,
    constructorParameters: constructorParams,
    entitySecretCiphertext,
    feeLevel: "MEDIUM",
  });
  const contractId = res.data?.contractId;
  if (!contractId) throw new Error(`No contractId returned: ${JSON.stringify(res.data)}`);

  // Wait for deployment
  const start = Date.now();
  while (Date.now() - start < 180_000) {
    const check = await fetch(`${API}/contracts/${contractId}`, {
      headers: { Authorization: `Bearer ${API_KEY}`, Accept: "application/json" },
    });
    const checkData = await check.json();
    const c = checkData.data?.contract;
    if (c?.status === "COMPLETE" && c.contractAddress) {
      console.log(`  ✅ ${name} → ${c.contractAddress}`);
      return c.contractAddress;
    }
    if (c?.status === "FAILED") throw new Error(`Contract ${name} failed: ${JSON.stringify(c)}`);
    process.stdout.write(".");
    await wait(3000);
  }
  throw new Error(`Timeout deploying ${name}`);
}

async function callContract(contractAddress, signature, params) {
  ciphertextCache = null;
  const entitySecretCiphertext = await getCiphertext();
  const res = await apiPost("/developer/transactions/contractExecution", {
    idempotencyKey: crypto.randomUUID(),
    walletId: WALLET_ID,
    contractAddress,
    abiFunctionSignature: signature,
    abiParameters: params,
    feeLevel: "MEDIUM",
    entitySecretCiphertext,
  });
  const txId = res.data?.id;
  if (!txId) throw new Error(`No txId: ${JSON.stringify(res.data)}`);

  // Wait for tx
  const start = Date.now();
  while (Date.now() - start < 60_000) {
    const check = await fetch(`${API}/transactions/${txId}`, {
      headers: { Authorization: `Bearer ${API_KEY}`, Accept: "application/json" },
    });
    const checkData = await check.json();
    const tx = checkData.data?.transaction;
    if (tx?.state === "COMPLETE") return txId;
    if (tx?.state === "FAILED") throw new Error(`TX ${txId} failed`);
    await wait(3000);
  }
  console.log(`  ⚠️ TX ${txId} timed out (may still succeed)`);
  return txId;
}

// ─── Load existing deployed addresses from .env ────────────────────

function getEnv(key) {
  const envPath = path.resolve(import.meta.dirname, "../.env");
  const content = fs.existsSync(envPath) ? fs.readFileSync(envPath, "utf8") : "";
  const m = content.match(new RegExp(`${key}=(.*)`, "m"));
  return m ? m[1].trim() : null;
}

function setEnv(key, value) {
  const envPath = path.resolve(import.meta.dirname, "../.env");
  let content = fs.existsSync(envPath) ? fs.readFileSync(envPath, "utf8") : "";
  if (content.includes(`${key}=`)) {
    content = content.replace(new RegExp(`${key}=.*`), `${key}=${value}`);
  } else {
    content += `\n${key}=${value}`;
  }
  fs.writeFileSync(envPath, content);
}

// ─── Main ───────────────────────────────────────────────────────────

async function main() {
  console.log("=== Deploying AMM + Vault + Registry Contracts ===\n");

  const ammRouterArt = loadArtifact("AMMRouter");
  const vaultFactoryArt = loadArtifact("VaultFactory");
  const traceRegArt = loadArtifact("ReasoningTraceRegistry");
  const assetRegArt = loadArtifact("AssetRegistry");

  // 1. Deploy AMMRouter
  let ammRouterAddr = getEnv("AMM_ROUTER");
  if (ammRouterAddr) {
    console.log(`AMMRouter already deployed: ${ammRouterAddr}`);
  } else {
    ammRouterAddr = await deployContract("Archimedes AMMRouter", ammRouterArt, [WALLET_ADDRESS]);
    setEnv("AMM_ROUTER", ammRouterAddr);
  }

  // 2. Deploy ReasoningTraceRegistry
  let traceRegAddr = getEnv("TRACE_REGISTRY");
  if (traceRegAddr) {
    console.log(`ReasoningTraceRegistry already deployed: ${traceRegAddr}`);
  } else {
    traceRegAddr = await deployContract("Archimedes TraceRegistry", traceRegArt, [WALLET_ADDRESS]);
    setEnv("TRACE_REGISTRY", traceRegAddr);
  }

  // 3. Deploy AssetRegistry
  let assetRegAddr = getEnv("ASSET_REGISTRY");
  if (assetRegAddr) {
    console.log(`AssetRegistry already deployed: ${assetRegAddr}`);
  } else {
    assetRegAddr = await deployContract("Archimedes AssetRegistry", assetRegArt, [WALLET_ADDRESS]);
    setEnv("ASSET_REGISTRY", assetRegAddr);
  }

  // 4. Deploy VaultFactory
  //    constructor(agent, ammRouter, usdc, platformFeeRecipient, owner)
  let vaultFactoryAddr = getEnv("VAULT_FACTORY");
  if (vaultFactoryAddr) {
    console.log(`VaultFactory already deployed: ${vaultFactoryAddr}`);
  } else {
    vaultFactoryAddr = await deployContract("Archimedes VaultFactory", vaultFactoryArt, [
      WALLET_ADDRESS,  // agent address
      ammRouterAddr,    // AMM router
      USDC,             // USDC
      WALLET_ADDRESS,   // platform fee recipient
      WALLET_ADDRESS,   // owner
    ]);
    setEnv("VAULT_FACTORY", vaultFactoryAddr);
  }

  // 5. Create AMM Pools for each synthetic asset
  const tokenAddrs = [
    { sym: "sTSLA", env: "TSLA_TOKEN" },
    { sym: "sNVDA", env: "NVDA_TOKEN" },
    { sym: "sSPY",  env: "SPY_TOKEN" },
    { sym: "sBTC",  env: "BTC_TOKEN" },
    { sym: "sGOLD", env: "GOLD_TOKEN" },
    { sym: "sOIL",  env: "OIL_TOKEN" },
    { sym: "sNKY",  env: "NIKKEI_TOKEN" },
  ];

  console.log("\n=== Creating AMM Pools ===");
  const ammPoolArt = loadArtifact("AMMPool");
  for (const t of tokenAddrs) {
    const tokenAddr = getEnv(t.env);
    if (!tokenAddr) {
      console.log(`  ${t.sym}: SKIP (no token address)`);
      continue;
    }

    const poolEnvKey = `AMM_POOL_${t.sym}`;
    let poolAddr = getEnv(poolEnvKey);
    if (poolAddr) {
      console.log(`  ${t.sym}/USDC pool already exists: ${poolAddr}`);
      continue;
    }

    try {
      // createPool on router: (tokenA, tokenB)
      const txId = await callContract(ammRouterAddr, "createPool(address,address)", [USDC, tokenAddr]);
      console.log(`  ✅ ${t.sym}/USDC pool created (tx: ${txId})`);
      // Note: getting the pool address requires reading the PoolCreated event
      // For now, we'll read it via getPool in the test UI
    } catch (err) {
      console.log(`  ⚠️ ${t.sym}/USDC pool: ${err.message}`);
    }
  }

  console.log("\n=== Deployment Complete ===");
  console.log(`AMM_ROUTER=${ammRouterAddr}`);
  console.log(`VAULT_FACTORY=${vaultFactoryAddr}`);
  console.log(`TRACE_REGISTRY=${traceRegAddr}`);
  console.log(`ASSET_REGISTRY=${assetRegAddr}`);
  console.log("\nSaved to .env");
}

main().catch((err) => {
  console.error("\nFailed:", err.message || err);
  process.exit(1);
});
