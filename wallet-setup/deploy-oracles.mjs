// deploy-oracles.mjs
//
// Deploys 5 new PriceOracles (with updater role) via Circle Wallets API.
// Then sets the oracle addresses on each vault via setTokenOracles.
//
// Usage: node --env-file=../.env deploy-oracles.mjs

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

const API = "https://api.circle.com/v1/w3s";
const BLOCKCHAIN = "arc-testnet";

// Load compiled PriceOracle artifact
const artifactPath = path.resolve(import.meta.dirname, "../contracts/out/PriceOracle.sol/PriceOracle.json");
const artifact = JSON.parse(fs.readFileSync(artifactPath, "utf-8"));
const bytecode = artifact.bytecode.object;
const abi = artifact.abi;

// Assets: symbol → initial price (6 decimals)
const ASSETS = [
  { symbol: "sTSLA", price: "285500000" },
  { symbol: "sNVDA", price: "135200000" },
  { symbol: "sSPY",  price: "592400000" },
  { symbol: "sBTC",  price: "104500000000" },
  { symbol: "sGOLD", price: "3250000000" },
];

// Vaults: name → address
const VAULTS = {
  vMOM: "0x827a2584317cEd061685d97841f60a5feA0ab1d9",
  vYLD: "0xA492Fb80F0AFbD4bd75325c15d6C91Ad9e11362b",
  vDEGN: "0xf7ad098f3b2138f6ab1b260366d0Bd7a91fd356c",
  vSAFE: "0x60Df04A366e7556146A12a4F727D6861086C29Ed",
  vMFQ: "0x5f00B73B64f9c4f3D5723072eaA9194cD47810f6",
};

// Synth token addresses
const TOKENS = {
  sTSLA: "0xE745C07d7d32A1Ca0d6162A1c50e876619CF7388",
  sNVDA: "0xC297A15E702C910b71Ac531c6633aFDd90389e1d",
  sSPY:  "0x04315D3c35639288949cEE1d1E01Bd6100aDf3f5",
  sBTC:  "0xdDbac3Cf2feb7192f963e6a9bB4DE0822C3DF4DB",
  sGOLD: "0xb13Eb59d8CDfACeDE2990207651e8649bdf7A89f",
};

// USDC address (also needs oracle for vault totalAssets)
const USDC = "0x3600000000000000000000000000000000000000";

async function getCiphertext() {
  const pkRes = await fetch(`${API}/config/entity/publicKey`, {
    headers: { Authorization: `Bearer ${API_KEY}`, Accept: "application/json" },
  });
  const { data } = await pkRes.json();
  const pub = crypto.createPublicKey({ key: data.publicKey, format: "pem" });
  return crypto.publicEncrypt(
    { key: pub, padding: crypto.constants.RSA_PKCS1_OAEP_PADDING, oaepHash: "sha256" },
    Buffer.from(ENTITY_SECRET, "hex")
  ).toString("base64");
}

async function submitTx(payload) {
  const resp = await fetch(`${API}/developer/transactions/contractExecution`, {
    method: "POST",
    headers: {
      Authorization: `Bearer ${API_KEY}`,
      "Content-Type": "application/json",
    },
    body: JSON.stringify(payload),
  });
  const body = await resp.json();
  if (resp.status === 201) {
    return body.data.id;
  }
  console.error("  TX FAILED:", JSON.stringify(body));
  return null;
}

async function deployContract(ciphertext, symbol, price) {
  // Encode constructor args: (string _symbol, uint256 _initialPrice, address _owner)
  // Using ethers-like encoding manually with ABI
  // constructor(string,uint256,address)
  
  // Manual ABI encoding for constructor
  const iface = new (await import("ethers")).Interface(abi);
  const constructorFragment = abi.find(a => a.type === "constructor");
  
  // We need to encode the constructor args ourselves
  // Using the ethers Interface
  const deployData = iface.deployTransaction.bytecode; // won't work this way
  
  // Simplest: use raw encoding
  // string symbol → offset + bytes
  // uint256 price
  // address owner
  const encoder = new TextEncoder();
  
  // Actually, let's just use ethers.utils.defaultAbiCoder
  const { defaultAbiCoder } = await import("ethers");
  // Wait, ethers v6 has different imports
  
  // Let me just hardcode the encoding
  // Use Node.js with web3-style encoding
  const { encodeFunctionData, encodeAbiParameters, parseAbiParameters } = await import("viem");
  
  // Hmm, this is getting complicated. Let me just use the bytecode + manual ABI encoding
  // The constructor is: (string, uint256, address)
  
  console.log(`  Deploying ${symbol} oracle...`);
  
  // Actually, let's just use forge to get the deployment data
  // or use a simpler approach with cast
  return null;
}

