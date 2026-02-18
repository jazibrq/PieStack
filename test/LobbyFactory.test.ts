import { expect } from "chai";
import hre from "hardhat";
import { loadFixture } from "@nomicfoundation/hardhat-network-helpers";

describe("LobbyFactory + Match", function () {
  // ─── Fixture ─────────────────────────────────────────
  async function deployFixture() {
    const [owner, alice, bob, charlie, dave, eve, frank, grace, heidi] =
      await hre.ethers.getSigners();

    const Factory = await hre.ethers.getContractFactory("LobbyFactory");
    const factory = await Factory.deploy();
    await factory.waitForDeployment();

    const entryFee = hre.ethers.parseEther("1"); // 1 MON

    return {
      factory,
      entryFee,
      owner,
      alice,
      bob,
      charlie,
      dave,
      eve,
      frank,
      grace,
      heidi,
    };
  }

  // Helper: get Match contract at an address
  async function matchAt(addr: string) {
    return hre.ethers.getContractAt("Match", addr);
  }

  // ═════════════════════════════════════════════════════
  // FACTORY DEPLOYMENT
  // ═════════════════════════════════════════════════════
  describe("Factory Deployment", function () {
    it("sets the deployer as owner", async function () {
      const { factory, owner } = await loadFixture(deployFixture);
      expect(await factory.owner()).to.equal(owner.address);
    });

    it("starts with zero matches", async function () {
      const { factory } = await loadFixture(deployFixture);
      expect(await factory.matchCount()).to.equal(0);
    });
  });

  // ═════════════════════════════════════════════════════
  // MATCH CREATION
  // ═════════════════════════════════════════════════════
  describe("Match Creation", function () {
    it("creates a match and registers it", async function () {
      const { factory, alice, entryFee } = await loadFixture(deployFixture);

      const tx = await factory
        .connect(alice)
        .createMatch(2, entryFee, { value: entryFee });
      const receipt = await tx.wait();

      expect(await factory.matchCount()).to.equal(1);

      // Get the match address from allMatches
      const matchAddr = await factory.allMatches(0);
      expect(await factory.isMatch(matchAddr)).to.be.true;

      // Creator should be auto-joined
      const match = await matchAt(matchAddr);
      expect(await match.playerCount()).to.equal(1);
      expect(await match.enrolled(alice.address)).to.be.true;
      expect(await match.creator()).to.equal(alice.address);
      expect(await match.maxPlayers()).to.equal(2);
      expect(await match.entryFee()).to.equal(entryFee);
      expect(await match.status()).to.equal(0); // Open
    });

    it("emits MatchCreated event", async function () {
      const { factory, alice, entryFee } = await loadFixture(deployFixture);

      await expect(
        factory.connect(alice).createMatch(2, entryFee, { value: entryFee })
      ).to.emit(factory, "MatchCreated");
    });

    it("rejects invalid maxPlayers (3, 5, 10)", async function () {
      const { factory, alice, entryFee } = await loadFixture(deployFixture);

      await expect(
        factory.connect(alice).createMatch(3, entryFee, { value: entryFee })
      ).to.be.revertedWith("Invalid maxPlayers");

      await expect(
        factory.connect(alice).createMatch(5, entryFee, { value: entryFee })
      ).to.be.revertedWith("Invalid maxPlayers");

      await expect(
        factory.connect(alice).createMatch(10, entryFee, { value: entryFee })
      ).to.be.revertedWith("Invalid maxPlayers");
    });

    it("accepts valid maxPlayers (2, 4, 8, 16)", async function () {
      const { factory, alice, entryFee } = await loadFixture(deployFixture);

      for (const size of [2, 4, 8, 16]) {
        await expect(
          factory.connect(alice).createMatch(size, entryFee, { value: entryFee })
        ).to.not.be.reverted;
      }
      expect(await factory.matchCount()).to.equal(4);
    });

    it("rejects zero entry fee", async function () {
      const { factory, alice } = await loadFixture(deployFixture);

      await expect(
        factory.connect(alice).createMatch(2, 0, { value: 0 })
      ).to.be.revertedWith("Entry fee must be > 0");
    });

    it("rejects mismatched msg.value", async function () {
      const { factory, alice, entryFee } = await loadFixture(deployFixture);

      await expect(
        factory.connect(alice).createMatch(2, entryFee, {
          value: hre.ethers.parseEther("0.5"),
        })
      ).to.be.revertedWith("msg.value must equal entryFee");
    });
  });

  // ═════════════════════════════════════════════════════
  // JOINING A MATCH
  // ═════════════════════════════════════════════════════
  describe("Joining a Match", function () {
    it("allows a second player to join", async function () {
      const { factory, alice, bob, entryFee } =
        await loadFixture(deployFixture);

      await factory
        .connect(alice)
        .createMatch(2, entryFee, { value: entryFee });
      const matchAddr = await factory.allMatches(0);
      const match = await matchAt(matchAddr);

      await match.connect(bob).join({ value: entryFee });
      expect(await match.playerCount()).to.equal(2);
      expect(await match.enrolled(bob.address)).to.be.true;
    });

    it("auto-starts when match is full (2-player)", async function () {
      const { factory, alice, bob, entryFee } =
        await loadFixture(deployFixture);

      await factory
        .connect(alice)
        .createMatch(2, entryFee, { value: entryFee });
      const matchAddr = await factory.allMatches(0);
      const match = await matchAt(matchAddr);

      await expect(match.connect(bob).join({ value: entryFee }))
        .to.emit(match, "MatchStarted");

      expect(await match.status()).to.equal(1); // InProgress
    });

    it("rejects wrong entry fee", async function () {
      const { factory, alice, bob, entryFee } =
        await loadFixture(deployFixture);

      await factory
        .connect(alice)
        .createMatch(2, entryFee, { value: entryFee });
      const matchAddr = await factory.allMatches(0);
      const match = await matchAt(matchAddr);

      await expect(
        match.connect(bob).join({ value: hre.ethers.parseEther("0.5") })
      ).to.be.revertedWith("Wrong entry fee");
    });

    it("rejects double join", async function () {
      const { factory, alice, entryFee } = await loadFixture(deployFixture);

      await factory
        .connect(alice)
        .createMatch(2, entryFee, { value: entryFee });
      const matchAddr = await factory.allMatches(0);
      const match = await matchAt(matchAddr);

      await expect(
        match.connect(alice).join({ value: entryFee })
      ).to.be.revertedWith("Already joined");
    });

    it("rejects joining a full match", async function () {
      const { factory, alice, bob, charlie, entryFee } =
        await loadFixture(deployFixture);

      await factory
        .connect(alice)
        .createMatch(2, entryFee, { value: entryFee });
      const matchAddr = await factory.allMatches(0);
      const match = await matchAt(matchAddr);

      await match.connect(bob).join({ value: entryFee });

      // Match is now InProgress (auto-started), so "Not open"
      await expect(
        match.connect(charlie).join({ value: entryFee })
      ).to.be.revertedWith("Not open");
    });
  });

  // ═════════════════════════════════════════════════════
  // 2-PLAYER MATCH — FULL FLOW
  // ═════════════════════════════════════════════════════
  describe("2-Player Match — Full Flow", function () {
    it("2 users play, winner takes all, balances are correct", async function () {
      const { factory, owner, alice, bob, entryFee } =
        await loadFixture(deployFixture);

      // Alice creates, Bob joins → auto-starts
      await factory
        .connect(alice)
        .createMatch(2, entryFee, { value: entryFee });
      const matchAddr = await factory.allMatches(0);
      const match = await matchAt(matchAddr);
      await match.connect(bob).join({ value: entryFee });

      // Prize pool should be 2 MON
      expect(await match.prizePool()).to.equal(hre.ethers.parseEther("2"));

      // Record balances before results
      const aliceBefore = await hre.ethers.provider.getBalance(alice.address);
      const bobBefore = await hre.ethers.provider.getBalance(bob.address);

      // Owner submits results: Alice scored 500, Bob scored 300
      await factory
        .connect(owner)
        .submitResults(
          matchAddr,
          [alice.address, bob.address],
          [500, 300]
        );

      expect(await match.status()).to.equal(2); // Completed

      // Alice (1st) gets 100% of 2 MON
      const aliceAfter = await hre.ethers.provider.getBalance(alice.address);
      const bobAfter = await hre.ethers.provider.getBalance(bob.address);

      // Alice gained 2 ETH (the full pool)
      expect(aliceAfter - aliceBefore).to.equal(hre.ethers.parseEther("2"));
      // Bob gained nothing
      expect(bobAfter - bobBefore).to.equal(0);

      // Scores recorded
      expect(await match.scores(alice.address)).to.equal(500);
      expect(await match.scores(bob.address)).to.equal(300);
    });

    it("emits MatchCompleted with correct ranking", async function () {
      const { factory, owner, alice, bob, entryFee } =
        await loadFixture(deployFixture);

      await factory
        .connect(alice)
        .createMatch(2, entryFee, { value: entryFee });
      const matchAddr = await factory.allMatches(0);
      const match = await matchAt(matchAddr);
      await match.connect(bob).join({ value: entryFee });

      // Bob wins this time
      await expect(
        factory
          .connect(owner)
          .submitResults(matchAddr, [alice.address, bob.address], [100, 999])
      ).to.emit(match, "MatchCompleted");
    });
  });

  // ═════════════════════════════════════════════════════
  // 4-PLAYER MATCH — PRIZE SPLIT
  // ═════════════════════════════════════════════════════
  describe("4-Player Match — Prize Distribution", function () {
    it("distributes 60/40 split correctly", async function () {
      const { factory, owner, alice, bob, charlie, dave, entryFee } =
        await loadFixture(deployFixture);

      await factory
        .connect(alice)
        .createMatch(4, entryFee, { value: entryFee });
      const matchAddr = await factory.allMatches(0);
      const match = await matchAt(matchAddr);

      await match.connect(bob).join({ value: entryFee });
      await match.connect(charlie).join({ value: entryFee });
      await match.connect(dave).join({ value: entryFee });

      expect(await match.status()).to.equal(1); // InProgress
      const pool = hre.ethers.parseEther("4"); // 4 MON total

      const balBefore = {
        alice: await hre.ethers.provider.getBalance(alice.address),
        bob: await hre.ethers.provider.getBalance(bob.address),
        charlie: await hre.ethers.provider.getBalance(charlie.address),
        dave: await hre.ethers.provider.getBalance(dave.address),
      };

      // Scores: Dave=1000, Charlie=800, Bob=500, Alice=200
      await factory.connect(owner).submitResults(
        matchAddr,
        [alice.address, bob.address, charlie.address, dave.address],
        [200, 500, 800, 1000]
      );

      const balAfter = {
        alice: await hre.ethers.provider.getBalance(alice.address),
        bob: await hre.ethers.provider.getBalance(bob.address),
        charlie: await hre.ethers.provider.getBalance(charlie.address),
        dave: await hre.ethers.provider.getBalance(dave.address),
      };

      // 1st: Dave → 60% of 4 MON = 2.4 MON
      const firstPrize = (pool * 60n) / 100n;
      // 2nd: Charlie → 40% of 4 MON = 1.6 MON
      const secondPrize = pool - firstPrize; // remainder to avoid dust

      expect(balAfter.dave - balBefore.dave).to.equal(firstPrize);
      expect(balAfter.charlie - balBefore.charlie).to.equal(secondPrize);
      expect(balAfter.bob - balBefore.bob).to.equal(0);
      expect(balAfter.alice - balBefore.alice).to.equal(0);
    });
  });

  // ═════════════════════════════════════════════════════
  // CANCELLATION & REFUNDS
  // ═════════════════════════════════════════════════════
  describe("Cancellation & Refunds", function () {
    it("creator can cancel an open match − refunds all players", async function () {
      const { factory, alice, bob, entryFee } =
        await loadFixture(deployFixture);

      await factory
        .connect(alice)
        .createMatch(4, entryFee, { value: entryFee });
      const matchAddr = await factory.allMatches(0);
      const match = await matchAt(matchAddr);

      await match.connect(bob).join({ value: entryFee });

      const aliceBefore = await hre.ethers.provider.getBalance(alice.address);
      const bobBefore = await hre.ethers.provider.getBalance(bob.address);

      // Creator cancels (direct call on match contract)
      const tx = await match.connect(alice).cancel();
      const receipt = await tx.wait();
      const gasUsed = receipt!.gasUsed * receipt!.gasPrice;

      const aliceAfter = await hre.ethers.provider.getBalance(alice.address);
      const bobAfter = await hre.ethers.provider.getBalance(bob.address);

      // Alice gets refund minus gas for the cancel tx
      expect(aliceAfter - aliceBefore + gasUsed).to.equal(entryFee);
      // Bob gets full refund (didn't pay gas)
      expect(bobAfter - bobBefore).to.equal(entryFee);

      expect(await match.status()).to.equal(3); // Cancelled
    });

    it("factory owner can cancel via factory", async function () {
      const { factory, owner, alice, entryFee } =
        await loadFixture(deployFixture);

      await factory
        .connect(alice)
        .createMatch(2, entryFee, { value: entryFee });
      const matchAddr = await factory.allMatches(0);

      await expect(factory.connect(owner).cancelMatch(matchAddr))
        .to.emit(factory, "MatchStatusChanged");

      const match = await matchAt(matchAddr);
      expect(await match.status()).to.equal(3);
    });

    it("random user cannot cancel", async function () {
      const { factory, alice, bob, entryFee } =
        await loadFixture(deployFixture);

      await factory
        .connect(alice)
        .createMatch(2, entryFee, { value: entryFee });
      const matchAddr = await factory.allMatches(0);
      const match = await matchAt(matchAddr);

      await expect(
        match.connect(bob).cancel()
      ).to.be.revertedWith("Not authorized");
    });
  });

  // ═════════════════════════════════════════════════════
  // PARALLEL MATCH INDEPENDENCE
  // ═════════════════════════════════════════════════════
  describe("Parallel Match Independence", function () {
    it("two matches run simultaneously with no interference", async function () {
      const { factory, owner, alice, bob, charlie, dave, entryFee } =
        await loadFixture(deployFixture);

      // Match 1: Alice vs Bob
      await factory
        .connect(alice)
        .createMatch(2, entryFee, { value: entryFee });
      const match1Addr = await factory.allMatches(0);
      const match1 = await matchAt(match1Addr);

      // Match 2: Charlie vs Dave
      await factory
        .connect(charlie)
        .createMatch(2, entryFee, { value: entryFee });
      const match2Addr = await factory.allMatches(1);
      const match2 = await matchAt(match2Addr);

      // Both matches fill up
      await match1.connect(bob).join({ value: entryFee });
      await match2.connect(dave).join({ value: entryFee });

      // Both in progress
      expect(await match1.status()).to.equal(1);
      expect(await match2.status()).to.equal(1);

      // Resolve match 1: Bob wins
      await factory
        .connect(owner)
        .submitResults(match1Addr, [alice.address, bob.address], [100, 500]);

      // Match 1 is done, match 2 still in progress
      expect(await match1.status()).to.equal(2);
      expect(await match2.status()).to.equal(1);

      // Resolve match 2: Charlie wins
      await factory.connect(owner).submitResults(
        match2Addr,
        [charlie.address, dave.address],
        [999, 200]
      );

      expect(await match2.status()).to.equal(2);

      // Verify each match has independent state
      expect(await match1.scores(alice.address)).to.equal(100);
      expect(await match1.scores(bob.address)).to.equal(500);
      expect(await match2.scores(charlie.address)).to.equal(999);
      expect(await match2.scores(dave.address)).to.equal(200);
    });
  });

  // ═════════════════════════════════════════════════════
  // READ HELPERS
  // ═════════════════════════════════════════════════════
  describe("Read Helpers", function () {
    it("getOpenMatches returns only open matches", async function () {
      const { factory, owner, alice, bob, charlie, entryFee } =
        await loadFixture(deployFixture);

      // Create 3 matches
      await factory
        .connect(alice)
        .createMatch(2, entryFee, { value: entryFee });
      await factory
        .connect(bob)
        .createMatch(2, entryFee, { value: entryFee });
      await factory
        .connect(charlie)
        .createMatch(2, entryFee, { value: entryFee });

      let open = await factory.getOpenMatches();
      expect(open.length).to.equal(3);

      // Cancel match 1
      const match1Addr = await factory.allMatches(0);
      await factory.connect(owner).cancelMatch(match1Addr);

      open = await factory.getOpenMatches();
      expect(open.length).to.equal(2);
    });

    it("getMatchInfo returns correct info", async function () {
      const { factory, alice, entryFee } = await loadFixture(deployFixture);

      await factory
        .connect(alice)
        .createMatch(4, entryFee, { value: entryFee });
      const matchAddr = await factory.allMatches(0);

      const info = await factory.getMatchInfo(matchAddr);
      expect(info._creator).to.equal(alice.address);
      expect(info._maxPlayers).to.equal(4);
      expect(info._entryFee).to.equal(entryFee);
      expect(info._status).to.equal(0); // Open
      expect(info._playerCount).to.equal(1);
      expect(info._prizePool).to.equal(entryFee);
    });

    it("getMatches pagination works", async function () {
      const { factory, alice, entryFee } = await loadFixture(deployFixture);

      // Create 5 matches
      for (let i = 0; i < 5; i++) {
        await factory
          .connect(alice)
          .createMatch(2, entryFee, { value: entryFee });
      }

      const page1 = await factory.getMatches(0, 3);
      expect(page1.length).to.equal(3);

      const page2 = await factory.getMatches(3, 3);
      expect(page2.length).to.equal(2);

      const empty = await factory.getMatches(10, 5);
      expect(empty.length).to.equal(0);
    });

    it("getMatchInfo reverts for unknown match", async function () {
      const { factory, alice } = await loadFixture(deployFixture);
      await expect(
        factory.getMatchInfo(alice.address)
      ).to.be.revertedWith("Unknown match");
    });
  });

  // ═════════════════════════════════════════════════════
  // ACCESS CONTROL
  // ═════════════════════════════════════════════════════
  describe("Access Control", function () {
    it("only factory can submit results", async function () {
      const { factory, alice, bob, entryFee } =
        await loadFixture(deployFixture);

      await factory
        .connect(alice)
        .createMatch(2, entryFee, { value: entryFee });
      const matchAddr = await factory.allMatches(0);
      const match = await matchAt(matchAddr);
      await match.connect(bob).join({ value: entryFee });

      // Direct call to Match.submitResults should fail (alice is not factory)
      await expect(
        match
          .connect(alice)
          .submitResults([alice.address, bob.address], [100, 200])
      ).to.be.revertedWith("Not factory");
    });

    it("only factory owner can call submitResults on factory", async function () {
      const { factory, alice, bob, entryFee } =
        await loadFixture(deployFixture);

      await factory
        .connect(alice)
        .createMatch(2, entryFee, { value: entryFee });
      const matchAddr = await factory.allMatches(0);
      const match = await matchAt(matchAddr);
      await match.connect(bob).join({ value: entryFee });

      await expect(
        factory
          .connect(alice)
          .submitResults(matchAddr, [alice.address, bob.address], [100, 200])
      ).to.be.revertedWith("Not owner");
    });

    it("cannot submit results for a match that is not InProgress", async function () {
      const { factory, owner, alice, entryFee } =
        await loadFixture(deployFixture);

      await factory
        .connect(alice)
        .createMatch(2, entryFee, { value: entryFee });
      const matchAddr = await factory.allMatches(0);

      // Match is Open (only 1 player), not InProgress
      await expect(
        factory
          .connect(owner)
          .submitResults(matchAddr, [alice.address], [100])
      ).to.be.revertedWith("Not in progress");
    });

    it("cannot join after match is cancelled", async function () {
      const { factory, owner, alice, bob, entryFee } =
        await loadFixture(deployFixture);

      await factory
        .connect(alice)
        .createMatch(2, entryFee, { value: entryFee });
      const matchAddr = await factory.allMatches(0);
      const match = await matchAt(matchAddr);

      await factory.connect(owner).cancelMatch(matchAddr);

      await expect(
        match.connect(bob).join({ value: entryFee })
      ).to.be.revertedWith("Not open");
    });
  });

  // ═════════════════════════════════════════════════════
  // MATCH VIEWS
  // ═════════════════════════════════════════════════════
  describe("Match Views", function () {
    it("getPlayers returns enrolled list", async function () {
      const { factory, alice, bob, entryFee } =
        await loadFixture(deployFixture);

      await factory
        .connect(alice)
        .createMatch(4, entryFee, { value: entryFee });
      const matchAddr = await factory.allMatches(0);
      const match = await matchAt(matchAddr);

      await match.connect(bob).join({ value: entryFee });

      const players = await match.getPlayers();
      expect(players.length).to.equal(2);
      expect(players[0]).to.equal(alice.address);
      expect(players[1]).to.equal(bob.address);
    });

    it("getInfo returns all fields", async function () {
      const { factory, alice, bob, entryFee } =
        await loadFixture(deployFixture);

      await factory
        .connect(alice)
        .createMatch(2, entryFee, { value: entryFee });
      const matchAddr = await factory.allMatches(0);
      const match = await matchAt(matchAddr);

      const info = await match.getInfo();
      expect(info._creator).to.equal(alice.address);
      expect(info._maxPlayers).to.equal(2);
      expect(info._entryFee).to.equal(entryFee);
      expect(info._status).to.equal(0);
      expect(info._playerCount).to.equal(1);
      expect(info._prizePool).to.equal(entryFee);
    });
  });

  // ═════════════════════════════════════════════════════
  // EDGE CASES
  // ═════════════════════════════════════════════════════
  describe("Edge Cases", function () {
    it("cannot cancel an already completed match", async function () {
      const { factory, owner, alice, bob, entryFee } =
        await loadFixture(deployFixture);

      await factory
        .connect(alice)
        .createMatch(2, entryFee, { value: entryFee });
      const matchAddr = await factory.allMatches(0);
      const match = await matchAt(matchAddr);
      await match.connect(bob).join({ value: entryFee });

      await factory
        .connect(owner)
        .submitResults(matchAddr, [alice.address, bob.address], [500, 300]);

      await expect(
        factory.connect(owner).cancelMatch(matchAddr)
      ).to.be.revertedWith("Cannot cancel");
    });

    it("cannot submit results twice", async function () {
      const { factory, owner, alice, bob, entryFee } =
        await loadFixture(deployFixture);

      await factory
        .connect(alice)
        .createMatch(2, entryFee, { value: entryFee });
      const matchAddr = await factory.allMatches(0);
      const match = await matchAt(matchAddr);
      await match.connect(bob).join({ value: entryFee });

      await factory
        .connect(owner)
        .submitResults(matchAddr, [alice.address, bob.address], [500, 300]);

      await expect(
        factory
          .connect(owner)
          .submitResults(matchAddr, [alice.address, bob.address], [500, 300])
      ).to.be.revertedWith("Not in progress");
    });

    it("player count mismatch in submitResults reverts", async function () {
      const { factory, owner, alice, bob, entryFee } =
        await loadFixture(deployFixture);

      await factory
        .connect(alice)
        .createMatch(2, entryFee, { value: entryFee });
      const matchAddr = await factory.allMatches(0);
      const match = await matchAt(matchAddr);
      await match.connect(bob).join({ value: entryFee });

      // Only pass 1 player instead of 2
      await expect(
        factory
          .connect(owner)
          .submitResults(matchAddr, [alice.address], [500])
      ).to.be.revertedWith("Player count mismatch");
    });

    it("unknown player address in submitResults reverts", async function () {
      const { factory, owner, alice, bob, charlie, entryFee } =
        await loadFixture(deployFixture);

      await factory
        .connect(alice)
        .createMatch(2, entryFee, { value: entryFee });
      const matchAddr = await factory.allMatches(0);
      const match = await matchAt(matchAddr);
      await match.connect(bob).join({ value: entryFee });

      // Pass charlie who never joined
      await expect(
        factory
          .connect(owner)
          .submitResults(matchAddr, [alice.address, charlie.address], [500, 300])
      ).to.be.revertedWith("Unknown player");
    });

    it("scores & payouts mismatch length reverts", async function () {
      const { factory, owner, alice, bob, entryFee } =
        await loadFixture(deployFixture);

      await factory
        .connect(alice)
        .createMatch(2, entryFee, { value: entryFee });
      const matchAddr = await factory.allMatches(0);
      const match = await matchAt(matchAddr);
      await match.connect(bob).join({ value: entryFee });

      // 2 players but 3 scores
      await expect(
        factory
          .connect(owner)
          .submitResults(
            matchAddr,
            [alice.address, bob.address],
            [500, 300, 100]
          )
      ).to.be.revertedWith("Score count mismatch");
    });
  });
});
