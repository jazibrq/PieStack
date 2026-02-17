export const MONAD_TESTNET = {
  chainId: 10143,
  chainIdHex: '0x27A7',
  name: 'Monad Testnet',
  rpcUrl: 'https://testnet-rpc.monad.xyz',
  blockExplorer: 'https://testnet.monadexplorer.com',
  currency: {
    name: 'MON',
    symbol: 'MON',
    decimals: 18,
  },
};

// Update these addresses after deploying contracts to Monad testnet.
// Run: npx hardhat run scripts/deploy.ts --network monadTestnet
export const CONTRACT_ADDRESSES = {
  stakingAdapter: '0x0000000000000000000000000000000000000000',
  gameManager: '0x0000000000000000000000000000000000000000',
};

export const STAKING_ADAPTER_ABI = [
  {"inputs":[],"stateMutability":"nonpayable","type":"constructor"},
  {"anonymous":false,"inputs":[{"indexed":true,"internalType":"address","name":"user","type":"address"},{"indexed":false,"internalType":"uint256","name":"amount","type":"uint256"}],"name":"Deposited","type":"event"},
  {"anonymous":false,"inputs":[{"indexed":true,"internalType":"address","name":"user","type":"address"},{"indexed":false,"internalType":"uint256","name":"amount","type":"uint256"}],"name":"FaucetClaimed","type":"event"},
  {"anonymous":false,"inputs":[{"indexed":true,"internalType":"address","name":"gameManager","type":"address"}],"name":"GameManagerSet","type":"event"},
  {"anonymous":false,"inputs":[{"indexed":true,"internalType":"address","name":"user","type":"address"},{"indexed":false,"internalType":"uint256","name":"amount","type":"uint256"}],"name":"RewardsCredited","type":"event"},
  {"anonymous":false,"inputs":[{"indexed":true,"internalType":"address","name":"user","type":"address"},{"indexed":false,"internalType":"uint256","name":"amount","type":"uint256"}],"name":"RewardsDeducted","type":"event"},
  {"anonymous":false,"inputs":[{"indexed":true,"internalType":"address","name":"user","type":"address"},{"indexed":false,"internalType":"uint256","name":"principal","type":"uint256"},{"indexed":false,"internalType":"uint256","name":"rewards","type":"uint256"}],"name":"Withdrawn","type":"event"},
  {"inputs":[],"name":"APY_BPS","outputs":[{"internalType":"uint256","name":"","type":"uint256"}],"stateMutability":"view","type":"function"},
  {"inputs":[],"name":"FAUCET_COOLDOWN","outputs":[{"internalType":"uint256","name":"","type":"uint256"}],"stateMutability":"view","type":"function"},
  {"inputs":[],"name":"FAUCET_MAX","outputs":[{"internalType":"uint256","name":"","type":"uint256"}],"stateMutability":"view","type":"function"},
  {"inputs":[],"name":"FAUCET_MIN","outputs":[{"internalType":"uint256","name":"","type":"uint256"}],"stateMutability":"view","type":"function"},
  {"inputs":[{"internalType":"address","name":"user","type":"address"},{"internalType":"uint256","name":"amount","type":"uint256"}],"name":"creditRewards","outputs":[],"stateMutability":"nonpayable","type":"function"},
  {"inputs":[{"internalType":"address","name":"user","type":"address"},{"internalType":"uint256","name":"amount","type":"uint256"}],"name":"deductRewards","outputs":[],"stateMutability":"nonpayable","type":"function"},
  {"inputs":[],"name":"deposit","outputs":[],"stateMutability":"payable","type":"function"},
  {"inputs":[],"name":"faucet","outputs":[],"stateMutability":"nonpayable","type":"function"},
  {"inputs":[{"internalType":"address","name":"user","type":"address"}],"name":"faucetCooldownRemaining","outputs":[{"internalType":"uint256","name":"","type":"uint256"}],"stateMutability":"view","type":"function"},
  {"inputs":[],"name":"gameManager","outputs":[{"internalType":"address","name":"","type":"address"}],"stateMutability":"view","type":"function"},
  {"inputs":[{"internalType":"address","name":"user","type":"address"}],"name":"getAccruedRewards","outputs":[{"internalType":"uint256","name":"","type":"uint256"}],"stateMutability":"view","type":"function"},
  {"inputs":[{"internalType":"address","name":"user","type":"address"}],"name":"getAvailableRewards","outputs":[{"internalType":"uint256","name":"","type":"uint256"}],"stateMutability":"view","type":"function"},
  {"inputs":[{"internalType":"address","name":"user","type":"address"}],"name":"getPrincipal","outputs":[{"internalType":"uint256","name":"","type":"uint256"}],"stateMutability":"view","type":"function"},
  {"inputs":[{"internalType":"address","name":"","type":"address"}],"name":"lastFaucetClaim","outputs":[{"internalType":"uint256","name":"","type":"uint256"}],"stateMutability":"view","type":"function"},
  {"inputs":[],"name":"owner","outputs":[{"internalType":"address","name":"","type":"address"}],"stateMutability":"view","type":"function"},
  {"inputs":[{"internalType":"address","name":"","type":"address"}],"name":"principal","outputs":[{"internalType":"uint256","name":"","type":"uint256"}],"stateMutability":"view","type":"function"},
  {"inputs":[{"internalType":"address","name":"","type":"address"}],"name":"rewardBalance","outputs":[{"internalType":"uint256","name":"","type":"uint256"}],"stateMutability":"view","type":"function"},
  {"inputs":[{"internalType":"address","name":"_gameManager","type":"address"}],"name":"setGameManager","outputs":[],"stateMutability":"nonpayable","type":"function"},
  {"inputs":[{"internalType":"address","name":"","type":"address"}],"name":"stakeTimestamp","outputs":[{"internalType":"uint256","name":"","type":"uint256"}],"stateMutability":"view","type":"function"},
  {"inputs":[],"name":"withdraw","outputs":[],"stateMutability":"nonpayable","type":"function"},
  {"stateMutability":"payable","type":"receive"}
] as const;

