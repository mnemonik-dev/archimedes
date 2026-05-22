import { createPublicClient, createWalletClient, custom, http } from 'viem'

const arcTestnet = {
  id: 5042002,
  name: 'Arc Testnet',
  nativeCurrency: { name: 'USD Coin', symbol: 'USDC', decimals: 18 },
  rpcUrls: { default: { http: ['https://rpc.testnet.arc.network'] } },
}

export const publicClient = createPublicClient({
  chain: arcTestnet,
  transport: http(),
})

// ─── Wallet Connection ──────────────────────────────────────

export const WALLET_PROVIDERS = [
  {
    id: 'metamask',
    name: 'MetaMask',
    icon: '🦊',
    detect: () => {
      if (!window.ethereum) return null
      // MetaMask injects window.ethereum with isMetaMask
      if (window.ethereum.isMetaMask) return window.ethereum
      // Some browsers have multiple wallets — check for MetaMask specifically
      if (window.ethereum.providers?.find(p => p.isMetaMask)) {
        return window.ethereum.providers.find(p => p.isMetaMask)
      }
      return null
    },
  },
  {
    id: 'coinbase',
    name: 'Coinbase Wallet',
    icon: '🔵',
    detect: () => {
      // Coinbase Wallet extension
      if (window.ethereum?.isCoinbaseWallet) return window.ethereum
      // Coinbase injected as separate provider
      if (window.coinbaseWalletExtension) return window.coinbaseWalletExtension
      // Multiple providers — find Coinbase
      if (window.ethereum?.providers?.find(p => p.isCoinbaseWallet)) {
        return window.ethereum.providers.find(p => p.isCoinbaseWallet)
      }
      return null
    },
  },
  {
    id: 'browser',
    name: 'Browser Wallet',
    icon: '🌐',
    detect: () => {
      // Fallback: any window.ethereum provider
      return window.ethereum || null
    },
  },
]

const STORAGE_KEY = 'archimedes_wallet'

let _walletClient = null
let _provider = null
let _address = null
let _providerId = null

export function getConnectedProvider() { return _providerId }
export function getAddress() { return _address }

function saveWalletMeta(providerId, address) {
  try {
    localStorage.setItem(STORAGE_KEY, JSON.stringify({ providerId, address }))
  } catch { /* storage unavailable */ }
}

function clearWalletMeta() {
  try { localStorage.removeItem(STORAGE_KEY) } catch { /* */ }
}

function loadWalletMeta() {
  try {
    const raw = localStorage.getItem(STORAGE_KEY)
    return raw ? JSON.parse(raw) : null
  } catch { return null }
}

// Try to reconnect to a previously connected wallet on page load.
// Uses eth_accounts (non-popup) to check if the user is still authorised.
export async function reconnectWallet() {
  const meta = loadWalletMeta()
  if (!meta) return null

  const provider = WALLET_PROVIDERS.find(p => p.id === meta.providerId)
  if (!provider) { clearWalletMeta(); return null }

  const ethereum = provider.detect()
  if (!ethereum) { clearWalletMeta(); return null }

  try {
    const accounts = await ethereum.request({ method: 'eth_accounts' })
    if (!accounts?.length) { clearWalletMeta(); return null }

    const addr = accounts[0]
    await ensureArcChain(ethereum)

    _provider = ethereum
    _address = addr
    _providerId = meta.providerId
    _walletClient = createWalletClient({
      account: _address,
      chain: arcTestnet,
      transport: custom(ethereum),
    })

    saveWalletMeta(_providerId, _address)
    return { address: _address, provider: _providerId }
  } catch {
    clearWalletMeta()
    return null
  }
}

const ARC_CHAIN_HEX = '0x4cef52'  // 5042002

// MetaMask returns -32002 when a wallet_requestPermissions / eth_requestAccounts
// is already pending — usually because the user dismissed the popup without
// confirming, leaving the request live. Turn this into an actionable message
// instead of bubbling the raw RPC error.
function isAlreadyPendingError(err) {
  return err?.code === -32002
}

