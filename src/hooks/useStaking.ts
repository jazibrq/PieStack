import { useState, useCallback, useEffect } from 'react';
import { ethers } from 'ethers';
import { useWallet } from '@/contexts/WalletContext';
import { CONTRACT_ADDRESSES, STAKING_ADAPTER_ABI, MONAD_TESTNET } from '@/config/contracts';

interface StakingState {
  principal: string;
  availableRewards: string;
  faucetCooldown: number; // seconds remaining
  loading: boolean;
}

export function useStaking() {
  const { signer, provider, address, isConnected, refreshBalance, balance } = useWallet();
  const [state, setState] = useState<StakingState>({
    principal: '0',
    availableRewards: '0',
    faucetCooldown: 0,
    loading: false,
  });

  const getContract = useCallback((useSigner = false) => {
    const connection = useSigner ? signer : provider;
    if (!connection) return null;
    return new ethers.Contract(
      CONTRACT_ADDRESSES.stakingAdapter,
      STAKING_ADAPTER_ABI,
      connection
    );
  }, [signer, provider]);

  const fetchBalances = useCallback(async () => {
    if (!isConnected || !address) {
      setState({ principal: '0', availableRewards: '0', faucetCooldown: 0, loading: false });
      return;
    }

    const contract = getContract();
    if (!contract) return;

    try {
      const [principal, rewards, cooldown] = await Promise.all([
        contract.getPrincipal(address),
        contract.getAvailableRewards(address),
        contract.faucetCooldownRemaining(address),
      ]);
      setState({
        principal: ethers.formatEther(principal),
        availableRewards: ethers.formatEther(rewards),
        faucetCooldown: Number(cooldown),
        loading: false,
      });
    } catch (error) {
      console.error('[PieStack] Failed to fetch staking balances:', error);
    }
  }, [isConnected, address, getContract]);

  // Refresh balances on mount and periodically
  useEffect(() => {
    fetchBalances();
    if (!isConnected) return;
    const interval = setInterval(fetchBalances, 15000);
    return () => clearInterval(interval);
  }, [fetchBalances, isConnected]);

  const deposit = useCallback(async (amountEther: string) => {
    // --- Pre-flight validation ---
    if (!isConnected || !signer || !address) {
      throw new Error('Wallet not connected. Please connect MetaMask first.');
    }

    // Validate amount format
    const parsedAmount = parseFloat(amountEther);
    if (isNaN(parsedAmount) || parsedAmount <= 0) {
      throw new Error('Please enter a valid amount greater than 0.');
    }

    // Validate against wallet balance (leave gas headroom)
    const walletBalance = parseFloat(balance);
    if (parsedAmount > walletBalance) {
      throw new Error(`Insufficient balance. You have ${walletBalance.toFixed(6)} MON but tried to deposit ${parsedAmount.toFixed(6)} MON.`);
    }

    // Verify we're on Monad Testnet
    const ethereum = (window as unknown as { ethereum?: { request: (a: { method: string }) => Promise<unknown> } }).ethereum;
    if (ethereum) {
      const chainId = await ethereum.request({ method: 'eth_chainId' }) as string;
      if (chainId.toLowerCase() !== MONAD_TESTNET.chainIdHex.toLowerCase()) {
        throw new Error('Wrong network. Please switch to Monad Testnet in MetaMask.');
      }
    }

    const contract = getContract(true);
    if (!contract) throw new Error('Failed to initialize contract. Please reconnect wallet.');

    // Convert to wei (18 decimals, exact)
    const amountWei = ethers.parseEther(amountEther);
    console.log('[PieStack] Deposit: sending', amountEther, 'MON (', amountWei.toString(), 'wei ) from', address);

    setState(prev => ({ ...prev, loading: true }));
    try {
      // Send deposit tx — MetaMask popup will appear
      const tx = await contract.deposit({ value: amountWei });
      console.log('[PieStack] Deposit tx sent:', tx.hash);

      // Wait for on-chain confirmation
      const receipt = await tx.wait();
      console.log('[PieStack] Deposit confirmed in block:', receipt.blockNumber);

      // Refresh both staking balances and wallet MON balance
      await Promise.all([fetchBalances(), refreshBalance()]);
      console.log('[PieStack] Balances refreshed after deposit');
    } catch (error: unknown) {
      const err = error as { code?: string | number; reason?: string; message?: string };

      // User rejected in MetaMask
      if (err.code === 'ACTION_REJECTED' || err.code === 4001) {
        throw new Error('Transaction rejected by user.');
      }

      // Insufficient funds (gas + value)
      if (err.message?.includes('insufficient funds')) {
        throw new Error('Insufficient MON for deposit + gas fees.');
      }

      throw error;
    } finally {
      setState(prev => ({ ...prev, loading: false }));
    }
  }, [isConnected, signer, address, balance, getContract, fetchBalances, refreshBalance]);

  const withdraw = useCallback(async () => {
    const contract = getContract(true);
    if (!contract) throw new Error('Wallet not connected');

    setState(prev => ({ ...prev, loading: true }));
    try {
      const tx = await contract.withdraw();
      console.log('[PieStack] Withdraw tx sent:', tx.hash);
      await tx.wait();
      await Promise.all([fetchBalances(), refreshBalance()]);
    } catch (error: unknown) {
      const err = error as { code?: string | number };
      if (err.code === 'ACTION_REJECTED' || err.code === 4001) {
        throw new Error('Transaction rejected by user.');
      }
      throw error;
    } finally {
      setState(prev => ({ ...prev, loading: false }));
    }
  }, [getContract, fetchBalances, refreshBalance]);

  const claimFaucet = useCallback(async () => {
    const contract = getContract(true);
    if (!contract) throw new Error('Wallet not connected');

    setState(prev => ({ ...prev, loading: true }));
    try {
      const tx = await contract.faucet();
      console.log('[PieStack] Faucet tx sent:', tx.hash);
      await tx.wait();
      await Promise.all([fetchBalances(), refreshBalance()]);
    } catch (error: unknown) {
      const err = error as { code?: string | number };
      if (err.code === 'ACTION_REJECTED' || err.code === 4001) {
        throw new Error('Transaction rejected by user.');
      }
      throw error;
    } finally {
      setState(prev => ({ ...prev, loading: false }));
    }
  }, [getContract, fetchBalances, refreshBalance]);

  return {
    principal: state.principal,
    availableRewards: state.availableRewards,
    faucetCooldown: state.faucetCooldown,
    loading: state.loading,
    deposit,
    withdraw,
    claimFaucet,
    refreshBalances: fetchBalances,
  };
}
