import { expect } from "chai";
import hre from "hardhat";
import { loadFixture, time } from "@nomicfoundation/hardhat-network-helpers";

describe("StakingAdapter", function () {
  async function deployFixture() {
    const [owner, user1, user2, user3] = await hre.ethers.getSigners();

    const StakingAdapter = await hre.ethers.getContractFactory("StakingAdapter");
    const staking = await StakingAdapter.deploy();
    await staking.waitForDeployment();
    const stakingAddr = await staking.getAddress();

    const GameManager = await hre.ethers.getContractFactory("GameManager");
    const gameManager = await GameManager.deploy(stakingAddr);
    await gameManager.waitForDeployment();
    const gameManagerAddr = await gameManager.getAddress();

    // Link GameManager in StakingAdapter
    await staking.setGameManager(gameManagerAddr);

    return { staking, gameManager, stakingAddr, gameManagerAddr, owner, user1, user2, user3 };
  }

  // ─── Deployment ─────────────────────────────────────────────────────
  describe("Deployment", function () {
    it("Should set deployer as owner", async function () {
      const { staking, owner } = await loadFixture(deployFixture);
      expect(await staking.owner()).to.equal(owner.address);
    });

    it("Should set GameManager address correctly", async function () {
      const { staking, gameManagerAddr } = await loadFixture(deployFixture);
      expect(await staking.gameManager()).to.equal(gameManagerAddr);
    });

    it("Should reject setGameManager from non-owner", async function () {
      const { staking, user1, user2 } = await loadFixture(deployFixture);
      await expect(
        staking.connect(user1).setGameManager(user2.address)
      ).to.be.revertedWith("Not owner");
    });

    it("Should reject zero address for GameManager", async function () {
      const { staking } = await loadFixture(deployFixture);
      await expect(
        staking.setGameManager(hre.ethers.ZeroAddress)
      ).to.be.revertedWith("Zero address");
    });
  });

  // ─── Deposits ───────────────────────────────────────────────────────
  describe("Deposits", function () {
    it("Should accept MON deposit and credit to correct user", async function () {
      const { staking, user1 } = await loadFixture(deployFixture);
      const depositAmount = hre.ethers.parseEther("1.0");

      await staking.connect(user1).deposit({ value: depositAmount });

      // Verify principal is stored for user1's address specifically
      expect(await staking.getPrincipal(user1.address)).to.equal(depositAmount);
      expect(await staking.principal(user1.address)).to.equal(depositAmount);
    });

    it("Should NOT credit deposit to wrong address", async function () {
      const { staking, user1, user2 } = await loadFixture(deployFixture);
      const depositAmount = hre.ethers.parseEther("5.0");

      // user1 deposits
      await staking.connect(user1).deposit({ value: depositAmount });

      // user2 should have 0 principal
      expect(await staking.getPrincipal(user2.address)).to.equal(0n);
      // user1 should have the full amount
      expect(await staking.getPrincipal(user1.address)).to.equal(depositAmount);
    });

    it("Should handle multiple deposits from same user", async function () {
      const { staking, user1 } = await loadFixture(deployFixture);

      await staking.connect(user1).deposit({ value: hre.ethers.parseEther("1.0") });
      await staking.connect(user1).deposit({ value: hre.ethers.parseEther("2.0") });

      expect(await staking.getPrincipal(user1.address)).to.equal(
        hre.ethers.parseEther("3.0")
      );
    });

    it("Should isolate deposits between different users", async function () {
      const { staking, user1, user2, user3 } = await loadFixture(deployFixture);

      await staking.connect(user1).deposit({ value: hre.ethers.parseEther("1.0") });
      await staking.connect(user2).deposit({ value: hre.ethers.parseEther("3.0") });
      await staking.connect(user3).deposit({ value: hre.ethers.parseEther("7.5") });

      expect(await staking.getPrincipal(user1.address)).to.equal(hre.ethers.parseEther("1.0"));
      expect(await staking.getPrincipal(user2.address)).to.equal(hre.ethers.parseEther("3.0"));
      expect(await staking.getPrincipal(user3.address)).to.equal(hre.ethers.parseEther("7.5"));
    });

    it("Should reject zero deposit", async function () {
      const { staking, user1 } = await loadFixture(deployFixture);
      await expect(
        staking.connect(user1).deposit({ value: 0 })
      ).to.be.revertedWith("Zero deposit");
    });

    it("Should emit Deposited event with correct user and amount", async function () {
      const { staking, user1 } = await loadFixture(deployFixture);
      const amount = hre.ethers.parseEther("2.5");

      await expect(staking.connect(user1).deposit({ value: amount }))
        .to.emit(staking, "Deposited")
        .withArgs(user1.address, amount);
    });

    it("Should update contract ETH balance on deposit", async function () {
      const { staking, stakingAddr, user1 } = await loadFixture(deployFixture);
      const amount = hre.ethers.parseEther("10.0");

      const balBefore = await hre.ethers.provider.getBalance(stakingAddr);
      await staking.connect(user1).deposit({ value: amount });
      const balAfter = await hre.ethers.provider.getBalance(stakingAddr);

      expect(balAfter - balBefore).to.equal(amount);
    });

    it("Should set stakeTimestamp on deposit", async function () {
      const { staking, user1 } = await loadFixture(deployFixture);

      await staking.connect(user1).deposit({ value: hre.ethers.parseEther("1.0") });

      const ts = await staking.stakeTimestamp(user1.address);
      expect(ts).to.be.gt(0n);
    });
  });

  // ─── Reward Accrual ─────────────────────────────────────────────────
  describe("Reward Accrual", function () {
    it("Should accrue rewards over time (8% APY)", async function () {
      const { staking, user1 } = await loadFixture(deployFixture);
      const amount = hre.ethers.parseEther("100.0");

      await staking.connect(user1).deposit({ value: amount });

      // Advance 1 year
      await time.increase(365 * 24 * 60 * 60);

      const rewards = await staking.getAccruedRewards(user1.address);
      const expected = hre.ethers.parseEther("8.0"); // 100 * 8% = 8

      // Allow small rounding difference (within 0.001 ETH)
      expect(rewards).to.be.closeTo(expected, hre.ethers.parseEther("0.01"));
    });

    it("Should return 0 rewards with no deposit", async function () {
      const { staking, user2 } = await loadFixture(deployFixture);
      expect(await staking.getAccruedRewards(user2.address)).to.equal(0n);
    });

    it("Should accrue rewards proportional to principal", async function () {
      const { staking, user1, user2 } = await loadFixture(deployFixture);

      await staking.connect(user1).deposit({ value: hre.ethers.parseEther("100.0") });
      await staking.connect(user2).deposit({ value: hre.ethers.parseEther("200.0") });

      await time.increase(365 * 24 * 60 * 60);

      const r1 = await staking.getAccruedRewards(user1.address);
      const r2 = await staking.getAccruedRewards(user2.address);

      // user2 should earn ~2x user1's rewards
      // Allow ±1% tolerance
      const ratio = Number(r2) / Number(r1);
      expect(ratio).to.be.closeTo(2.0, 0.05);
    });

    it("Should accrue rewards for correct user only", async function () {
      const { staking, user1, user2 } = await loadFixture(deployFixture);

      await staking.connect(user1).deposit({ value: hre.ethers.parseEther("50.0") });

      await time.increase(30 * 24 * 60 * 60); // 30 days

      // user1 earns, user2 doesn't
      expect(await staking.getAccruedRewards(user1.address)).to.be.gt(0n);
      expect(await staking.getAccruedRewards(user2.address)).to.equal(0n);
    });

    it("Should snapshot rewards on second deposit", async function () {
      const { staking, user1 } = await loadFixture(deployFixture);

      await staking.connect(user1).deposit({ value: hre.ethers.parseEther("100.0") });

      await time.increase(365 * 24 * 60 * 60); // 1 year

      // Second deposit should snapshot ~8 ETH rewards
      await staking.connect(user1).deposit({ value: hre.ethers.parseEther("50.0") });

      expect(await staking.getPrincipal(user1.address)).to.equal(
        hre.ethers.parseEther("150.0")
      );

      // Stored rewards should be ~8 ETH
      const storedRewards = await staking.rewardBalance(user1.address);
      expect(storedRewards).to.be.closeTo(
        hre.ethers.parseEther("8.0"),
        hre.ethers.parseEther("0.01")
      );
    });

    it("Should return total available rewards (stored + accrued)", async function () {
      const { staking, user1 } = await loadFixture(deployFixture);

      await staking.connect(user1).deposit({ value: hre.ethers.parseEther("100.0") });
      await time.increase(365 * 24 * 60 * 60);

      // Second deposit snapshots rewards
      await staking.connect(user1).deposit({ value: hre.ethers.parseEther("0.01") });

      await time.increase(30 * 24 * 60 * 60); // 30 more days

      const available = await staking.getAvailableRewards(user1.address);
      // Should be > 8 ETH (snapshot from year 1 + 30 days more)
      expect(available).to.be.gt(hre.ethers.parseEther("8.0"));
    });
  });

  // ─── Withdrawals ────────────────────────────────────────────────────
  describe("Withdrawals", function () {
    it("Should withdraw principal + rewards to correct address", async function () {
      const { staking, stakingAddr, user1, owner } = await loadFixture(deployFixture);
      const depositAmt = hre.ethers.parseEther("100.0");

      // Fund contract for reward payouts
      await owner.sendTransaction({ to: stakingAddr, value: hre.ethers.parseEther("20.0") });

      await staking.connect(user1).deposit({ value: depositAmt });
      await time.increase(365 * 24 * 60 * 60);

      const balBefore = await hre.ethers.provider.getBalance(user1.address);
      const tx = await staking.connect(user1).withdraw();
      const receipt = await tx.wait();
      const gasUsed = receipt!.gasUsed * receipt!.gasPrice;
      const balAfter = await hre.ethers.provider.getBalance(user1.address);

      // User should receive principal + ~8% rewards
      const received = balAfter - balBefore + gasUsed;
      expect(received).to.be.closeTo(
        hre.ethers.parseEther("108.0"),
        hre.ethers.parseEther("0.1")
      );
    });

    it("Should reset principal to 0 after withdrawal", async function () {
      const { staking, stakingAddr, user1, owner } = await loadFixture(deployFixture);

      // Fund contract to cover any micro-rewards from timestamp drift
      await owner.sendTransaction({ to: stakingAddr, value: hre.ethers.parseEther("1.0") });

      await staking.connect(user1).deposit({ value: hre.ethers.parseEther("5.0") });
      await staking.connect(user1).withdraw();

      expect(await staking.getPrincipal(user1.address)).to.equal(0n);
      expect(await staking.rewardBalance(user1.address)).to.equal(0n);
      expect(await staking.stakeTimestamp(user1.address)).to.equal(0n);
    });

    it("Should not affect other users on withdrawal", async function () {
      const { staking, stakingAddr, user1, user2, owner } = await loadFixture(deployFixture);

      // Fund contract to cover any micro-rewards
      await owner.sendTransaction({ to: stakingAddr, value: hre.ethers.parseEther("1.0") });

      await staking.connect(user1).deposit({ value: hre.ethers.parseEther("5.0") });
      await staking.connect(user2).deposit({ value: hre.ethers.parseEther("10.0") });

      await staking.connect(user1).withdraw();

      // user2 should be unaffected
      expect(await staking.getPrincipal(user2.address)).to.equal(
        hre.ethers.parseEther("10.0")
      );
    });

    it("Should reject withdrawal with no deposit", async function () {
      const { staking, user1 } = await loadFixture(deployFixture);
      await expect(staking.connect(user1).withdraw()).to.be.revertedWith("No deposit");
    });

    it("Should emit Withdrawn event", async function () {
      const { staking, stakingAddr, user1, owner } = await loadFixture(deployFixture);

      // Fund contract to cover any micro-rewards from timestamp drift
      await owner.sendTransaction({ to: stakingAddr, value: hre.ethers.parseEther("1.0") });

      await staking.connect(user1).deposit({ value: hre.ethers.parseEther("5.0") });

      await expect(staking.connect(user1).withdraw())
        .to.emit(staking, "Withdrawn");
    });
  });

  // ─── Address Correctness (Critical Tests) ──────────────────────────
  describe("Address Correctness — Deposit & Principal Mapping", function () {
    it("msg.sender address matches principal mapping key", async function () {
      const { staking, user1, user2, user3 } = await loadFixture(deployFixture);

      // Multiple users deposit
      await staking.connect(user1).deposit({ value: hre.ethers.parseEther("1.0") });
      await staking.connect(user2).deposit({ value: hre.ethers.parseEther("2.0") });
      await staking.connect(user3).deposit({ value: hre.ethers.parseEther("3.0") });

      // Each user's principal maps to THEIR address only
      const p1 = await staking.principal(user1.address);
      const p2 = await staking.principal(user2.address);
      const p3 = await staking.principal(user3.address);

      expect(p1).to.equal(hre.ethers.parseEther("1.0"), "user1 principal mismatch");
      expect(p2).to.equal(hre.ethers.parseEther("2.0"), "user2 principal mismatch");
      expect(p3).to.equal(hre.ethers.parseEther("3.0"), "user3 principal mismatch");
    });

    it("Deposited event logs the correct sender address", async function () {
      const { staking, user1, user2 } = await loadFixture(deployFixture);

      // user1 deposits
      await expect(staking.connect(user1).deposit({ value: hre.ethers.parseEther("5.0") }))
        .to.emit(staking, "Deposited")
        .withArgs(user1.address, hre.ethers.parseEther("5.0"));

      // user2 deposits — event should log user2's address, not user1's
      await expect(staking.connect(user2).deposit({ value: hre.ethers.parseEther("7.0") }))
        .to.emit(staking, "Deposited")
        .withArgs(user2.address, hre.ethers.parseEther("7.0"));
    });

    it("Sequential deposits from user1 do not leak into user2", async function () {
      const { staking, user1, user2 } = await loadFixture(deployFixture);

      for (let i = 0; i < 5; i++) {
        await staking.connect(user1).deposit({ value: hre.ethers.parseEther("1.0") });
      }

      expect(await staking.getPrincipal(user1.address)).to.equal(
        hre.ethers.parseEther("5.0")
      );
      expect(await staking.getPrincipal(user2.address)).to.equal(0n);
    });

    it("Withdrawal sends funds to correct address", async function () {
      const { staking, stakingAddr, user1, user2, owner } = await loadFixture(deployFixture);

      // Fund contract to cover any micro-rewards
      await owner.sendTransaction({ to: stakingAddr, value: hre.ethers.parseEther("1.0") });

      await staking.connect(user1).deposit({ value: hre.ethers.parseEther("10.0") });
      await staking.connect(user2).deposit({ value: hre.ethers.parseEther("20.0") });

      const user2BalBefore = await hre.ethers.provider.getBalance(user2.address);

      // user1 withdraws — should not affect user2 balance
      await staking.connect(user1).withdraw();

      const user2BalAfter = await hre.ethers.provider.getBalance(user2.address);
      expect(user2BalAfter).to.equal(user2BalBefore);
    });

    it("Re-deposit after full withdrawal maps to correct user", async function () {
      const { staking, stakingAddr, user1, owner } = await loadFixture(deployFixture);

      // Fund contract to cover any micro-rewards
      await owner.sendTransaction({ to: stakingAddr, value: hre.ethers.parseEther("1.0") });

      await staking.connect(user1).deposit({ value: hre.ethers.parseEther("5.0") });
      await staking.connect(user1).withdraw();

      expect(await staking.getPrincipal(user1.address)).to.equal(0n);

      // Re-deposit
      await staking.connect(user1).deposit({ value: hre.ethers.parseEther("3.0") });
      expect(await staking.getPrincipal(user1.address)).to.equal(
        hre.ethers.parseEther("3.0")
      );
    });
  });

  // ─── GameManager Integration ────────────────────────────────────────
  describe("GameManager Reward Deductions", function () {
    it("Should only allow GameManager to deduct rewards", async function () {
      const { staking, user1 } = await loadFixture(deployFixture);

      await staking.connect(user1).deposit({ value: hre.ethers.parseEther("100.0") });
      await time.increase(365 * 24 * 60 * 60);

      await expect(
        staking.connect(user1).deductRewards(user1.address, hre.ethers.parseEther("1.0"))
      ).to.be.revertedWith("Not game manager");
    });

    it("Should only allow GameManager to credit rewards", async function () {
      const { staking, user1 } = await loadFixture(deployFixture);

      await expect(
        staking.connect(user1).creditRewards(user1.address, hre.ethers.parseEther("1.0"))
      ).to.be.revertedWith("Not game manager");
    });
  });

  // ─── Faucet ─────────────────────────────────────────────────────────
  describe("Faucet", function () {
    it("Should dispense MON from funded contract", async function () {
      const { staking, stakingAddr, user1, owner } = await loadFixture(deployFixture);

      // Fund the contract
      await owner.sendTransaction({ to: stakingAddr, value: hre.ethers.parseEther("100.0") });

      const balBefore = await hre.ethers.provider.getBalance(user1.address);
      const tx = await staking.connect(user1).faucet();
      const receipt = await tx.wait();
      const gasUsed = receipt!.gasUsed * receipt!.gasPrice;
      const balAfter = await hre.ethers.provider.getBalance(user1.address);

      const received = balAfter - balBefore + gasUsed;
      // Should be between 5 and 50 ETH (FAUCET_MIN and FAUCET_MAX)
      expect(received).to.be.gte(hre.ethers.parseEther("5.0"));
      expect(received).to.be.lte(hre.ethers.parseEther("50.0"));
    });

    it("Should enforce cooldown", async function () {
      const { staking, stakingAddr, user1, owner } = await loadFixture(deployFixture);

      await owner.sendTransaction({ to: stakingAddr, value: hre.ethers.parseEther("200.0") });

      await staking.connect(user1).faucet();

      await expect(staking.connect(user1).faucet()).to.be.revertedWith(
        "Faucet cooldown active"
      );
    });

    it("Should allow claim after cooldown expires", async function () {
      const { staking, stakingAddr, user1, owner } = await loadFixture(deployFixture);

      await owner.sendTransaction({ to: stakingAddr, value: hre.ethers.parseEther("200.0") });

      await staking.connect(user1).faucet();
      await time.increase(3601); // 1 hour + 1 second
      await staking.connect(user1).faucet(); // Should not revert
    });

    it("Should report cooldown remaining correctly", async function () {
      const { staking, stakingAddr, user1, owner } = await loadFixture(deployFixture);

      // Before any claim, cooldown should be 0
      expect(await staking.faucetCooldownRemaining(user1.address)).to.equal(0n);

      await owner.sendTransaction({ to: stakingAddr, value: hre.ethers.parseEther("100.0") });
      await staking.connect(user1).faucet();

      const remaining = await staking.faucetCooldownRemaining(user1.address);
      expect(remaining).to.be.gt(0n);
      expect(remaining).to.be.lte(3600n);
    });
  });

  // ─── Receive ────────────────────────────────────────────────────────
  describe("Receive", function () {
    it("Contract should accept plain ETH transfers", async function () {
      const { staking, stakingAddr, owner } = await loadFixture(deployFixture);

      await owner.sendTransaction({ to: stakingAddr, value: hre.ethers.parseEther("1.0") });

      const bal = await hre.ethers.provider.getBalance(stakingAddr);
      expect(bal).to.equal(hre.ethers.parseEther("1.0"));
    });
  });
});
