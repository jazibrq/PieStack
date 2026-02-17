import { createContext, useContext, useState, useEffect, useCallback, useRef, ReactNode } from 'react';
import { ethers } from 'ethers';
import { MONAD_TESTNET } from '@/config/contracts';

/* ------------------------------------------------------------------ */
/*  Types                                                              */
/* ------------------------------------------------------------------ */

interface EthereumProvider extends ethers.Eip1193Provider {
  request: (args: { method: string; params?: unknown[] }) => Promise<unknown>;
  on?: (event: string, handler: (...args: unknown[]) => void) => void;
  removeListener?: (event: string, handler: (...args: unknown[]) => void) => void;
  isMetaMask?: boolean;
}

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

/* ------------------------------------------------------------------ */
/*  Helpers                                                            */
/* ------------------------------------------------------------------ */

function getEthereum(): EthereumProvider | undefined {
  return (window as unknown as { ethereum?: EthereumProvider }).ethereum;
}

async function ensureMonadTestnet(ethereum: EthereumProvider): Promise<void> {
  try {
    await ethereum.request({
      method: 'wallet_switchEthereumChain',
      params: [{ chainId: MONAD_TESTNET.chainIdHex }],
    });
  } catch (switchError: unknown) {
    const err = switchError as { code?: number };
    if (err.code === 4902) {
      // Chain not yet added — add it
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

/** Build provider + signer + fetch balance for a given address list. */
async function bootstrapWallet(ethereum: EthereumProvider, accounts: string[]) {
  if (accounts.length === 0) return null;

  const browserProvider = new ethers.BrowserProvider(ethereum);
  const userSigner = await browserProvider.getSigner();
  const userAddress = await userSigner.getAddress();
  const bal = await browserProvider.getBalance(userAddress);

  return {
    provider: browserProvider,
    signer: userSigner,
    address: userAddress,
    balance: ethers.formatEther(bal),
  };
}

/* ------------------------------------------------------------------ */
/*  Provider                                                           */
/* ------------------------------------------------------------------ */

export const WalletProvider = ({ children }: { children: ReactNode }) => {
  const [isConnected, setIsConnected] = useState(false);
  const [address, setAddress] = useState<string | null>(null);
  const [balance, setBalance] = useState('0');
  const [provider, setProvider] = useState<ethers.BrowserProvider | null>(null);
  const [signer, setSigner] = useState<ethers.Signer | null>(null);

  // Keep a ref so event handlers always see latest state without re-registering
  const connectedRef = useRef(isConnected);
  connectedRef.current = isConnected;

  /* ---- helpers exposed to consumers ---- */

  const refreshBalance = useCallback(async () => {
    const ethereum = getEthereum();
    if (!ethereum) return;

    // Always build a fresh provider to avoid stale internal state
    try {
      const accounts = await ethereum.request({ method: 'eth_accounts' }) as string[];
      if (accounts.length === 0) return;

      const browserProvider = new ethers.BrowserProvider(ethereum);
      const bal = await browserProvider.getBalance(accounts[0]);
      setBalance(ethers.formatEther(bal));
    } catch {
      // silently fail on balance refresh
    }
  }, []);

  const applyWallet = useCallback(
    (data: { provider: ethers.BrowserProvider; signer: ethers.Signer; address: string; balance: string }) => {
      setProvider(data.provider);
      setSigner(data.signer);
      setAddress(data.address);
      setBalance(data.balance);
      setIsConnected(true);
    },
    [],
  );

  const disconnect = useCallback(() => {
    setIsConnected(false);
    setAddress(null);
    setBalance('0');
    setProvider(null);
    setSigner(null);
  }, []);

  const connect = useCallback(async () => {
    const ethereum = getEthereum();
    if (!ethereum) {
      alert('Please install MetaMask to connect.');
      return;
    }

    try {
      // 1. Request accounts FIRST (must authorize site before switching chain)
      const accounts = await ethereum.request({ method: 'eth_requestAccounts' }) as string[];
      console.log('[PieStack] Accounts authorized:', accounts);

      // 2. Now switch to Monad Testnet
      await ensureMonadTestnet(ethereum);
      console.log('[PieStack] Switched to Monad Testnet');

      // 3. Bootstrap provider / signer / balance
      const data = await bootstrapWallet(ethereum, accounts);
      if (!data) {
        console.warn('[PieStack] bootstrapWallet returned null');
        return;
      }
      console.log('[PieStack] Connected:', data.address, 'Balance:', data.balance, 'MON');
      applyWallet(data);
    } catch (error) {
      console.error('[PieStack] Wallet connection failed:', error);
    }
  }, [applyWallet]);

  /* ---- Auto-reconnect on page load ---- */

  useEffect(() => {
    const autoConnect = async () => {
      const ethereum = getEthereum();
      if (!ethereum) {
        console.log('[PieStack] No ethereum provider found');
        return;
      }

      try {
        // eth_accounts is read-only — no popup
        const accounts = await ethereum.request({ method: 'eth_accounts' }) as string[];
        if (accounts.length === 0) {
          console.log('[PieStack] No previously authorized accounts');
          return;
        }

        console.log('[PieStack] Auto-reconnecting with account:', accounts[0]);

        // Check current chain — only switch if not already on Monad
        const currentChainId = await ethereum.request({ method: 'eth_chainId' }) as string;
        if (currentChainId.toLowerCase() !== MONAD_TESTNET.chainIdHex.toLowerCase()) {
          console.log('[PieStack] Wrong chain during auto-connect, switching...');
          await ensureMonadTestnet(ethereum);
        }

        const data = await bootstrapWallet(ethereum, accounts);
        if (!data) return;
        console.log('[PieStack] Auto-connected:', data.address, 'Balance:', data.balance, 'MON');
        applyWallet(data);
      } catch (error) {
        console.error('[PieStack] Auto-connect failed:', error);
      }
    };

    autoConnect();
    // Only run once on mount
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  /* ---- accountsChanged / chainChanged listeners ---- */

  useEffect(() => {
    const ethereum = getEthereum();
    if (!ethereum?.on) return;

    const handleAccountsChanged = async (raw: unknown) => {
      const accounts = raw as string[];
      if (accounts.length === 0) {
        disconnect();
        return;
      }

      if (!connectedRef.current) return;

      // Rebuild provider + signer + balance for the new account
      try {
        const data = await bootstrapWallet(ethereum, accounts);
        if (data) applyWallet(data);
      } catch (err) {
        console.error('Failed to switch account:', err);
      }
    };

    const handleChainChanged = async () => {
      if (!connectedRef.current) return;

      // Rebuild everything so provider + balance match the new chain
      try {
        const accounts = await ethereum.request({ method: 'eth_accounts' }) as string[];
        if (accounts.length === 0) {
          disconnect();
          return;
        }

        await ensureMonadTestnet(ethereum);
        const data = await bootstrapWallet(ethereum, accounts);
        if (data) applyWallet(data);
      } catch (err) {
        console.error('Chain change handling failed:', err);
      }
    };

    ethereum.on('accountsChanged', handleAccountsChanged);
    ethereum.on('chainChanged', handleChainChanged);

    return () => {
      ethereum.removeListener?.('accountsChanged', handleAccountsChanged);
      ethereum.removeListener?.('chainChanged', handleChainChanged);
    };
  }, [applyWallet, disconnect]);

  /* ---- Periodic balance refresh (every 15 s) ---- */

  useEffect(() => {
    if (!isConnected) return;
    refreshBalance();
    const interval = setInterval(refreshBalance, 15000);
    return () => clearInterval(interval);
  }, [isConnected, refreshBalance]);

  /* ---- Render ---- */

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
