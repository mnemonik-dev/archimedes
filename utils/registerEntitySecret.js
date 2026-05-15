import { registerEntitySecretCiphertext } from "@circle-fin/developer-controlled-wallets";

const response = await registerEntitySecretCiphertext({
  apiKey: 'TEST_API_KEY:70dfe02ea2770aeac105eeba4d93bfc2:f207ec6a3839ebb8ebbe6f837664fcaa',
  entitySecret: '340f511c245bf92c753b0afddffc971cd389617d9fa26303290325ac3ad9bfea',
  recoveryFileDownloadPath: "./recovery",
});

console.log(response.data?.recoveryFile);

// AAABnilIqjR5D4CLJMSpCc44agZ5AAAAAFCOPS9O7bmjsW5mFjXgXbrGkoE8KNue+DLBr2otW3wve5r6703h3hfToPwIivB2QKwebNtZCI3ZeDvAPitIUGQTWVNjkU/3EkToFH0ieiDkLg==