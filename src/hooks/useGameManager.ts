import { useState, useCallback, useEffect } from 'react';
import { ethers } from 'ethers';
import { useWallet } from '@/contexts/WalletContext';
import { CONTRACT_ADDRESSES, GAME_MANAGER_ABI } from '@/config/contracts';

export interface LobbyData {
  id: number;
  host: string;
  buyIn: string; // in ether units
  maxPlayers: number;
  players: string[];
  resolved: boolean;
  active: boolean;
  prizePool: string; // in ether units
}

export function useGameManager() {
  const { signer, provider, address, isConnected } = useWallet();
  const [lobbies, setLobbies] = useState<LobbyData[]>([]);
  const [loading, setLoading] = useState(false);

  const getContract = useCallback((useSigner = false) => {
    const connection = useSigner ? signer : provider;
    if (!connection) return null;
    return new ethers.Contract(
      CONTRACT_ADDRESSES.gameManager,
      GAME_MANAGER_ABI,
      connection
    );
  }, [signer, provider]);

  const fetchLobbies = useCallback(async () => {
    const contract = getContract();
    if (!contract) return;

    try {
      const count = await contract.getLobbyCount();
      const lobbyCount = Number(count);

      const lobbyPromises = [];
      for (let i = 0; i < lobbyCount; i++) {
        lobbyPromises.push(contract.getLobby(i));
      }

      const results = await Promise.all(lobbyPromises);
      const parsedLobbies: LobbyData[] = results.map((result, index) => ({
        id: index,
        host: result.host,
        buyIn: ethers.formatEther(result.buyIn),
        maxPlayers: Number(result.maxPlayers),
        players: [...result.players],
        resolved: result.resolved,
        active: result.active,
        prizePool: ethers.formatEther(result.prizePool),
      }));

      setLobbies(parsedLobbies);
    } catch (error) {
      console.error('Failed to fetch lobbies:', error);
    }
  }, [getContract]);

  useEffect(() => {
    fetchLobbies();
    if (!provider) return;
    const interval = setInterval(fetchLobbies, 10000);
    return () => clearInterval(interval);
  }, [fetchLobbies, provider]);

  const createLobby = useCallback(async (buyInEther: string, maxPlayers: number) => {
    const contract = getContract(true);
    if (!contract) throw new Error('Wallet not connected');

    setLoading(true);
    try {
      const tx = await contract.createLobby(
        ethers.parseEther(buyInEther),
        maxPlayers
      );
      const receipt = await tx.wait();

      // Parse LobbyCreated event to get lobby ID
      const event = receipt.logs
        .map((log: ethers.Log) => {
          try { return contract.interface.parseLog({ topics: [...log.topics], data: log.data }); }
          catch { return null; }
        })
        .find((e: ethers.LogDescription | null) => e?.name === 'LobbyCreated');

      await fetchLobbies();
      return event ? Number(event.args.lobbyId) : undefined;
    } finally {
      setLoading(false);
    }
  }, [getContract, fetchLobbies]);

  const joinLobby = useCallback(async (lobbyId: number) => {
    const contract = getContract(true);
    if (!contract) throw new Error('Wallet not connected');

    setLoading(true);
    try {
      const tx = await contract.joinLobby(lobbyId);
      await tx.wait();
      await fetchLobbies();
    } finally {
      setLoading(false);
    }
  }, [getContract, fetchLobbies]);

  const cancelLobby = useCallback(async (lobbyId: number) => {
    const contract = getContract(true);
    if (!contract) throw new Error('Wallet not connected');

    setLoading(true);
    try {
      const tx = await contract.cancelLobby(lobbyId);
      await tx.wait();
      await fetchLobbies();
    } finally {
      setLoading(false);
    }
  }, [getContract, fetchLobbies]);

  const isPlayerInLobby = useCallback((lobby: LobbyData) => {
    if (!address) return false;
    return lobby.players.some(p => p.toLowerCase() === address.toLowerCase());
  }, [address]);

  return {
    lobbies,
    activeLobbies: lobbies.filter(l => l.active && !l.resolved),
    loading,
    createLobby,
    joinLobby,
    cancelLobby,
    isPlayerInLobby,
    refreshLobbies: fetchLobbies,
  };
}
