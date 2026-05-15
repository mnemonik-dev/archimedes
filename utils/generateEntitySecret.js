import { generateEntitySecret } from "@circle-fin/developer-controlled-wallets";

const entitySecret = generateEntitySecret({
  apiKey: "TEST_API_KEY:70dfe02ea2770aeac105eeba4d93bfc2:f207ec6a3839ebb8ebbe6f837664fcaa", // Replace with your actual key
  recoveryFileDownloadPath: "./recovery",
});

console.log("Entity Secret:", entitySecret);