async function ensureArcChain(ethereum) {
  // Skip the switch popup if we're already on Arc.
  try {
    const current = await ethereum.request({ method: 'eth_chainId' })
    if (current?.toLowerCase() === ARC_CHAIN_HEX) return
  } catch { /* fall through to switch */ }

  try {
    await ethereum.request({
      method: 'wallet_switchEthereumChain',
      params: [{ chainId: ARC_CHAIN_HEX }],
    })
  } catch (switchError) {
    if (switchError.code === 4902) {
      await ethereum.request({
        method: 'wallet_addEthereumChain',
        params: [{
          chainId: ARC_CHAIN_HEX,
          chainName: 'Arc Testnet',
          nativeCurrency: { name: 'USD Coin', symbol: 'USDC', decimals: 18 },
          rpcUrls: ['https://rpc.testnet.arc.network'],
          blockExplorerUrls: [],
        }],
      })
    } else if (isAlreadyPendingError(switchError)) {
      throw new Error('A wallet request is already open — check your MetaMask extension popup, then try again.')
    } else {
      throw switchError
    }
  }
}

export async function connectWallet(providerId) {
  const provider = WALLET_PROVIDERS.find(p => p.id === providerId)
  if (!provider) throw new Error(`Unknown provider: ${providerId}`)

  const ethereum = provider.detect()
  if (!ethereum) throw new Error(`${provider.name} not detected. Please install the extension.`)

  let accounts
  try {
    accounts = await ethereum.request({ method: 'eth_requestAccounts' })
  } catch (err) {
    if (isAlreadyPendingError(err)) {
      throw new Error('A wallet request is already open — check your MetaMask extension popup, then try again.')
    }
    if (err?.code === 4001) {
      throw new Error('Connection rejected — approve the request in MetaMask to continue.')
    }
    throw err
  }
  if (!accounts?.length) throw new Error('No accounts returned from wallet.')

  await ensureArcChain(ethereum)

  _provider = ethereum
  _address = accounts[0]
  _providerId = providerId
  _walletClient = createWalletClient({
    account: _address,
    chain: arcTestnet,
    transport: custom(ethereum),
  })

  saveWalletMeta(providerId, _address)
  return { address: _address, provider: providerId }
}

export function disconnectWallet() {
  _walletClient = null
  _provider = null
  _address = null
  _providerId = null
  clearWalletMeta()
}

export async function getWalletClient() {
  if (_walletClient) return _walletClient
  throw new Error('No wallet connected. Click "Connect Wallet" to continue.')
}

// Check which providers are available
export function getAvailableProviders() {
  return WALLET_PROVIDERS.filter(p => p.detect() !== null)
}

// Listen for account/chain changes from the wallet extension
if (typeof window !== 'undefined' && window.ethereum) {
  window.ethereum.on?.('accountsChanged', (accounts) => {
    if (!accounts?.length) {
      disconnectWallet()
      window.dispatchEvent(new CustomEvent('wallet-changed', { detail: { address: null } }))
    } else {
      _address = accounts[0]
      if (_providerId) saveWalletMeta(_providerId, _address)
      if (_provider) {
        _walletClient = createWalletClient({
          account: _address,
          chain: arcTestnet,
          transport: custom(_provider),
        })
      }
      window.dispatchEvent(new CustomEvent('wallet-changed', { detail: { address: _address } }))
    }
  })
  window.ethereum.on?.('chainChanged', () => {
    window.location.reload()
  })
}

// ─── ABIs (minimal, just what we need) ──────────────────────

export const ORACLE_ABI = [
  { name: 'price',       type: 'function', stateMutability: 'view', inputs: [], outputs: [{ type: 'uint256' }] },
  { name: 'symbol',      type: 'function', stateMutability: 'view', inputs: [], outputs: [{ type: 'string'  }] },
  { name: 'lastUpdated', type: 'function', stateMutability: 'view', inputs: [], outputs: [{ type: 'uint256' }] },
  { name: 'isFresh',     type: 'function', stateMutability: 'view', inputs: [], outputs: [{ type: 'bool'    }] },
  { name: 'setPrice',    type: 'function', stateMutability: 'nonpayable', inputs: [{ type: 'uint256', name: '_newPrice' }], outputs: [] },
]

