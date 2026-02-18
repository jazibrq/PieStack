import { describe, it, expect, beforeEach, afterEach } from 'vitest';
import {
  APY_RATE,
  SECONDS_PER_YEAR,
  PER_SECOND_RATE,
  DEMO_MULTIPLIER,
  STAKING_KEY,
  calcSimulatedRewards,
  computeMetrics,
  simulateDeposit,
  simulateWithdraw,
  getLocalStake,
  saveLocalStake,
  clearLocalStake,
  storageKey,
  type LocalStake,
} from '@/lib/staking-sim';

// ──────────────────────────────────────────────────────
// CONSTANTS
// ──────────────────────────────────────────────────────
describe('Staking Constants', () => {
  it('APY_RATE is 8%', () => {
    expect(APY_RATE).toBe(0.08);
  });

  it('SECONDS_PER_YEAR accounts for leap years', () => {
    expect(SECONDS_PER_YEAR).toBeCloseTo(365.25 * 24 * 3600, 0);
  });

  it('PER_SECOND_RATE = APY / SECONDS_PER_YEAR', () => {
    expect(PER_SECOND_RATE).toBeCloseTo(APY_RATE / SECONDS_PER_YEAR, 20);
  });

  it('DEMO_MULTIPLIER is 100,000', () => {
    expect(DEMO_MULTIPLIER).toBe(100_000);
  });
});

// ──────────────────────────────────────────────────────
// LOCAL STORAGE OPERATIONS
// ──────────────────────────────────────────────────────
describe('Local Storage Operations', () => {
  const addr = '0xTestAddress1234';
  const keysToClean: string[] = [];

  function trackAndSave(a: string, s: LocalStake) {
    keysToClean.push(storageKey(a));
    saveLocalStake(a, s);
  }

  afterEach(() => {
    keysToClean.forEach(k => localStorage.removeItem(k));
    keysToClean.length = 0;
  });

  it('storageKey builds correct key', () => {
    expect(storageKey(addr)).toBe(`${STAKING_KEY}_${addr}`);
  });

  it('getLocalStake returns null when no data', () => {
    expect(getLocalStake(addr)).toBeNull();
  });

  it('saveLocalStake + getLocalStake roundtrips correctly', () => {
    const stake: LocalStake = {
      principal: 5.0,
      depositedAt: 1000000,
      accumulatedRewards: 0.123,
      lastCalcAt: 1000000,
    };
    trackAndSave(addr, stake);

    const loaded = getLocalStake(addr);
    expect(loaded).not.toBeNull();
    expect(loaded!.principal).toBe(5.0);
    expect(loaded!.depositedAt).toBe(1000000);
    expect(loaded!.accumulatedRewards).toBe(0.123);
    expect(loaded!.lastCalcAt).toBe(1000000);
  });

  it('clearLocalStake removes the data', () => {
    const stake: LocalStake = {
      principal: 10.0,
      depositedAt: 1000000,
      accumulatedRewards: 0,
      lastCalcAt: 1000000,
    };
    trackAndSave(addr, stake);
    expect(getLocalStake(addr)).not.toBeNull();

    clearLocalStake(addr);
    expect(getLocalStake(addr)).toBeNull();
  });

  it('different addresses have independent storage', () => {
    const addr2 = '0xOtherAddress5678';
    trackAndSave(addr, {
      principal: 5,
      depositedAt: 100,
      accumulatedRewards: 0.1,
      lastCalcAt: 100,
    });
    trackAndSave(addr2, {
      principal: 99,
      depositedAt: 200,
      accumulatedRewards: 3.0,
      lastCalcAt: 200,
    });

    expect(getLocalStake(addr)!.principal).toBe(5);
    expect(getLocalStake(addr2)!.principal).toBe(99);
  });

  it('getLocalStake handles corrupt JSON gracefully', () => {
    const key = storageKey(addr);
    keysToClean.push(key);
    localStorage.setItem(key, 'NOT_VALID_JSON{{');
    expect(getLocalStake(addr)).toBeNull();
  });
});

