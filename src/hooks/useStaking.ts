import { useState, useCallback, useEffect } from 'react';
import { ethers } from 'ethers';
import { useWallet } from '@/contexts/WalletContext';
import { CONTRACT_ADDRESSES, STAKING_ADAPTER_ABI } from '@/config/contracts';

interface StakingState {
  principal: string;
  availableRewards: string;
  faucetCooldown: number; // seconds remaining
  loading: boolean;
}

export function useStaking() {
  const { signer, provider, address, isConnected, refreshBalance } = useWallet();
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
      console.error('Failed to fetch staking balances:', error);
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
    const contract = getContract(true);
    if (!contract) throw new Error('Wallet not connected');

    setState(prev => ({ ...prev, loading: true }));
    try {
      const tx = await contract.deposit({
        value: ethers.parseEther(amountEther),
      });
      await tx.wait();
      await fetchBalances();
      await refreshBalance();
    } finally {
      setState(prev => ({ ...prev, loading: false }));
    }
  }, [getContract, fetchBalances, refreshBalance]);

  const withdraw = useCallback(async () => {
    const contract = getContract(true);
    if (!contract) throw new Error('Wallet not connected');

    setState(prev => ({ ...prev, loading: true }));
    try {
      const tx = await contract.withdraw();
      await tx.wait();
      await fetchBalances();
      await refreshBalance();
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
      await tx.wait();
      await fetchBalances();
      await refreshBalance();
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
