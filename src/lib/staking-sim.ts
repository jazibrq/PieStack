/**
 * Pure staking simulation functions.
 * These are the source-of-truth calculation for the local demo layer.
 * Fully testable — no React, no ethers, no side-effects.
 */

// ─── Constants ────────────────────────────────────────
export const APY_RATE = 0.08; // 8% annual
export const SECONDS_PER_YEAR = 365.25 * 24 * 3600;
export const PER_SECOND_RATE = APY_RATE / SECONDS_PER_YEAR;
export const DEMO_MULTIPLIER = 100_000; // 1 real minute ≈ 70 simulated days

export const STAKING_KEY = 'piestack_stake';

// ─── Types ────────────────────────────────────────────
export interface LocalStake {
  principal: number;       // MON deposited
  depositedAt: number;     // timestamp ms (first deposit)
  accumulatedRewards: number; // rewards snapshot at lastCalcAt
  lastCalcAt: number;      // timestamp ms of last calc
}

// ─── Storage helpers ──────────────────────────────────
export function storageKey(addr: string): string {
  return `${STAKING_KEY}_${addr}`;
}

export function getLocalStake(addr: string): LocalStake | null {
  try {
    const raw = localStorage.getItem(storageKey(addr));
    return raw ? JSON.parse(raw) : null;
  } catch {
    return null;
  }
}

export function saveLocalStake(addr: string, stake: LocalStake): void {
  localStorage.setItem(storageKey(addr), JSON.stringify(stake));
}

export function clearLocalStake(addr: string): void {
  localStorage.removeItem(storageKey(addr));
}

// ─── Reward calculation ───────────────────────────────
/**
 * Calculate simulated rewards accrued since last checkpoint.
 * Formula: accumulatedRewards + principal × perSecondRate × elapsedSeconds × DEMO_MULTIPLIER
 *
 * @param stake  The local stake record.
 * @param now    Optional override for "current time" (ms). Defaults to Date.now().
 * @returns      Total accumulated rewards (prior + newly accrued).
 */
export function calcSimulatedRewards(stake: LocalStake, now?: number): number {
  if (stake.principal <= 0) return stake.accumulatedRewards;
  const currentTime = now ?? Date.now();
  const elapsedSec = Math.max(0, (currentTime - stake.lastCalcAt) / 1000);
  const newRewards = stake.principal * PER_SECOND_RATE * elapsedSec * DEMO_MULTIPLIER;
  return stake.accumulatedRewards + newRewards;
}

// ─── Metric helpers ───────────────────────────────────
/**
 * Compute the portfolio metrics that display on the dashboard.
 * Mirrors exactly what Portfolio.tsx computes from useStaking() outputs.
 */
export interface PortfolioMetrics {
  principalNum: number;
  rewardsNum: number;
  totalPosition: number;
  principalDisplay: string;
  rewardsDisplay: string;
  totalDisplay: string;
}

export function computeMetrics(
  principalStr: string,
  rewardsStr: string
): PortfolioMetrics {
  const principalNum = parseFloat(principalStr) || 0;
  const rewardsNum = parseFloat(rewardsStr) || 0;
  const totalPosition = principalNum + rewardsNum;
  return {
    principalNum,
    rewardsNum,
    totalPosition,
    principalDisplay: `${principalNum.toFixed(4)} MON`,
    rewardsDisplay: `${rewardsNum.toFixed(6)} MON`,
    totalDisplay: `${totalPosition.toFixed(4)} MON`,
  };
}

// ─── Deposit simulation ──────────────────────────────
/**
 * Simulate a deposit into the local stake.
 * Returns the updated stake record. Does NOT write to localStorage
 * (caller is responsible for that).
 */
export function simulateDeposit(
  existing: LocalStake | null,
  amount: number,
  now?: number
): LocalStake {
  const currentTime = now ?? Date.now();

  if (!existing || existing.principal <= 0) {
    return {
      principal: amount,
      depositedAt: currentTime,
      accumulatedRewards: 0,
      lastCalcAt: currentTime,
    };
  }

  // Snapshot rewards earned so far
  const rewards = calcSimulatedRewards(existing, currentTime);
  return {
    principal: existing.principal + amount,
    depositedAt: existing.depositedAt,
    accumulatedRewards: rewards,
    lastCalcAt: currentTime,
  };
}

// ─── Withdraw simulation ─────────────────────────────
/**
 * Simulate a withdrawal: principal + rewards become 0.
 * Returns the total withdrawn amount.
 */
export function simulateWithdraw(
  existing: LocalStake | null,
  now?: number
): { totalWithdrawn: number } {
  if (!existing || existing.principal <= 0) {
    return { totalWithdrawn: 0 };
  }
  const rewards = calcSimulatedRewards(existing, now);
  return { totalWithdrawn: existing.principal + rewards };
}