export const TOKEN_ABI = [
  { name: 'totalSupply',   type: 'function', stateMutability: 'view', inputs: [], outputs: [{ type: 'uint256' }] },
  { name: 'balanceOf',     type: 'function', stateMutability: 'view', inputs: [{ type: 'address' }], outputs: [{ type: 'uint256' }] },
  { name: 'approve',       type: 'function', stateMutability: 'nonpayable', inputs: [{ type: 'address' }, { type: 'uint256' }], outputs: [{ type: 'bool' }] },
  { name: 'allowance',     type: 'function', stateMutability: 'view', inputs: [{ type: 'address' }, { type: 'address' }], outputs: [{ type: 'uint256' }] },
  { name: 'symbol',        type: 'function', stateMutability: 'view', inputs: [], outputs: [{ type: 'string' }] },
  { name: 'decimals',      type: 'function', stateMutability: 'view', inputs: [], outputs: [{ type: 'uint8' }] },
]

export const SYNTH_VAULT_ABI = [
  { name: 'mint',                type: 'function', stateMutability: 'nonpayable', inputs: [{ type: 'uint256', name: 'amountUsdc' }], outputs: [{ type: 'uint256' }] },
  { name: 'burn',                type: 'function', stateMutability: 'nonpayable', inputs: [{ type: 'uint256', name: 'synthAmount' }], outputs: [{ type: 'uint256' }] },
  { name: 'previewMint',         type: 'function', stateMutability: 'view', inputs: [{ type: 'uint256' }], outputs: [{ type: 'uint256' }] },
  { name: 'previewBurn',         type: 'function', stateMutability: 'view', inputs: [{ type: 'uint256' }], outputs: [{ type: 'uint256' }] },
  { name: 'totalCollateral',     type: 'function', stateMutability: 'view', inputs: [], outputs: [{ type: 'uint256' }] },
  { name: 'vaultCollateralization', type: 'function', stateMutability: 'view', inputs: [], outputs: [{ type: 'uint256' }] },
]

export const AMM_ROUTER_ABI = [
  { name: 'createPool',    type: 'function', stateMutability: 'nonpayable', inputs: [{ type: 'address' }, { type: 'address' }], outputs: [{ type: 'address' }] },
  { name: 'getPool',       type: 'function', stateMutability: 'view', inputs: [{ type: 'address' }, { type: 'address' }], outputs: [{ type: 'address' }] },
  { name: 'getAllPools',   type: 'function', stateMutability: 'view', inputs: [], outputs: [{ type: 'address[]' }] },
  { name: 'swap',          type: 'function', stateMutability: 'nonpayable', inputs: [{ type: 'address' }, { type: 'address' }, { type: 'uint256' }, { type: 'uint256' }], outputs: [{ type: 'uint256' }] },
  { name: 'getAmountOut',  type: 'function', stateMutability: 'view', inputs: [{ type: 'address' }, { type: 'address' }, { type: 'uint256' }], outputs: [{ type: 'uint256' }] },
  { name: 'addLiquidity',  type: 'function', stateMutability: 'nonpayable', inputs: [{ type: 'address' }, { type: 'address' }, { type: 'uint256' }, { type: 'uint256' }, { type: 'uint256' }], outputs: [{ type: 'uint256' }] },
]