export const GAME_MANAGER_ABI = [
  {"inputs":[{"internalType":"address","name":"_stakingAdapter","type":"address"}],"stateMutability":"nonpayable","type":"constructor"},
  {"anonymous":false,"inputs":[{"indexed":true,"internalType":"uint256","name":"lobbyId","type":"uint256"},{"indexed":true,"internalType":"address","name":"winner","type":"address"},{"indexed":false,"internalType":"uint256","name":"prizeAmount","type":"uint256"}],"name":"GameResolved","type":"event"},
  {"anonymous":false,"inputs":[{"indexed":true,"internalType":"uint256","name":"lobbyId","type":"uint256"}],"name":"LobbyCancelled","type":"event"},
  {"anonymous":false,"inputs":[{"indexed":true,"internalType":"uint256","name":"lobbyId","type":"uint256"},{"indexed":true,"internalType":"address","name":"host","type":"address"},{"indexed":false,"internalType":"uint256","name":"buyIn","type":"uint256"},{"indexed":false,"internalType":"uint256","name":"maxPlayers","type":"uint256"}],"name":"LobbyCreated","type":"event"},
  {"anonymous":false,"inputs":[{"indexed":true,"internalType":"uint256","name":"lobbyId","type":"uint256"},{"indexed":true,"internalType":"address","name":"player","type":"address"}],"name":"PlayerJoined","type":"event"},
  {"inputs":[],"name":"admin","outputs":[{"internalType":"address","name":"","type":"address"}],"stateMutability":"view","type":"function"},
  {"inputs":[{"internalType":"uint256","name":"lobbyId","type":"uint256"}],"name":"cancelLobby","outputs":[],"stateMutability":"nonpayable","type":"function"},
  {"inputs":[{"internalType":"uint256","name":"buyIn","type":"uint256"},{"internalType":"uint256","name":"maxPlayers","type":"uint256"}],"name":"createLobby","outputs":[{"internalType":"uint256","name":"","type":"uint256"}],"stateMutability":"nonpayable","type":"function"},
  {"inputs":[{"internalType":"uint256","name":"lobbyId","type":"uint256"}],"name":"getLobby","outputs":[{"internalType":"address","name":"host","type":"address"},{"internalType":"uint256","name":"buyIn","type":"uint256"},{"internalType":"uint256","name":"maxPlayers","type":"uint256"},{"internalType":"address[]","name":"players","type":"address[]"},{"internalType":"bool","name":"resolved","type":"bool"},{"internalType":"bool","name":"active","type":"bool"},{"internalType":"uint256","name":"prizePool","type":"uint256"}],"stateMutability":"view","type":"function"},
  {"inputs":[],"name":"getLobbyCount","outputs":[{"internalType":"uint256","name":"","type":"uint256"}],"stateMutability":"view","type":"function"},
  {"inputs":[{"internalType":"uint256","name":"lobbyId","type":"uint256"}],"name":"getLobbyPlayerCount","outputs":[{"internalType":"uint256","name":"","type":"uint256"}],"stateMutability":"view","type":"function"},
  {"inputs":[{"internalType":"uint256","name":"","type":"uint256"},{"internalType":"address","name":"","type":"address"}],"name":"isPlayerInLobby","outputs":[{"internalType":"bool","name":"","type":"bool"}],"stateMutability":"view","type":"function"},
  {"inputs":[{"internalType":"uint256","name":"lobbyId","type":"uint256"}],"name":"joinLobby","outputs":[],"stateMutability":"nonpayable","type":"function"},
  {"inputs":[{"internalType":"uint256","name":"","type":"uint256"}],"name":"lobbies","outputs":[{"internalType":"address","name":"host","type":"address"},{"internalType":"uint256","name":"buyIn","type":"uint256"},{"internalType":"uint256","name":"maxPlayers","type":"uint256"},{"internalType":"bool","name":"resolved","type":"bool"},{"internalType":"bool","name":"active","type":"bool"},{"internalType":"uint256","name":"prizePool","type":"uint256"}],"stateMutability":"view","type":"function"},
  {"inputs":[],"name":"lobbyCount","outputs":[{"internalType":"uint256","name":"","type":"uint256"}],"stateMutability":"view","type":"function"},
  {"inputs":[{"internalType":"uint256","name":"lobbyId","type":"uint256"},{"internalType":"address","name":"winner","type":"address"}],"name":"resolveGame","outputs":[],"stateMutability":"nonpayable","type":"function"},
  {"inputs":[],"name":"stakingAdapter","outputs":[{"internalType":"contract StakingAdapter","name":"","type":"address"}],"stateMutability":"view","type":"function"}
] as const;