async function main() {
  console.log("=== Deploying 5 new PriceOracles ===\n");
  
  const ciphertext = await getCiphertext();
  const deployedOracles = {};
  
  // Deploy each oracle by calling the Circle API with bytecode + constructor args
  // We need to encode constructor args manually
  // PriceOracle constructor: (string _symbol, uint256 _initialPrice, address _owner)
  
  for (const { symbol, price } of ASSETS) {
    // ABI-encode constructor args: string, uint256, address
    const encoded = encodeConstructorArgs(symbol, BigInt(price), WALLET_ADDRESS);
    const fullBytecode = bytecode + encoded.slice(2); // remove 0x prefix from encoded
    
    const payload = {
      idempotencyKey: crypto.randomUUID(),
      walletId: WALLET_ID,
      bytecode: fullBytecode,
      feeLevel: "MEDIUM",
      blockchain: BLOCKCHAIN,
      entitySecretCiphertext: ciphertext,
    };
    
    const resp = await fetch(`${API}/developer/transactions/deploy`, {
      method: "POST",
      headers: {
        Authorization: `Bearer ${API_KEY}`,
        "Content-Type": "application/json",
      },
      body: JSON.stringify(payload),
    });
    const body = await resp.json();
    
    if (resp.status === 201) {
      const txId = body.data.id;
      console.log(`  ${symbol}: deployed, tx=${txId}`);
      deployedOracles[symbol] = { txId };
    } else {
      console.error(`  ${symbol}: FAILED - ${JSON.stringify(body)}`);
    }
    
    // Small delay between deploys
    await new Promise(r => setTimeout(r, 1000));
  }
  
  console.log("\nWaiting 30s for transactions to confirm...");
  await new Promise(r => setTimeout(r, 30000));
  
  // Get deployed addresses
  console.log("\n=== Checking deployed addresses ===\n");
  for (const [symbol, { txId }] of Object.entries(deployedOracles)) {
    const resp = await fetch(`${API}/developer/transactions/${txId}`, {
      headers: { Authorization: `Bearer ${API_KEY}` },
    });
    const body = await resp.json();
    const tx = body.data?.transaction || {};
    const addr = tx.contractAddress;
    const state = tx.state;
    console.log(`  ${symbol}: state=${state} address=${addr}`);
    if (addr) deployedOracles[symbol].address = addr;
  }
  
  // Now set oracle addresses on vaults via setTokenOracles
  console.log("\n=== Setting oracle addresses on vaults ===\n");
  
  // setTokenOracles(address[] tokens, address[] oracles)
  const allTokens = Object.values(TOKENS);
  const allOracles = ASSETS.map(a => deployedOracles[a.symbol]?.address).filter(Boolean);
  
  if (allOracles.length === 5) {
    for (const [vname, vaddr] of Object.entries(VAULTS)) {
      // Encode setTokenOracles call
      const callData = encodeSetTokenOracles(allTokens, allOracles);
      
      const payload = {
        idempotencyKey: crypto.randomUUID(),
        walletId: WALLET_ID,
        contractAddress: vaddr,
        abiFunctionSignature: "setTokenOracles(address[],address[])",
        abiParameters: [allTokens, allOracles],
        feeLevel: "MEDIUM",
        blockchain: BLOCKCHAIN,
        entitySecretCiphertext: ciphertext,
      };
      
      const resp = await fetch(`${API}/developer/transactions/contractExecution`, {
        method: "POST",
        headers: {
          Authorization: `Bearer ${API_KEY}`,
          "Content-Type": "application/json",
        },
        body: JSON.stringify(payload),
      });
      const body = await resp.json();
      
      if (resp.status === 201) {
        console.log(`  ${vname} (${vaddr}): setTokenOracles tx=${body.data.id}`);
      } else {
        console.error(`  ${vname}: FAILED - ${JSON.stringify(body)}`);
      }
      
      await new Promise(r => setTimeout(r, 1000));
    }
  } else {
    console.error("Not all oracles deployed, skipping vault oracle mapping update");
  }
  
  console.log("\n=== Done. Oracle addresses: ===");
  for (const [symbol, info] of Object.entries(deployedOracles)) {
    console.log(`  ${symbol}: ${info.address || "FAILED"}`);
  }
}

// Helper: ABI-encode constructor args (string, uint256, address)
function encodeConstructorArgs(symbol, price, owner) {
  // Manual Solidity ABI encoding:
  // Offset to string (32 bytes): 0x60 (= 96 bytes offset for the dynamic data)
  // uint256 price (32 bytes)
  // address owner (32 bytes, left-padded)
  // String length (32 bytes)
  // String data (padded to 32 bytes)
  
  const symbolBytes = Buffer.from(symbol, "utf-8");
  const stringSlotCount = Math.ceil(symbolBytes.length / 32);
  
  const buf = Buffer.alloc(96 + 32 + stringSlotCount * 32);
  
  // Offset to string dynamic data = 96 (3 static slots × 32)
  buf.writeBigUInt64BE(0n, 24); // offset = 96 (stored in last 8 bytes of first 32-byte slot)
  // Wait, need proper uint256 encoding
  buf.writeBigUInt64BE(96n, 24);
  
  // uint256 price
  let priceBuf = Buffer.alloc(32);
  priceBuf.writeBigUInt64BE(BigInt(price), 24);
  priceBuf.copy(buf, 32);
  
  // address (left-padded to 32 bytes)
  const addrBuf = Buffer.alloc(32);
  addrBuf.write(owner.replace("0x", "").padStart(64, "0"), 0, "hex");
  addrBuf.copy(buf, 64);
  
  // String length
  let lenBuf = Buffer.alloc(32);
  lenBuf.writeBigUInt64BE(BigInt(symbolBytes.length), 24);
  lenBuf.copy(buf, 96);
  
  // String data (right-padded to 32-byte boundary)
  symbolBytes.copy(buf, 128);
  
  return "0x" + buf.toString("hex");
}

// Helper: encode setTokenOracles(address[], address[])
function encodeSetTokenOracles(tokens, oracles) {
  // This is handled by Circle API's abiParameters field, not needed manually
  return "";
}

main().catch(console.error);