// ──────────────────────────────────────────────────────
// REWARD CALCULATION
// ──────────────────────────────────────────────────────
describe('calcSimulatedRewards', () => {
  it('returns accumulatedRewards when principal is 0', () => {
    const stake: LocalStake = {
      principal: 0,
      depositedAt: 0,
      accumulatedRewards: 1.5,
      lastCalcAt: 0,
    };
    expect(calcSimulatedRewards(stake, Date.now())).toBe(1.5);
  });

  it('returns accumulatedRewards when principal is negative', () => {
    const stake: LocalStake = {
      principal: -1,
      depositedAt: 0,
      accumulatedRewards: 2.0,
      lastCalcAt: 0,
    };
    expect(calcSimulatedRewards(stake, Date.now())).toBe(2.0);
  });

  it('returns 0 when stakes are brand-new (zero elapsed time)', () => {
    const now = Date.now();
    const stake: LocalStake = {
      principal: 10.0,
      depositedAt: now,
      accumulatedRewards: 0,
      lastCalcAt: now,
    };
    expect(calcSimulatedRewards(stake, now)).toBe(0);
  });

  it('accrues correct rewards for 1 real second elapsed', () => {
    // 1 real second × 100,000 multiplier = 100,000 simulated seconds
    const now = 1_000_000_000;
    const stake: LocalStake = {
      principal: 10.0,
      depositedAt: now,
      accumulatedRewards: 0,
      lastCalcAt: now,
    };

    const oneSecLater = now + 1000; // 1 second = 1000 ms
    const rewards = calcSimulatedRewards(stake, oneSecLater);

    // Expected: 10 × (0.08 / 31_557_600) × 1 × 100_000
    const expected = 10 * PER_SECOND_RATE * 1 * DEMO_MULTIPLIER;
    expect(rewards).toBeCloseTo(expected, 10);
  });

  it('accrues correct rewards for 60 real seconds elapsed', () => {
    const now = 1_000_000_000;
    const stake: LocalStake = {
      principal: 5.0,
      depositedAt: now,
      accumulatedRewards: 0,
      lastCalcAt: now,
    };

    const sixtySecLater = now + 60_000; // 60 seconds
    const rewards = calcSimulatedRewards(stake, sixtySecLater);

    // Expected: 5 × perSecondRate × 60 × 100_000
    const expected = 5 * PER_SECOND_RATE * 60 * DEMO_MULTIPLIER;
    expect(rewards).toBeCloseTo(expected, 10);
  });

  it('adds to existing accumulated rewards', () => {
    const now = 1_000_000_000;
    const stake: LocalStake = {
      principal: 10.0,
      depositedAt: now - 999999,
      accumulatedRewards: 5.0, // Already had 5 MON rewards
      lastCalcAt: now,
    };

    const tenSecLater = now + 10_000;
    const rewards = calcSimulatedRewards(stake, tenSecLater);
    const newRewards = 10 * PER_SECOND_RATE * 10 * DEMO_MULTIPLIER;
    expect(rewards).toBeCloseTo(5.0 + newRewards, 10);
  });

  it('larger principal accrues proportionally more', () => {
    const now = 1_000_000_000;
    const small: LocalStake = {
      principal: 1.0,
      depositedAt: now,
      accumulatedRewards: 0,
      lastCalcAt: now,
    };
    const large: LocalStake = {
      principal: 10.0,
      depositedAt: now,
      accumulatedRewards: 0,
      lastCalcAt: now,
    };

    const later = now + 5000;
    const smallRewards = calcSimulatedRewards(small, later);
    const largeRewards = calcSimulatedRewards(large, later);
    expect(largeRewards / smallRewards).toBeCloseTo(10.0, 5);
  });

  it('handles elapsed time of 0 (no double-counting)', () => {
    const now = Date.now();
    const stake: LocalStake = {
      principal: 100,
      depositedAt: now - 60000,
      accumulatedRewards: 42.0,
      lastCalcAt: now,
    };
    // Calling with same timestamp as lastCalcAt should add 0 new rewards
    expect(calcSimulatedRewards(stake, now)).toBe(42.0);
  });
});

