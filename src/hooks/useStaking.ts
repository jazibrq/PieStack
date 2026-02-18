import { useState, useCallback, useEffect } from 'react';
import { ethers } from 'ethers';
import { useWallet } from '@/contexts/WalletContext';
import { CONTRACT_ADDRESSES, STAKING_ADAPTER_ABI, MONAD_TESTNET, isContractDeployed } from '@/config/contracts';

// --- Local simulation layer for demo ---
const STAKING_KEY = 'piestack_stake';

interface LocalStake {
  principal: number;
  depositedAt: number;
  accumulatedRewards: number;
  lastCalcAt: number;
}

function getLocalStake(addr: string): LocalStake | null {
  try {
    const raw = localStorage.getItem(`${STAKING_KEY}_${addr}`);
    return raw ? JSON.parse(raw) : null;
  } catch { return null; }
}

function saveLocalStake(addr: string, stake: LocalStake) {
  localStorage.setItem(`${STAKING_KEY}_${addr}`, JSON.stringify(stake));
}

function clearLocalStake(addr: string) {
  localStorage.removeItem(`${STAKING_KEY}_${addr}`);
}

/** Calculate simulated rewards based on 8% APY, accelerated 100,000x for demo. */
function calcSimulatedRewards(stake: LocalStake): number {
  if (stake.principal <= 0) return stake.accumulatedRewards;
  const now = Date.now();
  const elapsedSec = (now - stake.lastCalcAt) / 1000;
  const DEMO_MULTIPLIER = 100_000; // ~1 real minute ≈ 70 simulated days
  const perSecondRate = 0.08 / (365.25 * 24 * 3600);
  return stake.accumulatedRewards + stake.principal * perSecondRate * elapsedSec * DEMO_MULTIPLIER;
}

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

    // Try on-chain data first
    if (isContractDeployed()) {
      const contract = getContract();
      if (contract) {
        try {
          const [principal, rewards, cooldown] = await Promise.all([
            contract.getPrincipal(address),
            contract.getAvailableRewards(address),
            contract.faucetCooldownRemaining(address),
          ]);
          const principalVal = parseFloat(ethers.formatEther(principal));
          const rewardsVal = parseFloat(ethers.formatEther(rewards));

          if (principalVal > 0 || rewardsVal > 0) {
            // Sync on-chain data to local storage
            saveLocalStake(address, {
              principal: principalVal,
              depositedAt: Date.now(),
              accumulatedRewards: rewardsVal,
              lastCalcAt: Date.now(),
            });
            setState({
              principal: ethers.formatEther(principal),
              availableRewards: ethers.formatEther(rewards),
              faucetCooldown: Number(cooldown),
              loading: false,
            });
            return;
          }
        } catch (error) {
          console.error('[PieStack] Failed to fetch staking balances:', error);
        }
      }
    }

    // Fall back to local simulation
    const local = getLocalStake(address);
    if (local && local.principal > 0) {
      const rewards = calcSimulatedRewards(local);
      const now = Date.now();
      saveLocalStake(address, { ...local, accumulatedRewards: rewards, lastCalcAt: now });
      setState({
        principal: local.principal.toString(),
        availableRewards: rewards.toFixed(18),
        faucetCooldown: 0,
        loading: false,
      });
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

    // Verify deployed contract (not zero address)
    if (!isContractDeployed()) {
      throw new Error(
        'Staking contract not deployed yet. Please deploy the StakingAdapter contract to Monad Testnet first.\n\n' +
        'Run: DEPLOYER_PRIVATE_KEY=0x... npx hardhat run scripts/deploy.ts --network monadTestnet\n\n' +
        'Then update CONTRACT_ADDRESSES in src/config/contracts.ts with the deployed address.'
      );
    }

    const contract = getContract(true);
    if (!contract) throw new Error('Failed to initialize contract. Please reconnect wallet.');

    // Convert to wei (18 decimals, exact)
    const amountWei = ethers.parseEther(amountEther);

    setState(prev => ({ ...prev, loading: true }));
    try {
      // Send deposit tx — MetaMask popup will appear
      const tx = await contract.deposit({ value: amountWei });

      // Wait for on-chain confirmation
      await tx.wait();

      // Track in local simulation layer
      const existing = getLocalStake(address!) || { principal: 0, depositedAt: Date.now(), accumulatedRewards: 0, lastCalcAt: Date.now() };
      const currentRewards = calcSimulatedRewards(existing);
      saveLocalStake(address!, {
        principal: existing.principal + parsedAmount,
        depositedAt: existing.depositedAt || Date.now(),
        accumulatedRewards: currentRewards,
        lastCalcAt: Date.now(),
      });

      // Refresh both staking balances and wallet MON balance
      await Promise.all([fetchBalances(), refreshBalance()]);
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
    if (!isContractDeployed()) throw new Error('Staking contract not deployed yet.');
    const contract = getContract(true);
    if (!contract) throw new Error('Wallet not connected');

    setState(prev => ({ ...prev, loading: true }));
    try {
      const tx = await contract.withdraw();
      await tx.wait();
      if (address) clearLocalStake(address);
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
  }, [getContract, fetchBalances, refreshBalance, address]);

  const claimFaucet = useCallback(async () => {
    if (!isContractDeployed()) throw new Error('Staking contract not deployed yet.');
    const contract = getContract(true);
    if (!contract) throw new Error('Wallet not connected');

    setState(prev => ({ ...prev, loading: true }));
    try {
      const tx = await contract.faucet();
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
