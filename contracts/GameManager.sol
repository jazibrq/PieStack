// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

import "./StakingAdapter.sol";

/**
 * @title GameManager
 * @notice Manages game lobbies where players wager staking rewards.
 *         Each lobby is an independent struct — no shared mutable state between
 *         lobbies, enabling Monad's parallel EVM to process concurrent lobby
 *         operations without contention.
 *
 *         Buy-ins are deducted from staking rewards (never principal).
 *         Winners receive the full prize pool credited to their reward balance.
 */
contract GameManager {
    // --- Types ---
    struct Lobby {
        address host;
        uint256 buyIn;
        uint256 maxPlayers;
        address[] players;
        bool resolved;
        bool active;
        uint256 prizePool;
    }

    // --- State ---
    StakingAdapter public stakingAdapter;
    address public admin;

    mapping(uint256 => Lobby) public lobbies;
    uint256 public lobbyCount;

    // Track which lobbies a player is in (to prevent double-join)
    mapping(uint256 => mapping(address => bool)) public isPlayerInLobby;

    // --- Events ---
    event LobbyCreated(uint256 indexed lobbyId, address indexed host, uint256 buyIn, uint256 maxPlayers);
    event PlayerJoined(uint256 indexed lobbyId, address indexed player);
    event GameResolved(uint256 indexed lobbyId, address indexed winner, uint256 prizeAmount);
    event LobbyCancelled(uint256 indexed lobbyId);

    // --- Modifiers ---
    modifier onlyAdmin() {
        require(msg.sender == admin, "Not admin");
        _;
    }

    constructor(address _stakingAdapter) {
        require(_stakingAdapter != address(0), "Zero address");
        stakingAdapter = StakingAdapter(payable(_stakingAdapter));
        admin = msg.sender;
    }

    // --- Lobby Functions ---

    /**
     * @notice Create a new lobby. The host is auto-joined and their buy-in
     *         is deducted from staking rewards.
     * @param buyIn The reward amount each player must wager (in wei).
     * @param maxPlayers Maximum number of players (2-16).
     */
    function createLobby(uint256 buyIn, uint256 maxPlayers) external returns (uint256) {
        require(buyIn > 0, "Buy-in must be > 0");
        require(maxPlayers >= 2 && maxPlayers <= 16, "Invalid player count");

        uint256 lobbyId = lobbyCount++;

        Lobby storage lobby = lobbies[lobbyId];
        lobby.host = msg.sender;
        lobby.buyIn = buyIn;
        lobby.maxPlayers = maxPlayers;
        lobby.active = true;

        // Auto-join host: deduct buy-in from their rewards
        stakingAdapter.deductRewards(msg.sender, buyIn);
        lobby.players.push(msg.sender);
        lobby.prizePool += buyIn;
        isPlayerInLobby[lobbyId][msg.sender] = true;

        emit LobbyCreated(lobbyId, msg.sender, buyIn, maxPlayers);
        emit PlayerJoined(lobbyId, msg.sender);

        return lobbyId;
    }

    /**
     * @notice Join an existing lobby. Buy-in is deducted from staking rewards.
     * @param lobbyId The lobby to join.
     */
    function joinLobby(uint256 lobbyId) external {
        Lobby storage lobby = lobbies[lobbyId];

        require(lobby.active, "Lobby not active");
        require(!lobby.resolved, "Lobby already resolved");
        require(lobby.players.length < lobby.maxPlayers, "Lobby full");
        require(!isPlayerInLobby[lobbyId][msg.sender], "Already in lobby");

        // Deduct buy-in from rewards
        stakingAdapter.deductRewards(msg.sender, lobby.buyIn);

        lobby.players.push(msg.sender);
        lobby.prizePool += lobby.buyIn;
        isPlayerInLobby[lobbyId][msg.sender] = true;

        emit PlayerJoined(lobbyId, msg.sender);
    }

    /**
     * @notice Resolve a game. Admin/oracle submits the winner who receives
     *         the full prize pool credited to their reward balance.
     * @param lobbyId The lobby to resolve.
     * @param winner The address of the winning player.
     */
    function resolveGame(uint256 lobbyId, address winner) external onlyAdmin {
        Lobby storage lobby = lobbies[lobbyId];

        require(lobby.active, "Lobby not active");
        require(!lobby.resolved, "Already resolved");
        require(isPlayerInLobby[lobbyId][winner], "Winner not in lobby");

        lobby.resolved = true;
        lobby.active = false;

        // Credit full prize pool to winner's reward balance
        stakingAdapter.creditRewards(winner, lobby.prizePool);

        emit GameResolved(lobbyId, winner, lobby.prizePool);
    }

    /**
     * @notice Cancel a lobby and refund all players' buy-ins.
     *         Only the host or admin can cancel.
     */
    function cancelLobby(uint256 lobbyId) external {
        Lobby storage lobby = lobbies[lobbyId];

        require(lobby.active, "Lobby not active");
        require(!lobby.resolved, "Already resolved");
        require(msg.sender == lobby.host || msg.sender == admin, "Not authorized");

        lobby.active = false;

        // Refund all players
        for (uint256 i = 0; i < lobby.players.length; i++) {
            stakingAdapter.creditRewards(lobby.players[i], lobby.buyIn);
        }

        emit LobbyCancelled(lobbyId);
    }

    // --- View Functions ---

    /**
     * @notice Get full details of a lobby.
     */
    function getLobby(uint256 lobbyId) external view returns (
        address host,
        uint256 buyIn,
        uint256 maxPlayers,
        address[] memory players,
        bool resolved,
        bool active,
        uint256 prizePool
    ) {
        Lobby storage lobby = lobbies[lobbyId];
        return (
            lobby.host,
            lobby.buyIn,
            lobby.maxPlayers,
            lobby.players,
            lobby.resolved,
            lobby.active,
            lobby.prizePool
        );
    }

    /**
     * @notice Get the number of players in a lobby.
     */
    function getLobbyPlayerCount(uint256 lobbyId) external view returns (uint256) {
        return lobbies[lobbyId].players.length;
    }

    /**
     * @notice Get total number of lobbies created.
     */
    function getLobbyCount() external view returns (uint256) {
        return lobbyCount;
    }
}