export const TRACE_REGISTRY_ABI = [
  { name: 'publishTrace',   type: 'function', stateMutability: 'nonpayable', inputs: [{ type: 'address' }, { type: 'bytes32' }, { type: 'bytes' }], outputs: [{ type: 'uint256' }] },
  { name: 'verifyTrace',    type: 'function', stateMutability: 'view', inputs: [{ type: 'uint256' }, { type: 'bytes' }], outputs: [{ type: 'bool' }] },
  { name: 'traceCount',     type: 'function', stateMutability: 'view', inputs: [], outputs: [{ type: 'uint256' }] },
  { name: 'getTracesByVault', type: 'function', stateMutability: 'view', inputs: [{ type: 'address' }], outputs: [{ type: 'uint256[]' }] },
  { name: 'getTraceById',   type: 'function', stateMutability: 'view', inputs: [{ type: 'uint256' }], outputs: [{ type: 'address', name: 'agent' }, { type: 'address', name: 'vault' }, { type: 'bytes32', name: 'traceHash' }, { type: 'uint256', name: 'timestamp' }, { type: 'bytes', name: 'metadata' }] },
]

export const ASSET_REGISTRY_ABI = [
  { name: 'getAllSynthetics', type: 'function', stateMutability: 'view', inputs: [], outputs: [{ type: 'address[]' }] },
  { name: 'vaultCount',       type: 'function', stateMutability: 'view', inputs: [], outputs: [{ type: 'uint256' }] },
  { name: 'getLeaderboard',   type: 'function', stateMutability: 'view', inputs: [{ type: 'uint8' }, { type: 'uint256' }], outputs: [{ type: 'address[]' }] },
]

export const VAULT_ABI = [
  { name: 'deposit',             type: 'function', stateMutability: 'nonpayable', inputs: [{ type: 'uint256' }, { type: 'address' }], outputs: [{ type: 'uint256' }] },
  { name: 'withdraw',            type: 'function', stateMutability: 'nonpayable', inputs: [{ type: 'uint256' }, { type: 'address' }, { type: 'address' }], outputs: [{ type: 'uint256' }] },
  { name: 'totalAssets',         type: 'function', stateMutability: 'view', inputs: [], outputs: [{ type: 'uint256' }] },
  { name: 'totalSupply',         type: 'function', stateMutability: 'view', inputs: [], outputs: [{ type: 'uint256' }] },
  { name: 'balanceOf',           type: 'function', stateMutability: 'view', inputs: [{ type: 'address' }], outputs: [{ type: 'uint256' }] },
  { name: 'getHoldings',         type: 'function', stateMutability: 'view', inputs: [], outputs: [{ type: 'address[]' }, { type: 'uint256[]' }] },
  { name: 'creator',             type: 'function', stateMutability: 'view', inputs: [], outputs: [{ type: 'address' }] },
  { name: 'tier',                type: 'function', stateMutability: 'view', inputs: [], outputs: [{ type: 'uint8' }] },
  { name: 'paused',              type: 'function', stateMutability: 'view', inputs: [], outputs: [{ type: 'bool' }] },
  { name: 'highWaterMark',       type: 'function', stateMutability: 'view', inputs: [], outputs: [{ type: 'uint256' }] },
  { name: 'asset',               type: 'function', stateMutability: 'view', inputs: [], outputs: [{ type: 'address' }] },
  { name: 'approve',             type: 'function', stateMutability: 'nonpayable', inputs: [{ type: 'address' }, { type: 'uint256' }], outputs: [{ type: 'bool' }] },
  { name: 'name',                type: 'function', stateMutability: 'view', inputs: [], outputs: [{ type: 'string' }] },
  { name: 'symbol',              type: 'function', stateMutability: 'view', inputs: [], outputs: [{ type: 'string' }] },
  { name: 'managementFeeBps',    type: 'function', stateMutability: 'view', inputs: [], outputs: [{ type: 'uint16' }] },
  { name: 'performanceFeeBps',   type: 'function', stateMutability: 'view', inputs: [], outputs: [{ type: 'uint16' }] },
  { name: 'setTargetAllocations', type: 'function', stateMutability: 'nonpayable', inputs: [{ type: 'address[]', name: 'tokens' }, { type: 'uint256[]', name: 'weightsBps' }], outputs: [] },
  { name: 'getTargetAllocations', type: 'function', stateMutability: 'view', inputs: [], outputs: [{ type: 'address[]' }, { type: 'uint256[]' }] },
  { name: 'setTokenOracles', type: 'function', stateMutability: 'nonpayable', inputs: [{ type: 'address[]', name: 'tokens' }, { type: 'address[]', name: 'oracles' }], outputs: [] },
  { name: 'tokenOracle', type: 'function', stateMutability: 'view', inputs: [{ type: 'address' }], outputs: [{ type: 'address' }] },
]

