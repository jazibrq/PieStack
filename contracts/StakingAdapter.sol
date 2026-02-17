// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

/**
 * @title StakingAdapter
 * @notice Simulates MON -> sMON staking with deterministic yield accrual.
 *         Accepts native MON deposits, tracks principal separately from rewards,
 *         and accrues rewards at ~8% APY based on block timestamps.
 *
 *         Only the linked GameManager contract may deduct or credit reward balances.
 *         Users may withdraw principal + unclaimed rewards at any time.
 */
contract StakingAdapter {
    // --- State ---
    mapping(address => uint256) public principal;
    mapping(address => uint256) public stakeTimestamp;
    mapping(address => uint256) public rewardBalance;

    address public owner;
    address public gameManager;

    // 8% APY expressed in basis points
    uint256 public constant APY_BPS = 800;
    uint256 private constant BPS_DENOMINATOR = 10_000;
    uint256 private constant SECONDS_PER_YEAR = 365 days;

    // Faucet: cooldown tracking per user
    mapping(address => uint256) public lastFaucetClaim;
    uint256 public constant FAUCET_COOLDOWN = 1 hours;
    uint256 public constant FAUCET_MIN = 5 ether;
    uint256 public constant FAUCET_MAX = 50 ether;

    // --- Events ---
    event Deposited(address indexed user, uint256 amount);
    event Withdrawn(address indexed user, uint256 principal, uint256 rewards);
    event RewardsDeducted(address indexed user, uint256 amount);
    event RewardsCredited(address indexed user, uint256 amount);
    event GameManagerSet(address indexed gameManager);
    event FaucetClaimed(address indexed user, uint256 amount);

    // --- Modifiers ---
    modifier onlyOwner() {
        require(msg.sender == owner, "Not owner");
        _;
    }

    modifier onlyGameManager() {
        require(msg.sender == gameManager, "Not game manager");
        _;
    }

    constructor() {
        owner = msg.sender;
    }

    // --- Owner Functions ---

    function setGameManager(address _gameManager) external onlyOwner {
        require(_gameManager != address(0), "Zero address");
        gameManager = _gameManager;
        emit GameManagerSet(_gameManager);
    }

    // --- User Functions ---

    /**
     * @notice Deposit native MON. Internally treated as sMON 1:1.
     *         Snapshots any pending rewards before updating principal.
     */
    function deposit() external payable {
        require(msg.value > 0, "Zero deposit");

        // Snapshot accrued rewards before changing principal
        if (principal[msg.sender] > 0) {
            rewardBalance[msg.sender] += _calculateAccrued(msg.sender);
        }

        principal[msg.sender] += msg.value;
        stakeTimestamp[msg.sender] = block.timestamp;

        emit Deposited(msg.sender, msg.value);
    }

    /**
     * @notice Withdraw all principal + unclaimed rewards as native MON.
     *         Resets the user's staking position entirely.
     */
    function withdraw() external {
        uint256 userPrincipal = principal[msg.sender];
        require(userPrincipal > 0, "No deposit");

        // Snapshot final rewards
        uint256 totalRewards = rewardBalance[msg.sender] + _calculateAccrued(msg.sender);
        uint256 totalPayout = userPrincipal + totalRewards;

        // Reset state before transfer (checks-effects-interactions)
        principal[msg.sender] = 0;
        stakeTimestamp[msg.sender] = 0;
        rewardBalance[msg.sender] = 0;

        require(address(this).balance >= totalPayout, "Insufficient contract balance");

        (bool success, ) = msg.sender.call{value: totalPayout}("");
        require(success, "Transfer failed");

        emit Withdrawn(msg.sender, userPrincipal, totalRewards);
    }

    // --- View Functions ---

    /**
     * @notice Returns rewards accrued since last snapshot (not yet stored).
     */
    function getAccruedRewards(address user) external view returns (uint256) {
        return _calculateAccrued(user);
    }

    /**
     * @notice Returns total available rewards (stored + accrued).
     *         This is the balance available for game buy-ins.
     */
    function getAvailableRewards(address user) external view returns (uint256) {
        return rewardBalance[user] + _calculateAccrued(user);
    }

    /**
     * @notice Returns the user's deposited principal (never used for game entries).
     */
    function getPrincipal(address user) external view returns (uint256) {
        return principal[user];
    }

    // --- GameManager Functions ---

    /**
     * @notice Deducts rewards from a user's balance for lobby buy-in.
     *         Called only by the GameManager contract.
     *         Snapshots accrued rewards first, then deducts.
     */
    function deductRewards(address user, uint256 amount) external onlyGameManager {
        // Snapshot accrued rewards
        rewardBalance[user] += _calculateAccrued(user);
        stakeTimestamp[user] = block.timestamp;

        require(rewardBalance[user] >= amount, "Insufficient rewards");
        rewardBalance[user] -= amount;

        emit RewardsDeducted(user, amount);
    }

    /**
     * @notice Credits rewards to a user's balance (game winnings).
     *         Called only by the GameManager contract.
     */
    function creditRewards(address user, uint256 amount) external onlyGameManager {
        rewardBalance[user] += amount;
        emit RewardsCredited(user, amount);
    }

    // --- Internal ---

    /**
     * @dev Calculates time-weighted rewards since last snapshot.
     *      Formula: principal * APY_BPS / BPS_DENOMINATOR * elapsed / SECONDS_PER_YEAR
     */
    function _calculateAccrued(address user) internal view returns (uint256) {
        if (principal[user] == 0 || stakeTimestamp[user] == 0) {
            return 0;
        }
        uint256 elapsed = block.timestamp - stakeTimestamp[user];
        // principal * 800 / 10000 * elapsed / 31536000
        return (principal[user] * APY_BPS * elapsed) / (BPS_DENOMINATOR * SECONDS_PER_YEAR);
    }

    // --- Faucet (Testnet Only) ---

    /**
     * @notice Claim a random amount of test MON from the contract.
     *         The contract must be pre-funded by the deployer.
     *         Each address has a 1-hour cooldown between claims.
     */
    function faucet() external {
        require(
            block.timestamp >= lastFaucetClaim[msg.sender] + FAUCET_COOLDOWN,
            "Faucet cooldown active"
        );

        // Pseudo-random amount between FAUCET_MIN and FAUCET_MAX
        uint256 randomSeed = uint256(
            keccak256(abi.encodePacked(block.timestamp, block.prevrandao, msg.sender))
        );
        uint256 amount = FAUCET_MIN + (randomSeed % (FAUCET_MAX - FAUCET_MIN));

        require(address(this).balance >= amount, "Faucet empty");

        lastFaucetClaim[msg.sender] = block.timestamp;

        (bool success, ) = msg.sender.call{value: amount}("");
        require(success, "Faucet transfer failed");

        emit FaucetClaimed(msg.sender, amount);
    }

    /**
     * @notice Returns seconds remaining until the user can claim the faucet again.
     */
    function faucetCooldownRemaining(address user) external view returns (uint256) {
        if (lastFaucetClaim[user] == 0) return 0;
        uint256 nextClaim = lastFaucetClaim[user] + FAUCET_COOLDOWN;
        if (block.timestamp >= nextClaim) return 0;
        return nextClaim - block.timestamp;
    }

    // Allow contract to receive MON for reward payouts and faucet funding
    receive() external payable {}
}