// ──────────────────────────────────────────────────────
// PORTFOLIO METRICS
// ──────────────────────────────────────────────────────
describe('computeMetrics', () => {
  it('computes correct values for zero inputs', () => {
    const m = computeMetrics('0', '0');
    expect(m.principalNum).toBe(0);
    expect(m.rewardsNum).toBe(0);
    expect(m.totalPosition).toBe(0);
    expect(m.principalDisplay).toBe('0.0000 MON');
    expect(m.rewardsDisplay).toBe('0.000000 MON');
    expect(m.totalDisplay).toBe('0.0000 MON');
  });

  it('computes correct values for principal only (no rewards)', () => {
    const m = computeMetrics('5.0', '0');
    expect(m.principalNum).toBe(5);
    expect(m.rewardsNum).toBe(0);
    expect(m.totalPosition).toBe(5);
    expect(m.principalDisplay).toBe('5.0000 MON');
    expect(m.rewardsDisplay).toBe('0.000000 MON');
    expect(m.totalDisplay).toBe('5.0000 MON');
  });

  it('computes correct values for principal + rewards', () => {
    const m = computeMetrics('10.0', '0.5');
    expect(m.principalNum).toBe(10);
    expect(m.rewardsNum).toBe(0.5);
    expect(m.totalPosition).toBe(10.5);
    expect(m.principalDisplay).toBe('10.0000 MON');
    expect(m.rewardsDisplay).toBe('0.500000 MON');
    expect(m.totalDisplay).toBe('10.5000 MON');
  });

  it('handles small reward amounts with precision', () => {
    const m = computeMetrics('1.0', '0.000001');
    expect(m.rewardsNum).toBeCloseTo(0.000001, 8);
    expect(m.totalPosition).toBeCloseTo(1.000001, 8);
    expect(m.rewardsDisplay).toBe('0.000001 MON');
  });

  it('handles very large amounts', () => {
    const m = computeMetrics('100000', '5000.123456');
    expect(m.principalNum).toBe(100000);
    expect(m.rewardsNum).toBeCloseTo(5000.123456, 4);
    expect(m.totalPosition).toBeCloseTo(105000.123456, 4);
  });

  it('handles non-numeric strings gracefully', () => {
    const m = computeMetrics('not_a_number', 'also_bad');
    expect(m.principalNum).toBe(0);
    expect(m.rewardsNum).toBe(0);
    expect(m.totalPosition).toBe(0);
  });

  it('handles empty strings', () => {
    const m = computeMetrics('', '');
    expect(m.principalNum).toBe(0);
    expect(m.rewardsNum).toBe(0);
  });

  it('totalPosition equals principal + rewards exactly', () => {
    const m = computeMetrics('7.25', '3.75');
    expect(m.totalPosition).toBe(m.principalNum + m.rewardsNum);
    expect(m.totalPosition).toBe(11);
  });
});

