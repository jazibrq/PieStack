import { createContext, useContext, useState, useEffect, useCallback, ReactNode } from 'react';
import { ethers } from 'ethers';
import { MONAD_TESTNET } from '@/config/contracts';

interface WalletContextType {
  isConnected: boolean;
  address: string | null;
  balance: string; // MON balance in ether units
  provider: ethers.BrowserProvider | null;
  signer: ethers.Signer | null;
  connect: () => Promise<void>;
  disconnect: () => void;
  refreshBalance: () => Promise<void>;
}

const WalletContext = createContext<WalletContextType>({
  isConnected: false,
  address: null,
  balance: '0',
  provider: null,
  signer: null,
  connect: async () => {},
  disconnect: () => {},
  refreshBalance: async () => {},
});

export const useWallet = () => useContext(WalletContext);

async function switchToMonadTestnet() {
  const ethereum = (window as unknown as { ethereum?: ethers.Eip1193Provider & { request: (args: { method: string; params?: unknown[] }) => Promise<unknown> } }).ethereum;
  if (!ethereum) return;

  try {
    await ethereum.request({
      method: 'wallet_switchEthereumChain',
      params: [{ chainId: MONAD_TESTNET.chainIdHex }],
    });
  } catch (switchError: unknown) {
    const err = switchError as { code?: number };
    // Chain not added — add it
    if (err.code === 4902) {
      await ethereum.request({
        method: 'wallet_addEthereumChain',
        params: [{
          chainId: MONAD_TESTNET.chainIdHex,
          chainName: MONAD_TESTNET.name,
          nativeCurrency: MONAD_TESTNET.currency,
          rpcUrls: [MONAD_TESTNET.rpcUrl],
          blockExplorerUrls: [MONAD_TESTNET.blockExplorer],
        }],
      });
    } else {
      throw switchError;
    }
  }
}

export const WalletProvider = ({ children }: { children: ReactNode }) => {
  const [isConnected, setIsConnected] = useState(false);
  const [address, setAddress] = useState<string | null>(null);
  const [balance, setBalance] = useState('0');
  const [provider, setProvider] = useState<ethers.BrowserProvider | null>(null);
  const [signer, setSigner] = useState<ethers.Signer | null>(null);

  const refreshBalance = useCallback(async () => {
    if (!provider || !address) return;
    try {
      const bal = await provider.getBalance(address);
      setBalance(ethers.formatEther(bal));
    } catch {
      // silently fail on balance refresh
    }
  }, [provider, address]);

  const connect = useCallback(async () => {
    const ethereum = (window as unknown as { ethereum?: ethers.Eip1193Provider }).ethereum;
    if (!ethereum) {
      alert('Please install MetaMask or another Web3 wallet to connect.');
      return;
    }

    try {
      await switchToMonadTestnet();

      const browserProvider = new ethers.BrowserProvider(ethereum);
      const accounts = await browserProvider.send('eth_requestAccounts', []);

      if (accounts.length === 0) return;

      const userSigner = await browserProvider.getSigner();
      const userAddress = await userSigner.getAddress();
      const bal = await browserProvider.getBalance(userAddress);

      setProvider(browserProvider);
      setSigner(userSigner);
      setAddress(userAddress);
      setBalance(ethers.formatEther(bal));
      setIsConnected(true);
    } catch (error) {
      console.error('Wallet connection failed:', error);
    }
  }, []);

  const disconnect = useCallback(() => {
    setIsConnected(false);
    setAddress(null);
    setBalance('0');
    setProvider(null);
    setSigner(null);
  }, []);

  // Auto-reconnect on page load if MetaMask already has authorized accounts
  useEffect(() => {
    const autoConnect = async () => {
      const ethereum = (window as unknown as { ethereum?: ethers.Eip1193Provider & { request: (args: { method: string; params?: unknown[] }) => Promise<unknown> } }).ethereum;
      if (!ethereum) return;

      try {
        // eth_accounts is read-only — no popup, just checks if already authorized
        const accounts = await ethereum.request({ method: 'eth_accounts' }) as string[];
        if (accounts.length === 0) return;

        await switchToMonadTestnet();

        const browserProvider = new ethers.BrowserProvider(ethereum);
        const userSigner = await browserProvider.getSigner();
        const userAddress = await userSigner.getAddress();
        const bal = await browserProvider.getBalance(userAddress);

        setProvider(browserProvider);
        setSigner(userSigner);
        setAddress(userAddress);
        setBalance(ethers.formatEther(bal));
        setIsConnected(true);
      } catch (error) {
        console.error('Auto-connect failed:', error);
      }
    };

    autoConnect();
  }, []);

  // Listen for account and chain changes
  useEffect(() => {
    const ethereum = (window as unknown as { ethereum?: ethers.Eip1193Provider & { on?: (event: string, handler: (...args: unknown[]) => void) => void; removeListener?: (event: string, handler: (...args: unknown[]) => void) => void } }).ethereum;
    if (!ethereum?.on) return;

    const handleAccountsChanged = (accounts: unknown) => {
      const accts = accounts as string[];
      if (accts.length === 0) {
        disconnect();
      } else if (isConnected) {
        setAddress(accts[0]);
      }
    };

    const handleChainChanged = () => {
      // Re-connect on chain change to refresh provider
      if (isConnected) {
        connect();
      }
    };

    ethereum.on('accountsChanged', handleAccountsChanged);
    ethereum.on('chainChanged', handleChainChanged);

    return () => {
      ethereum.removeListener?.('accountsChanged', handleAccountsChanged);
      ethereum.removeListener?.('chainChanged', handleChainChanged);
    };
  }, [isConnected, connect, disconnect]);

  // Refresh balance periodically
  useEffect(() => {
    if (!isConnected) return;
    refreshBalance();
    const interval = setInterval(refreshBalance, 15000);
    return () => clearInterval(interval);
  }, [isConnected, refreshBalance]);

  return (
    <WalletContext.Provider value={{
      isConnected,
      address,
      balance,
      provider,
      signer,
      connect,
      disconnect,
      refreshBalance,
    }}>
      {children}
    </WalletContext.Provider>
  );
};