export const VAULT_FACTORY_ABI = [
  { name: 'createVault',    type: 'function', stateMutability: 'nonpayable', inputs: [{ type: 'string' }, { type: 'string' }, { type: 'uint16' }, { type: 'uint16' }, { type: 'bool' }], outputs: [{ type: 'address' }] },
  { name: 'getVaults',      type: 'function', stateMutability: 'view', inputs: [], outputs: [{ type: 'address[]' }] },
  { name: 'vaultCount',     type: 'function', stateMutability: 'view', inputs: [], outputs: [{ type: 'uint256' }] },
  { name: 'agentAddress',   type: 'function', stateMutability: 'view', inputs: [], outputs: [{ type: 'address' }] },
  { name: 'getVaultsByCreator', type: 'function', stateMutability: 'view', inputs: [{ type: 'address' }], outputs: [{ type: 'address[]' }] },
  // VaultCreated event — used to extract new vault address from receipt
  { name: 'VaultCreated',   type: 'event', inputs: [
    { name: 'vault',   type: 'address', indexed: true },
    { name: 'creator', type: 'address', indexed: true },
    { name: 'name',    type: 'string',  indexed: false },
    { name: 'symbol',  type: 'string',  indexed: false },
    { name: 'tier',    type: 'uint8',   indexed: false },
  ]},
]

// ─── Deployed addresses from .env ────────────────────────────

export const USDC = "0x3600000000000000000000000000000000000000"

export const ASSETS = [
  { id: 'TSLA',   name: 'Tesla',      sym: 'sTSLA',   emoji: '🚗', oracle: '0x9eEd179B2E4f6Fb54a452D3E727649EA3b15b763', token: '0xE745C07d7d32A1Ca0d6162A1c50e876619CF7388' },
  { id: 'NVDA',   name: 'Nvidia',     sym: 'sNVDA',   emoji: '🎮', oracle: '0xbDa34c7e3FdF7B8e93c9aa383b50C2e0cE58E0dB', token: '0xC297A15E702C910b71Ac531c6633aFDd90389e1d' },
  { id: 'SPY',    name: 'S&P 500',    sym: 'sSPY',    emoji: '📈', oracle: '0x2D41e62D6bAD0a84190E257d3F5A90F48Be55Fbe', token: '0x04315D3c35639288949cEE1d1E01Bd6100aDf3f5' },
  { id: 'BTC',    name: 'Bitcoin',    sym: 'sBTC',    emoji: '₿',  oracle: '0xF9a2B28b9B4D67F43Cb490E54f8C6F4cd59482F1', token: '0xdDbac3Cf2feb7192f963e6a9bB4DE0822C3DF4DB' },
  { id: 'GOLD',   name: 'Gold ETF',   sym: 'sGOLD',   emoji: '🥇', oracle: '0xbFAd6DaDd35Cb56aE29dC47D9Ac4c46f0fCd9B9A', token: '0xb13Eb59d8CDfACeDE2990207651e8649bdf7A89f' },
]

// New contract addresses — set these after deploying via deploy-new.mjs
export const NEW_CONTRACTS = {
  ammRouter:       '0x090f8E245F2831b81c9ff21661FBd0cb1383f82D',
  vaultFactory:    '0x32A3e0D0a8215D77e3B92fa6d9b4Dbe19f255671',
  traceRegistry:   '0x44bD55c0DdF757e584a41fb7F3B6a47b4C5982ba',
  assetRegistry:   '0x79fc95A10E8240116006084439B650BA9e72F3cA',
}
