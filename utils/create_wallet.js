import { initiateDeveloperControlledWalletsClient } from "@circle-fin/developer-controlled-wallets";

const client = initiateDeveloperControlledWalletsClient({
  apiKey: "TEST_API_KEY:70dfe02ea2770aeac105eeba4d93bfc2:f207ec6a3839ebb8ebbe6f837664fcaa",
  entitySecret: "340f511c245bf92c753b0afddffc971cd389617d9fa26303290325ac3ad9bfea",
});

async function main() {
  const walletSetResponse = await client.createWalletSet({
    name: "My First Dev-Controlled Wallet Set",
  });

  const walletSet = walletSetResponse.data?.walletSet;
  if (!walletSet?.id) {
    throw new Error("Wallet set creation failed: no ID returned");
  }

  const walletResponse = await client.createWallets({
    walletSetId: walletSet.id,
    blockchains: ["ARC-TESTNET"], // Can be any supported blockchain
    count: 1,
    accountType: "EOA", // Can be EOA or SCA
  });

  console.log("Wallet set response:", walletSetResponse.data);
  console.log("Wallet response:", walletResponse.data);
}

main().catch((err) => {
  console.error("Error:", err.message || err);
  process.exit(1);
});


/*
Wallet set response: {
  walletSet: {
    id: '4c15ea67-abb6-5e5d-8906-be9122333b56',
    custodyType: 'DEVELOPER',
    name: 'My First Dev-Controlled Wallet Set',
    updateDate: '2026-05-15T01:56:16Z',
    createDate: '2026-05-15T01:56:16Z'
  }
}
Wallet response: {
  wallets: [
    {
      id: 'ec2cc041-de84-53f2-8167-2d689a2aa2f7',
      state: 'LIVE',
      walletSetId: '4c15ea67-abb6-5e5d-8906-be9122333b56',
      custodyType: 'DEVELOPER',
      address: '0xe77a6933c738e1a2722dded68bfb5a699aa86bb0',
      blockchain: 'ARC-TESTNET',
      accountType: 'EOA',
      updateDate: '2026-05-15T01:56:16Z',
      createDate: '2026-05-15T01:56:16Z'
    }
  ]
}
*/