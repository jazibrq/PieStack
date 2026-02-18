// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

/**
 * @title Match
 * @notice A single, independently-deployed match contract.
 *         Each match is its own contract — no shared mutable state across
 *         matches, enabling Monad's parallel EVM to process concurrent
 *         matches without contention.
 *
 *         Players join by sending the exact entry fee as native MON.
 *         Once all slots are filled the match is InProgress.
 *         The factory (admin) submits final scores; prize pool is
 *         distributed based on placement.
 *
 *         Prize distribution:
 *           2  players → 1st: 100%
 *           4  players → 1st: 60%, 2nd: 40%
 *           8  players → 1st: 50%, 2nd: 30%, 3rd: 20%
 *           16 players → 1st: 40%, 2nd: 25%, 3rd: 20%, 4th: 15%
 */
contract Match {
    // ─── Types ─────────────────────────────────────────
    enum Status { Open, InProgress, Completed, Cancelled }

    // ─── Immutables & Config ───────────────────────────
    address public immutable factory;
    address public immutable creator;
    uint8   public immutable maxPlayers;
    uint256 public immutable entryFee;

    // ─── State ─────────────────────────────────────────
    Status  public status;
    address[] public players;
    mapping(address => bool) public enrolled;
    mapping(address => uint256) public scores;
    mapping(address => uint256) public payout;

    // ─── Events ────────────────────────────────────────
    event PlayerJoined(address indexed player);
    event MatchStarted();
    event MatchCompleted(address[] ranked, uint256[] payouts);
    event MatchCancelled();
    event Withdrawn(address indexed player, uint256 amount);

    // ─── Modifiers ─────────────────────────────────────
    modifier onlyFactory() {
        require(msg.sender == factory, "Not factory");
        _;
    }

    modifier onlyCreator() {
        require(msg.sender == creator, "Not creator");
        _;
    }

    // ─── Constructor ───────────────────────────────────
    constructor(
        address _creator,
        uint8   _maxPlayers,
        uint256 _entryFee
    ) {
        require(_creator != address(0), "Zero creator");
        require(
            _maxPlayers == 2 || _maxPlayers == 4 ||
            _maxPlayers == 8 || _maxPlayers == 16,
            "Invalid maxPlayers"
        );
        require(_entryFee > 0, "Entry fee must be > 0");

        factory    = msg.sender;
        creator    = _creator;
        maxPlayers = _maxPlayers;
        entryFee   = _entryFee;
        status     = Status.Open;
    }

    // ─── Join ──────────────────────────────────────────
    /**
     * @notice Join this match by sending exactly `entryFee` MON.
     */
    function join() external payable {
        _join(msg.sender, msg.value);
    }

    /**
     * @notice Factory-only: join on behalf of a player (for createMatch auto-join).
     */
    function joinFor(address _player) external payable onlyFactory {
        _join(_player, msg.value);
    }

    function _join(address _player, uint256 _value) internal {
        require(status == Status.Open, "Not open");
        require(!enrolled[_player], "Already joined");
        require(players.length < maxPlayers, "Match full");
        require(_value == entryFee, "Wrong entry fee");

        enrolled[_player] = true;
        players.push(_player);
        emit PlayerJoined(_player);

        // Auto-start when full
        if (players.length == maxPlayers) {
            status = Status.InProgress;
            emit MatchStarted();
        }
    }

    // ─── Submit Results ────────────────────────────────
    /**
     * @notice Submit final scores and distribute prize pool.
     *         Only callable by the factory (trusted backend / oracle).
     * @param _players Ordered list of players (must match enrolled list, any order).
     * @param _scores  Score for each player (same index as _players).
     */
    function submitResults(
        address[] calldata _players,
        uint256[] calldata _scores
    ) external onlyFactory {
        require(status == Status.InProgress, "Not in progress");
        require(_players.length == players.length, "Player count mismatch");
        require(_scores.length == _players.length, "Score count mismatch");

        // Record scores
        for (uint256 i = 0; i < _players.length; i++) {
            require(enrolled[_players[i]], "Unknown player");
            scores[_players[i]] = _scores[i];
        }

        // Sort players by score descending (simple in-memory sort; max 16 elements)
        address[] memory ranked = new address[](_players.length);
        for (uint256 i = 0; i < _players.length; i++) {
            ranked[i] = _players[i];
        }
        for (uint256 i = 0; i < ranked.length; i++) {
            for (uint256 j = i + 1; j < ranked.length; j++) {
                if (scores[ranked[j]] > scores[ranked[i]]) {
                    (ranked[i], ranked[j]) = (ranked[j], ranked[i]);
                }
            }
        }

        // Compute payouts based on lobby size
        uint256 pool = address(this).balance;
        uint256[] memory payouts = _computePayouts(pool, maxPlayers, uint8(ranked.length));

        for (uint256 i = 0; i < ranked.length; i++) {
            if (i < payouts.length && payouts[i] > 0) {
                payout[ranked[i]] = payouts[i];
            }
        }

        status = Status.Completed;
        emit MatchCompleted(ranked, payouts);

        // Auto-send payouts
        for (uint256 i = 0; i < ranked.length; i++) {
            uint256 amt = payout[ranked[i]];
            if (amt > 0) {
                payout[ranked[i]] = 0;
                (bool ok, ) = ranked[i].call{value: amt}("");
                require(ok, "Transfer failed");
                emit Withdrawn(ranked[i], amt);
            }
        }
    }

    // ─── Cancel ────────────────────────────────────────
    /**
     * @notice Cancel the match. Refunds all players.
     *         Only the creator (before InProgress) or factory can cancel.
     */
    function cancel() external {
        require(
            msg.sender == creator || msg.sender == factory,
            "Not authorized"
        );
        require(
            status == Status.Open || status == Status.InProgress,
            "Cannot cancel"
        );

        status = Status.Cancelled;
        emit MatchCancelled();

        // Refund all players
        for (uint256 i = 0; i < players.length; i++) {
            address p = players[i];
            if (enrolled[p]) {
                enrolled[p] = false;
                (bool ok, ) = p.call{value: entryFee}("");
                require(ok, "Refund failed");
                emit Withdrawn(p, entryFee);
            }
        }
    }

    // ─── Views ─────────────────────────────────────────

    function getPlayers() external view returns (address[] memory) {
        return players;
    }

    function playerCount() external view returns (uint256) {
        return players.length;
    }

    function prizePool() external view returns (uint256) {
        return address(this).balance;
    }

    function getInfo() external view returns (
        address  _creator,
        uint8    _maxPlayers,
        uint256  _entryFee,
        uint8    _status,
        uint256  _playerCount,
        uint256  _prizePool
    ) {
        return (
            creator,
            maxPlayers,
            entryFee,
            uint8(status),
            players.length,
            address(this).balance
        );
    }

    // ─── Internal ──────────────────────────────────────

    /**
     * @dev Compute prize distribution array based on lobby size.
     *      Returns an array of payout amounts summing to `pool`.
     *        2  → [100%]
     *        4  → [60%, 40%]
     *        8  → [50%, 30%, 20%]
     *        16 → [40%, 25%, 20%, 15%]
     */
    function _computePayouts(
        uint256 pool,
        uint8 _maxPlayers,
        uint8 _actualPlayers
    ) internal pure returns (uint256[] memory) {
        uint256[] memory result;

        if (_maxPlayers == 2) {
            result = new uint256[](1);
            result[0] = pool;
        } else if (_maxPlayers == 4) {
            result = new uint256[](2);
            result[0] = (pool * 60) / 100;
            result[1] = pool - result[0]; // remainder to avoid dust
        } else if (_maxPlayers == 8) {
            result = new uint256[](3);
            result[0] = (pool * 50) / 100;
            result[1] = (pool * 30) / 100;
            result[2] = pool - result[0] - result[1];
        } else {
            // 16 players
            result = new uint256[](4);
            result[0] = (pool * 40) / 100;
            result[1] = (pool * 25) / 100;
            result[2] = (pool * 20) / 100;
            result[3] = pool - result[0] - result[1] - result[2];
        }

        // If fewer actual players than payout slots, truncate
        if (_actualPlayers < result.length) {
            uint256[] memory trimmed = new uint256[](_actualPlayers);
            uint256 dist = 0;
            for (uint256 i = 0; i < _actualPlayers; i++) {
                trimmed[i] = result[i];
                dist += result[i];
            }
            // Give remainder to 1st place
            if (pool > dist) {
                trimmed[0] += pool - dist;
            }
            return trimmed;
        }

        return result;
    }

    // Accept MON sent directly (factory or otherwise)
    receive() external payable {}
}
