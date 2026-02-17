import hre from "hardhat";
import "@nomicfoundation/hardhat-ethers";

async function main() {
  const ethers = hre.ethers;
  const [deployer] = await ethers.getSigners();
  console.log("Deploying with account:", deployer.address);

  // 1. Deploy StakingAdapter
  const StakingAdapter = await ethers.getContractFactory("StakingAdapter");
  const stakingAdapter = await StakingAdapter.deploy();
  await stakingAdapter.waitForDeployment();
  const stakingAddr = await stakingAdapter.getAddress();
  console.log("StakingAdapter deployed to:", stakingAddr);

  // 2. Deploy GameManager (linked to StakingAdapter)
  const GameManager = await ethers.getContractFactory("GameManager");
  const gameManager = await GameManager.deploy(stakingAddr);
  await gameManager.waitForDeployment();
  const gameManagerAddr = await gameManager.getAddress();
  console.log("GameManager deployed to:", gameManagerAddr);

  // 3. Authorize GameManager in StakingAdapter
  const tx = await stakingAdapter.setGameManager(gameManagerAddr);
  await tx.wait();
  console.log("GameManager authorized in StakingAdapter");

  console.log("\n--- Deployment Summary ---");
  console.log("StakingAdapter:", stakingAddr);
  console.log("GameManager:   ", gameManagerAddr);
  console.log("\nUpdate src/config/contracts.ts with these addresses.");
}

main()
  .then(() => process.exit(0))
  .catch((error) => {
    console.error(error);
    process.exit(1);
  });
