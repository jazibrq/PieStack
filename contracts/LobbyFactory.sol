// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

import "./Match.sol";

/**
 * @title LobbyFactory
 * @notice Factory that deploys independent Match contracts and keeps
 *         a lightweight registry for frontend querying.
 *
 *         Each match is its own contract — this factory only stores
 *         addresses so the frontend can discover them.  No mutable
 *         game state lives here; everything is inside the Match
 *         contracts, enabling Monad parallelism.
 */
contract LobbyFactory {
    // ─── State ─────────────────────────────────────────
    address public owner;
    address[] public allMatches;
    mapping(address => bool) public isMatch;

    // ─── Events ────────────────────────────────────────
    event MatchCreated(
        address indexed matchAddr,
        address indexed creator,
        uint8   maxPlayers,
        uint256 entryFee
    );
    event MatchStatusChanged(
        address indexed matchAddr,
        uint8   status
    );

    // ─── Constructor ───────────────────────────────────
    constructor() {
        owner = msg.sender;
    }

    // ─── Create Match ──────────────────────────────────
    /**
     * @notice Deploy a brand-new Match contract and auto-join the
     *         caller as the first player.
     * @param _maxPlayers  Allowed: 2, 4, 8, 16
     * @param _entryFee    Entry fee in MON (wei).  msg.value must equal.
     * @return matchAddr   Address of the newly deployed Match contract.
     */
    function createMatch(
        uint8   _maxPlayers,
        uint256 _entryFee
    ) external payable returns (address matchAddr) {
        require(msg.value == _entryFee, "msg.value must equal entryFee");
        require(_entryFee > 0, "Entry fee must be > 0");

        // Deploy independent contract
        Match m = new Match(msg.sender, _maxPlayers, _entryFee);
        matchAddr = address(m);

        // Register
        allMatches.push(matchAddr);
        isMatch[matchAddr] = true;

        // Forward the creator's entry fee — joinFor() registers the
        // actual user (msg.sender of this tx) as the player, not the factory.
        Match(payable(matchAddr)).joinFor{value: msg.value}(msg.sender);

        emit MatchCreated(matchAddr, msg.sender, _maxPlayers, _entryFee);
        return matchAddr;
    }

    // ─── Submit Results (Oracle) ───────────────────────
    /**
     * @notice Submit results for a match. Only factory owner (oracle).
     *         This is the trusted backend channel.
     */
    function submitResults(
        address matchAddr,
        address[] calldata _players,
        uint256[] calldata _scores
    ) external {
        require(msg.sender == owner, "Not owner");
        require(isMatch[matchAddr], "Unknown match");

        Match(payable(matchAddr)).submitResults(_players, _scores);
        emit MatchStatusChanged(matchAddr, uint8(Match(payable(matchAddr)).status()));
    }

    // ─── Cancel Match ──────────────────────────────────
    /**
     * @notice Factory can cancel any match (admin override).
     */
    function cancelMatch(address matchAddr) external {
        require(msg.sender == owner, "Not owner");
        require(isMatch[matchAddr], "Unknown match");

        Match(payable(matchAddr)).cancel();
        emit MatchStatusChanged(matchAddr, uint8(Match(payable(matchAddr)).status()));
    }

    // ─── Read Helpers ──────────────────────────────────

    /**
     * @notice Returns addresses of all matches that are still Open.
     */
    function getOpenMatches() external view returns (address[] memory) {
        uint256 total = allMatches.length;
        // First pass: count open
        uint256 count = 0;
        for (uint256 i = 0; i < total; i++) {
            if (Match(payable(allMatches[i])).status() == Match.Status.Open) {
                count++;
            }
        }
        // Second pass: fill array
        address[] memory open = new address[](count);
        uint256 idx = 0;
        for (uint256 i = 0; i < total; i++) {
            if (Match(payable(allMatches[i])).status() == Match.Status.Open) {
                open[idx] = allMatches[i];
                idx++;
            }
        }
        return open;
    }

    /**
     * @notice Get info for a specific match.
     */
    function getMatchInfo(address matchAddr) external view returns (
        address _creator,
        uint8   _maxPlayers,
        uint256 _entryFee,
        uint8   _status,
        uint256 _playerCount,
        uint256 _prizePool
    ) {
        require(isMatch[matchAddr], "Unknown match");
        return Match(payable(matchAddr)).getInfo();
    }

    /**
     * @notice Total number of matches ever created.
     */
    function matchCount() external view returns (uint256) {
        return allMatches.length;
    }

    /**
     * @notice Retrieve a page of all match addresses.
     */
    function getMatches(uint256 offset, uint256 limit)
        external view returns (address[] memory)
    {
        uint256 total = allMatches.length;
        if (offset >= total) {
            return new address[](0);
        }
        uint256 end = offset + limit;
        if (end > total) end = total;
        address[] memory result = new address[](end - offset);
        for (uint256 i = offset; i < end; i++) {
            result[i - offset] = allMatches[i];
        }
        return result;
    }
}