// ──────────────────────────────────────────────────────
// DEPOSIT SIMULATION
// ──────────────────────────────────────────────────────
describe('simulateDeposit', () => {
  it('creates new stake when no existing data', () => {
    const now = 1_700_000_000_000;
    const result = simulateDeposit(null, 5.0, now);
    expect(result.principal).toBe(5.0);
    expect(result.depositedAt).toBe(now);
    expect(result.accumulatedRewards).toBe(0);
    expect(result.lastCalcAt).toBe(now);
  });

  it('creates new stake when existing has 0 principal', () => {
    const existing: LocalStake = {
      principal: 0,
      depositedAt: 1000,
      accumulatedRewards: 0,
      lastCalcAt: 1000,
    };
    const now = 2000;
    const result = simulateDeposit(existing, 3.0, now);
    expect(result.principal).toBe(3.0);
    expect(result.depositedAt).toBe(now);
  });

  it('adds to existing principal and snapshots rewards', () => {
    const baseTime = 1_700_000_000_000;
    const existing: LocalStake = {
      principal: 5.0,
      depositedAt: baseTime,
      accumulatedRewards: 0,
      lastCalcAt: baseTime,
    };

    // 10 seconds later, deposit 3 more
    const depositTime = baseTime + 10_000;
    const result = simulateDeposit(existing, 3.0, depositTime);

    expect(result.principal).toBe(8.0);
    expect(result.depositedAt).toBe(baseTime); // preserves original
    expect(result.lastCalcAt).toBe(depositTime);
    // Should have accrued some rewards during those 10 seconds
    expect(result.accumulatedRewards).toBeGreaterThan(0);
  });

  it('multiple deposits accumulate correctly', () => {
    const t0 = 1_700_000_000_000;
    let stake = simulateDeposit(null, 5.0, t0);
    expect(stake.principal).toBe(5.0);

    const t1 = t0 + 5000; // 5 seconds later
    stake = simulateDeposit(stake, 3.0, t1);
    expect(stake.principal).toBe(8.0);
    expect(stake.accumulatedRewards).toBeGreaterThan(0);

    const t2 = t1 + 5000; // another 5 seconds
    stake = simulateDeposit(stake, 2.0, t2);
    expect(stake.principal).toBe(10.0);
    // Rewards should be even higher now
    const rewards = calcSimulatedRewards(stake, t2);
    expect(rewards).toBeGreaterThan(0);
  });
});

// ──────────────────────────────────────────────────────
// WITHDRAW SIMULATION
// ──────────────────────────────────────────────────────
describe('simulateWithdraw', () => {
  it('returns 0 when no existing data', () => {
    const result = simulateWithdraw(null);
    expect(result.totalWithdrawn).toBe(0);
  });

  it('returns 0 when principal is 0', () => {
    const existing: LocalStake = {
      principal: 0,
      depositedAt: 1000,
      accumulatedRewards: 0,
      lastCalcAt: 1000,
    };
    const result = simulateWithdraw(existing);
    expect(result.totalWithdrawn).toBe(0);
  });

  it('returns principal + accrued rewards', () => {
    const baseTime = 1_700_000_000_000;
    const existing: LocalStake = {
      principal: 10.0,
      depositedAt: baseTime,
      accumulatedRewards: 0,
      lastCalcAt: baseTime,
    };

    const withdrawTime = baseTime + 30_000; // 30 seconds later
    const result = simulateWithdraw(existing, withdrawTime);

    const expectedRewards = calcSimulatedRewards(existing, withdrawTime);
    expect(result.totalWithdrawn).toBeCloseTo(10.0 + expectedRewards, 10);
    expect(result.totalWithdrawn).toBeGreaterThan(10.0); // rewards > 0
  });
});

