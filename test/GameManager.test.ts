import { expect } from "chai";
import hre from "hardhat";
import { loadFixture, time } from "@nomicfoundation/hardhat-network-helpers";

describe("GameManager", function () {
  async function deployFixture() {
    const [admin, host, player1, player2, player3] = await hre.ethers.getSigners();

    const StakingAdapter = await hre.ethers.getContractFactory("StakingAdapter");
    const staking = await StakingAdapter.deploy();
    await staking.waitForDeployment();
    const stakingAddr = await staking.getAddress();

    const GameManager = await hre.ethers.getContractFactory("GameManager");
    const gameManager = await GameManager.deploy(stakingAddr);
    await gameManager.waitForDeployment();

    await staking.setGameManager(await gameManager.getAddress());

    return { staking, gameManager, stakingAddr, admin, host, player1, player2, player3 };
  }

  /** Helper: deposit MON then advance time so user has enough rewards for buy-in */
  async function fundWithRewards(
    staking: any,
    user: any,
    depositAmount: bigint,
    advanceSeconds: number
  ) {
    await staking.connect(user).deposit({ value: depositAmount });
    if (advanceSeconds > 0) {
      await time.increase(advanceSeconds);
    }
  }

  // ─── Deployment ─────────────────────────────────────────────────────
  describe("Deployment", function () {
    it("Should set admin to deployer", async function () {
      const { gameManager, admin } = await loadFixture(deployFixture);
      expect(await gameManager.admin()).to.equal(admin.address);
    });

    it("Should link StakingAdapter correctly", async function () {
      const { gameManager, stakingAddr } = await loadFixture(deployFixture);
      expect(await gameManager.stakingAdapter()).to.equal(stakingAddr);
    });

    it("Should reject zero address for StakingAdapter", async function () {
      const GameManager = await hre.ethers.getContractFactory("GameManager");
      await expect(
        GameManager.deploy(hre.ethers.ZeroAddress)
      ).to.be.revertedWith("Zero address");
    });
  });

  // ─── Lobby Creation ─────────────────────────────────────────────────
  describe("Lobby Creation", function () {
    it("Should create lobby and auto-join host", async function () {
      const { staking, gameManager, host } = await loadFixture(deployFixture);

      // Fund host with enough rewards
      await fundWithRewards(staking, host, hre.ethers.parseEther("100.0"), 365 * 24 * 3600);

      const buyIn = hre.ethers.parseEther("1.0");
      await gameManager.connect(host).createLobby(buyIn, 4);

      const lobby = await gameManager.getLobby(0);
      expect(lobby.host).to.equal(host.address);
      expect(lobby.buyIn).to.equal(buyIn);
      expect(lobby.maxPlayers).to.equal(4n);
      expect(lobby.active).to.be.true;
      expect(lobby.resolved).to.be.false;
      expect(lobby.players.length).to.equal(1);
      expect(lobby.players[0]).to.equal(host.address);
      expect(lobby.prizePool).to.equal(buyIn);
    });

    it("Should emit LobbyCreated event", async function () {
      const { staking, gameManager, host } = await loadFixture(deployFixture);
      await fundWithRewards(staking, host, hre.ethers.parseEther("100.0"), 365 * 24 * 3600);

      const buyIn = hre.ethers.parseEther("2.0");
      await expect(gameManager.connect(host).createLobby(buyIn, 2))
        .to.emit(gameManager, "LobbyCreated")
        .withArgs(0, host.address, buyIn, 2);
    });

    it("Should reject buy-in of 0", async function () {
      const { gameManager, host } = await loadFixture(deployFixture);
      await expect(
        gameManager.connect(host).createLobby(0, 2)
      ).to.be.revertedWith("Buy-in must be > 0");
    });

    it("Should reject invalid max players (<2 or >16)", async function () {
      const { staking, gameManager, host } = await loadFixture(deployFixture);
      await fundWithRewards(staking, host, hre.ethers.parseEther("100.0"), 365 * 24 * 3600);

      await expect(
        gameManager.connect(host).createLobby(hre.ethers.parseEther("1.0"), 1)
      ).to.be.revertedWith("Invalid player count");

      await expect(
        gameManager.connect(host).createLobby(hre.ethers.parseEther("1.0"), 17)
      ).to.be.revertedWith("Invalid player count");
    });

    it("Should increment lobby count", async function () {
      const { staking, gameManager, host } = await loadFixture(deployFixture);
      await fundWithRewards(staking, host, hre.ethers.parseEther("100.0"), 365 * 24 * 3600);

      expect(await gameManager.getLobbyCount()).to.equal(0n);

      await gameManager.connect(host).createLobby(hre.ethers.parseEther("1.0"), 2);
      expect(await gameManager.getLobbyCount()).to.equal(1n);

      await gameManager.connect(host).createLobby(hre.ethers.parseEther("2.0"), 4);
      expect(await gameManager.getLobbyCount()).to.equal(2n);
    });
  });

  // ─── Joining Lobbies ────────────────────────────────────────────────
  describe("Joining Lobbies", function () {
    it("Should allow player to join and deduct buy-in", async function () {
      const { staking, gameManager, host, player1 } = await loadFixture(deployFixture);

      const buyIn = hre.ethers.parseEther("1.0");
      await fundWithRewards(staking, host, hre.ethers.parseEther("100.0"), 365 * 24 * 3600);
      await fundWithRewards(staking, player1, hre.ethers.parseEther("100.0"), 365 * 24 * 3600);

      await gameManager.connect(host).createLobby(buyIn, 4);
      await gameManager.connect(player1).joinLobby(0);

      const lobby = await gameManager.getLobby(0);
      expect(lobby.players.length).to.equal(2);
      expect(lobby.players[1]).to.equal(player1.address);
      expect(lobby.prizePool).to.equal(buyIn * 2n);
    });

    it("Should prevent double-join", async function () {
      const { staking, gameManager, host } = await loadFixture(deployFixture);
      await fundWithRewards(staking, host, hre.ethers.parseEther("100.0"), 365 * 24 * 3600);

      await gameManager.connect(host).createLobby(hre.ethers.parseEther("1.0"), 4);

      // Host is already in lobby
      await expect(gameManager.connect(host).joinLobby(0)).to.be.revertedWith(
        "Already in lobby"
      );
    });

    it("Should prevent joining full lobby", async function () {
      const { staking, gameManager, host, player1, player2 } = await loadFixture(deployFixture);
      const buyIn = hre.ethers.parseEther("0.5");

      await fundWithRewards(staking, host, hre.ethers.parseEther("100.0"), 365 * 24 * 3600);
      await fundWithRewards(staking, player1, hre.ethers.parseEther("100.0"), 365 * 24 * 3600);
      await fundWithRewards(staking, player2, hre.ethers.parseEther("100.0"), 365 * 24 * 3600);

      await gameManager.connect(host).createLobby(buyIn, 2); // Max 2 players
      await gameManager.connect(player1).joinLobby(0);

      await expect(gameManager.connect(player2).joinLobby(0)).to.be.revertedWith("Lobby full");
    });

    it("Should prevent joining inactive lobby", async function () {
      const { staking, gameManager, host, player1 } = await loadFixture(deployFixture);
      await fundWithRewards(staking, host, hre.ethers.parseEther("100.0"), 365 * 24 * 3600);
      await fundWithRewards(staking, player1, hre.ethers.parseEther("100.0"), 365 * 24 * 3600);

      await gameManager.connect(host).createLobby(hre.ethers.parseEther("1.0"), 4);
      await gameManager.connect(host).cancelLobby(0);

      await expect(gameManager.connect(player1).joinLobby(0)).to.be.revertedWith(
        "Lobby not active"
      );
    });
  });

  // ─── Game Resolution ────────────────────────────────────────────────
  describe("Game Resolution", function () {
    it("Should resolve and credit winner with full prize pool", async function () {
      const { staking, gameManager, admin, host, player1 } = await loadFixture(deployFixture);
      const buyIn = hre.ethers.parseEther("5.0");

      await fundWithRewards(staking, host, hre.ethers.parseEther("100.0"), 365 * 24 * 3600);
      await fundWithRewards(staking, player1, hre.ethers.parseEther("100.0"), 365 * 24 * 3600);

      const rewardsBefore = await staking.getAvailableRewards(player1.address);

      await gameManager.connect(host).createLobby(buyIn, 2);
      await gameManager.connect(player1).joinLobby(0);

      const rewardsAfterJoin = await staking.getAvailableRewards(player1.address);

      // Resolve: player1 wins
      await gameManager.connect(admin).resolveGame(0, player1.address);

      const rewardsAfterWin = await staking.getAvailableRewards(player1.address);
      const lobby = await gameManager.getLobby(0);

      expect(lobby.resolved).to.be.true;
      expect(lobby.active).to.be.false;

      // Winner should have more rewards than after joining (got prize pool credited)
      expect(rewardsAfterWin).to.be.gt(rewardsAfterJoin);
    });

    it("Should only allow admin to resolve", async function () {
      const { staking, gameManager, host, player1 } = await loadFixture(deployFixture);
      await fundWithRewards(staking, host, hre.ethers.parseEther("100.0"), 365 * 24 * 3600);
      await fundWithRewards(staking, player1, hre.ethers.parseEther("100.0"), 365 * 24 * 3600);

      await gameManager.connect(host).createLobby(hre.ethers.parseEther("1.0"), 2);
      await gameManager.connect(player1).joinLobby(0);

      await expect(
        gameManager.connect(host).resolveGame(0, host.address)
      ).to.be.revertedWith("Not admin");
    });

    it("Should reject resolving with winner not in lobby", async function () {
      const { staking, gameManager, admin, host, player1, player2 } = await loadFixture(deployFixture);
      await fundWithRewards(staking, host, hre.ethers.parseEther("100.0"), 365 * 24 * 3600);
      await fundWithRewards(staking, player1, hre.ethers.parseEther("100.0"), 365 * 24 * 3600);

      await gameManager.connect(host).createLobby(hre.ethers.parseEther("1.0"), 2);
      await gameManager.connect(player1).joinLobby(0);

      await expect(
        gameManager.connect(admin).resolveGame(0, player2.address)
      ).to.be.revertedWith("Winner not in lobby");
    });

    it("Should reject double resolution", async function () {
      const { staking, gameManager, admin, host, player1 } = await loadFixture(deployFixture);
      await fundWithRewards(staking, host, hre.ethers.parseEther("100.0"), 365 * 24 * 3600);
      await fundWithRewards(staking, player1, hre.ethers.parseEther("100.0"), 365 * 24 * 3600);

      await gameManager.connect(host).createLobby(hre.ethers.parseEther("1.0"), 2);
      await gameManager.connect(player1).joinLobby(0);
      await gameManager.connect(admin).resolveGame(0, host.address);

      await expect(
        gameManager.connect(admin).resolveGame(0, host.address)
      ).to.be.revertedWith("Lobby not active");
    });
  });

  // ─── Lobby Cancellation ─────────────────────────────────────────────
  describe("Lobby Cancellation", function () {
    it("Host can cancel and refund all players", async function () {
      const { staking, gameManager, host, player1 } = await loadFixture(deployFixture);
      const buyIn = hre.ethers.parseEther("3.0");

      await fundWithRewards(staking, host, hre.ethers.parseEther("100.0"), 365 * 24 * 3600);
      await fundWithRewards(staking, player1, hre.ethers.parseEther("100.0"), 365 * 24 * 3600);

      const hostRewardsBefore = await staking.getAvailableRewards(host.address);
      const p1RewardsBefore = await staking.getAvailableRewards(player1.address);

      await gameManager.connect(host).createLobby(buyIn, 4);
      await gameManager.connect(player1).joinLobby(0);

      await gameManager.connect(host).cancelLobby(0);

      const hostRewardsAfter = await staking.getAvailableRewards(host.address);
      const p1RewardsAfter = await staking.getAvailableRewards(player1.address);

      // Rewards should be approximately restored (small time-based accrual difference is OK)
      expect(hostRewardsAfter).to.be.closeTo(hostRewardsBefore, hre.ethers.parseEther("0.01"));
      expect(p1RewardsAfter).to.be.closeTo(p1RewardsBefore, hre.ethers.parseEther("0.01"));

      const lobby = await gameManager.getLobby(0);
      expect(lobby.active).to.be.false;
    });

    it("Admin can cancel any lobby", async function () {
      const { staking, gameManager, admin, host } = await loadFixture(deployFixture);
      await fundWithRewards(staking, host, hre.ethers.parseEther("100.0"), 365 * 24 * 3600);

      await gameManager.connect(host).createLobby(hre.ethers.parseEther("1.0"), 2);
      await gameManager.connect(admin).cancelLobby(0); // Admin cancels host's lobby

      const lobby = await gameManager.getLobby(0);
      expect(lobby.active).to.be.false;
    });

    it("Random player cannot cancel", async function () {
      const { staking, gameManager, host, player1 } = await loadFixture(deployFixture);
      await fundWithRewards(staking, host, hre.ethers.parseEther("100.0"), 365 * 24 * 3600);

      await gameManager.connect(host).createLobby(hre.ethers.parseEther("1.0"), 2);

      await expect(
        gameManager.connect(player1).cancelLobby(0)
      ).to.be.revertedWith("Not authorized");
    });
  });

  // ─── View Functions ─────────────────────────────────────────────────
  describe("View Functions", function () {
    it("getLobbyPlayerCount returns correct count", async function () {
      const { staking, gameManager, host, player1 } = await loadFixture(deployFixture);
      await fundWithRewards(staking, host, hre.ethers.parseEther("100.0"), 365 * 24 * 3600);
      await fundWithRewards(staking, player1, hre.ethers.parseEther("100.0"), 365 * 24 * 3600);

      await gameManager.connect(host).createLobby(hre.ethers.parseEther("1.0"), 4);
      expect(await gameManager.getLobbyPlayerCount(0)).to.equal(1n);

      await gameManager.connect(player1).joinLobby(0);
      expect(await gameManager.getLobbyPlayerCount(0)).to.equal(2n);
    });
  });
});