// ──────────────────────────────────────────────────────
// END-TO-END SIMULATION FLOW
// ──────────────────────────────────────────────────────
describe('End-to-End Simulation', () => {
  const addr = '0xE2E_Test_Address';
  const keysToClean: string[] = [];

  function trackAndSave(a: string, s: LocalStake) {
    keysToClean.push(storageKey(a));
    saveLocalStake(a, s);
  }

  afterEach(() => {
    keysToClean.forEach(k => localStorage.removeItem(k));
    keysToClean.length = 0;
  });

  it('full flow: deposit → accrue rewards → check metrics → withdraw', () => {
    const t0 = 1_700_000_000_000;

    // 1. Deposit 5 MON
    const stake = simulateDeposit(null, 5.0, t0);
    trackAndSave(addr, stake);

    // Verify saved
    const saved = getLocalStake(addr);
    expect(saved).not.toBeNull();
    expect(saved!.principal).toBe(5.0);

    // 2. Check metrics immediately after deposit
    const m1 = computeMetrics(saved!.principal.toString(), '0');
    expect(m1.principalNum).toBe(5.0);
    expect(m1.rewardsNum).toBe(0);
    expect(m1.totalPosition).toBe(5.0);
    expect(m1.principalDisplay).toBe('5.0000 MON');

    // 3. Time passes — 60 real seconds (simulated ~70 days)
    const t1 = t0 + 60_000;
    const rewards = calcSimulatedRewards(saved!, t1);
    expect(rewards).toBeGreaterThan(0);

    // 4. Check metrics with rewards
    const m2 = computeMetrics(saved!.principal.toString(), rewards.toFixed(18));
    expect(m2.principalNum).toBe(5.0);
    expect(m2.rewardsNum).toBeGreaterThan(0);
    expect(m2.totalPosition).toBeGreaterThan(5.0);
    expect(m2.totalPosition).toBe(m2.principalNum + m2.rewardsNum);

    // 5. Withdraw
    const wResult = simulateWithdraw(saved!, t1);
    expect(wResult.totalWithdrawn).toBeCloseTo(5.0 + rewards, 10);
    expect(wResult.totalWithdrawn).toBeGreaterThan(5.0);

    // 6. Clear and verify empty
    clearLocalStake(addr);
    expect(getLocalStake(addr)).toBeNull();
    const m3 = computeMetrics('0', '0');
    expect(m3.totalPosition).toBe(0);
  });

  it('two addresses staking independently have isolated data', () => {
    const addr2 = '0xSecond_Address';
    const t0 = 1_700_000_000_000;

    // Address 1 deposits 10 MON
    const s1 = simulateDeposit(null, 10.0, t0);
    trackAndSave(addr, s1);

    // Address 2 deposits 3 MON
    const s2 = simulateDeposit(null, 3.0, t0);
    trackAndSave(addr2, s2);

    // 10 seconds later
    const t1 = t0 + 10_000;
    const r1 = calcSimulatedRewards(getLocalStake(addr)!, t1);
    const r2 = calcSimulatedRewards(getLocalStake(addr2)!, t1);

    // Address 1 rewards should be ~3.33x address 2 rewards (10/3)
    expect(r1 / r2).toBeCloseTo(10 / 3, 3);

    // Clearing one shouldn't affect the other
    clearLocalStake(addr);
    expect(getLocalStake(addr)).toBeNull();
    expect(getLocalStake(addr2)).not.toBeNull();
    expect(getLocalStake(addr2)!.principal).toBe(3.0);
  });

  it('rewards compound correctly across multiple checkpoints', () => {
    const t0 = 1_700_000_000_000;

    // Deposit 10 MON
    let stake = simulateDeposit(null, 10.0, t0);

    // Checkpoint 1: 5 seconds later
    const t1 = t0 + 5_000;
    const r1 = calcSimulatedRewards(stake, t1);
    stake = { ...stake, accumulatedRewards: r1, lastCalcAt: t1 };

    // Checkpoint 2: 5 more seconds later
    const t2 = t1 + 5_000;
    const r2 = calcSimulatedRewards(stake, t2);

    // Total rewards at t2 should equal what we'd get from t0 to t2 in one shot
    const singleShotStake: LocalStake = {
      principal: 10.0,
      depositedAt: t0,
      accumulatedRewards: 0,
      lastCalcAt: t0,
    };
    const singleShotR = calcSimulatedRewards(singleShotStake, t2);

    // They should be equal (no compounding loss from checkpointing)
    expect(r2).toBeCloseTo(singleShotR, 10);
  });

  it('portfolio display formats match expected patterns', () => {
    // Test the display format matches what the UI cards show
    const m = computeMetrics('9.7082', '0.123456789');

    // Total Deposited card: 4 decimal places
    expect(m.principalDisplay).toBe('9.7082 MON');

    // Available Rewards card: 6 decimal places
    expect(m.rewardsDisplay).toBe('0.123457 MON');

    // Total Position card: 4 decimal places
    expect(m.totalDisplay).toBe('9.8317 MON');

    // Verify total = principal + rewards
    expect(m.totalPosition).toBeCloseTo(9.7082 + 0.123456789, 6);
  });
});
