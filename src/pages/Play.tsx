import { useState, useCallback, useMemo } from 'react';
import { Navigation } from '@/components/Navigation';
import { VideoBackground } from '@/components/VideoBackground';
import { GrainOverlay } from '@/components/GrainOverlay';
import { Button } from '@/components/ui/button';
import { EmptyState } from '@/components/ui/shared';
import { HostLobbyModal } from '@/components/modals/HostLobbyModal';
import { MatchOverlay } from '@/components/modals/MatchOverlay';
import { PartnersBanner } from '@/components/home/PartnersBanner';
import { Footer } from '@/components/layout/Footer';
import { Leaderboard } from '@/components/home/Leaderboard';
import { BulletHellGame } from '@/components/game/BulletHellGame';
import {
  Plus, Users, Filter, Search,
  ChevronDown, Swords, Clock, Gamepad2
} from 'lucide-react';
import { cn } from '@/lib/utils';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu';
import { Input } from '@/components/ui/input';
import { useWallet } from '@/contexts/WalletContext';
import { useGameManager, LobbyData } from '@/hooks/useGameManager';
import { useStaking } from '@/hooks/useStaking';

const lobbySizes = [2, 4, 8, 16];
const sortOptions = ['Most Recent', 'Highest Stake'];

function truncateAddress(addr: string): string {
  return `${addr.slice(0, 6)}...${addr.slice(-4)}`;
}

const Play = () => {
  const [hostModalOpen, setHostModalOpen] = useState(false);
  const [matchOverlayOpen, setMatchOverlayOpen] = useState(false);
  const [selectedLobby, setSelectedLobby] = useState<LobbyData | null>(null);
  const [sizeFilter, setSizeFilter] = useState<number | null>(null);
  const [searchQuery, setSearchQuery] = useState('');
  const [sortBy, setSortBy] = useState('Most Recent');
  const [activeSection, setActiveSection] = useState<'play' | 'leaderboard'>('play');

  // Game state
  const [gamePlaying, setGamePlaying] = useState(false);
  const [lastGameResult, setLastGameResult] = useState<{ score: number; stage: number; kills: number } | null>(null);

  const { isConnected, connect } = useWallet();
  const { activeLobbies, joinLobby, loading: gameLoading } = useGameManager();
  const { availableRewards } = useStaking();

  // Generate 5 simulated lobbies for demo
  const fakeLobbies = useMemo<(LobbyData & { isFake?: boolean })[]>(() => {
    const hosts = [
      '0x742d35Cc6634C0532925a3b844Bc9e7595f2bD38',
      '0x8Ba1f109551bD432803012645Ac136ddd64DBA72',
      '0xdD2FD4581271e230360230F9337D5c0430Bf44C0',
      '0x2546BcD3c84621e976D8185a91A922aE77ECEc30',
      '0xbDA5747bFD65F08deb54cb465eB87D40e51B197E',
    ];
    const buyIns = ['0.05', '0.1', '0.25', '0.01', '0.5'];
    const maxPlayersList = [4, 2, 8, 4, 2];
    const playerCounts = [2, 1, 5, 3, 1];
    const fakeAddresses = [
      '0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48',
      '0x6B175474E89094C44Da98b954EedeAC495271d0F',
      '0xdAC17F958D2ee523a2206206994597C13D831ec7',
      '0x1f9840a85d5aF5bf1D1762F925BDADdC4201F984',
      '0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2',
    ];

    return hosts.map((host, i) => ({
      id: 10001 + i,
      host,
      buyIn: buyIns[i],
      maxPlayers: maxPlayersList[i],
      players: fakeAddresses.slice(0, playerCounts[i]),
      resolved: false,
      active: true,
      prizePool: (parseFloat(buyIns[i]) * playerCounts[i]).toFixed(4),
      isFake: true,
    }));
  }, []);

  const handleStartQuickPlay = useCallback(() => {
    setLastGameResult(null);
    setGamePlaying(true);
  }, []);

  const handleGameOver = useCallback((score: number, stage: number, kills: number) => {
    setLastGameResult({ score, stage, kills });
    setGamePlaying(false);
  }, []);

  const handleGameExit = useCallback(() => {
    setGamePlaying(false);
  }, []);

  const handleJoinLobby = async (lobby: LobbyData & { isFake?: boolean }) => {
    // Fake lobby — just start the game directly
    if (lobby.isFake) {
      setLastGameResult(null);
      setGamePlaying(true);
      return;
    }

    if (!isConnected) {
      connect();
      return;
    }

    const rewardsNum = parseFloat(availableRewards);
    const buyInNum = parseFloat(lobby.buyIn);

    if (rewardsNum < buyInNum) {
      alert(`Insufficient rewards. You need ${lobby.buyIn} MON in rewards but have ${rewardsNum.toFixed(6)} MON.`);
      return;
    }

    try {
      await joinLobby(lobby.id);
      setSelectedLobby(lobby);
      setMatchOverlayOpen(true);
    } catch (error: unknown) {
      const err = error as { reason?: string; message?: string };
      alert(`Failed to join lobby: ${err.reason || err.message || 'Unknown error'}`);
    }
  };

  const allLobbies: (LobbyData & { isFake?: boolean })[] = [...fakeLobbies, ...activeLobbies];
  const filteredLobbies = allLobbies
    .filter((lobby) => {
      if (sizeFilter && lobby.maxPlayers !== sizeFilter) return false;
      if (searchQuery && !lobby.host.toLowerCase().includes(searchQuery.toLowerCase())) return false;
      return true;
    })
    .sort((a, b) => {
      if (sortBy === 'Highest Stake') {
        return parseFloat(b.buyIn) - parseFloat(a.buyIn);
      }
      return b.id - a.id; // Most Recent (higher ID = newer)
    });

  return (
    <div className="min-h-screen">
      {/* Full-screen game overlay */}
      {gamePlaying && (
        <BulletHellGame onGameOver={handleGameOver} onExit={handleGameExit} />
      )}

      <VideoBackground />
      <GrainOverlay />
      <Navigation />

      <main className="relative z-10 pt-24 pb-12">
        <div className="container mx-auto max-w-6xl px-4">
          {/* Last Game Result Banner */}
          {lastGameResult && (
            <div className="card-surface p-4 mb-6 border border-primary/30 bg-primary/5">
              <div className="flex flex-col sm:flex-row items-center justify-between gap-3">
                <div className="flex items-center gap-4">
                  <Gamepad2 className="w-6 h-6 text-primary" />
                  <div>
                    <p className="text-sm font-semibold">Last Game Result</p>
                    <p className="text-xs text-muted-foreground font-mono">
                      Score: <span className="text-primary">{lastGameResult.score.toLocaleString()}</span>
                      {' '}&bull;{' '}
                      Stage: <span className="text-amber-400">{lastGameResult.stage}</span>
                      {' '}&bull;{' '}
                      Kills: <span className="text-emerald-400">{lastGameResult.kills}</span>
                    </p>
                  </div>
                </div>
                <Button
                  size="sm"
                  onClick={handleStartQuickPlay}
                  className="btn-cyan-gradient gap-2"
                >
                  <Gamepad2 className="w-4 h-4" />
                  Play Again
                </Button>
              </div>
            </div>
          )}

          {/* Header */}
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 mb-6">
            <div>
              <h1 className="text-3xl font-bold mb-2">Play</h1>
              <p className="text-muted-foreground">Join a lobby or host your own match</p>
              {isConnected && (
                <p className="text-xs text-primary mt-1 font-mono">
                  Available rewards: {parseFloat(availableRewards).toFixed(6)} MON
                </p>
              )}
            </div>
            <div className="flex gap-2">
              <Button
                onClick={handleStartQuickPlay}
                className="btn-cyan-gradient gap-2"
              >
                <Gamepad2 className="w-4 h-4" />
                Quick Play
              </Button>
              <Button
                onClick={() => {
                  if (!isConnected) { connect(); return; }
                  setHostModalOpen(true);
                }}
                variant="outline"
                className="gap-2"
              >
                <Plus className="w-4 h-4" />
                Host Lobby
              </Button>
            </div>
          </div>

          {/* Section Toggle */}
          <div className="flex items-center gap-2 mb-8">
            <Button
              variant={activeSection === 'play' ? 'default' : 'outline'}
              onClick={() => setActiveSection('play')}
              className={cn(
                'gap-2',
                activeSection === 'play' ? 'btn-cyan-gradient px-6 py-3 text-base' : 'px-5 py-2.5'
              )}
            >
              Play
            </Button>
            <Button
              variant={activeSection === 'leaderboard' ? 'default' : 'outline'}
              onClick={() => setActiveSection('leaderboard')}
              className={cn(
                'gap-2',
                activeSection === 'leaderboard' ? 'btn-cyan-gradient px-6 py-3 text-base' : 'px-5 py-2.5'
              )}
            >
              Leaderboard
            </Button>
          </div>

          {activeSection === 'play' ? (
            <>
              {/* Filters */}
              <div className="card-surface p-4 mb-6">
                <div className="flex flex-col lg:flex-row gap-4">
                  {/* Search */}
                  <div className="relative flex-1 max-w-xs">
                    <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-muted-foreground" />
                    <Input
                      placeholder="Search by host address..."
                      value={searchQuery}
                      onChange={(e) => setSearchQuery(e.target.value)}
                      className="pl-10"
                    />
                  </div>

                  {/* Size Filter */}
                  <div className="flex items-center gap-2">
                    <span className="text-sm text-muted-foreground whitespace-nowrap">Lobby Size:</span>
                    <div className="flex gap-1 bg-surface-2 p-1 rounded-lg">
                      <button
                        onClick={() => setSizeFilter(null)}
                        className={cn(
                          'px-3 py-1.5 text-xs font-medium rounded transition-all',
                          sizeFilter === null
                            ? 'bg-primary text-primary-foreground'
                            : 'text-muted-foreground hover:text-foreground'
                        )}
                      >
                        All
                      </button>
                      {lobbySizes.map((size) => (
                        <button
                          key={size}
                          onClick={() => setSizeFilter(size)}
                          className={cn(
                            'px-3 py-1.5 text-xs font-medium rounded transition-all',
                            sizeFilter === size
                              ? 'bg-primary text-primary-foreground'
                              : 'text-muted-foreground hover:text-foreground'
                          )}
                        >
                          {size}
                        </button>
                      ))}
                    </div>
                  </div>

                  {/* Sort */}
                  <div className="flex items-center gap-2 lg:ml-auto">
                    <Filter className="w-4 h-4 text-muted-foreground" />
                    <DropdownMenu>
                      <DropdownMenuTrigger asChild>
                        <Button variant="outline" size="sm" className="gap-2">
                          {sortBy}
                          <ChevronDown className="w-3 h-3" />
                        </Button>
                      </DropdownMenuTrigger>
                      <DropdownMenuContent>
                        {sortOptions.map((option) => (
                          <DropdownMenuItem
                            key={option}
                            onClick={() => setSortBy(option)}
                          >
                            {option}
                          </DropdownMenuItem>
                        ))}
                      </DropdownMenuContent>
                    </DropdownMenu>
                  </div>
                </div>
              </div>

              {/* Lobby List */}
              {filteredLobbies.length === 0 ? (
                <EmptyState
                  icon={<Swords className="w-8 h-8" />}
                  title="No lobbies found"
                  description="Try adjusting your filters or host your own lobby to get started."
                  action={
                    <Button
                      onClick={() => {
                        if (!isConnected) { connect(); return; }
                        setHostModalOpen(true);
                      }}
                      className="btn-cyan-gradient"
                    >
                      Host Lobby
                    </Button>
                  }
                />
              ) : (
                <div className="card-surface overflow-hidden">
                  {/* Desktop Table */}
                  <div className="hidden md:block overflow-x-auto">
                    <table className="w-full">
                      <thead>
                        <tr className="border-b border-border">
                          <th className="px-4 py-3 text-left text-xs font-medium text-muted-foreground uppercase">Host</th>
                          <th className="px-4 py-3 text-left text-xs font-medium text-muted-foreground uppercase">Buy-in</th>
                          <th className="px-4 py-3 text-left text-xs font-medium text-muted-foreground uppercase">Size</th>
                          <th className="px-4 py-3 text-left text-xs font-medium text-muted-foreground uppercase">Prize Pool</th>
                          <th className="px-4 py-3 text-left text-xs font-medium text-muted-foreground uppercase">Status</th>
                          <th className="px-4 py-3 text-right text-xs font-medium text-muted-foreground uppercase">Action</th>
                        </tr>
                      </thead>
                      <tbody>
                        {filteredLobbies.map((lobby, index) => (
                          <tr
                            key={lobby.id}
                            className="lobby-row-hover border-b border-border last:border-0 group cursor-pointer"
                            style={{ animationDelay: `${index * 50}ms` }}
                          >
                            <td className="px-4 py-4">
                              <div className="flex items-center gap-2">
                                <div className="w-6 h-6 rounded-full bg-gradient-to-br from-primary/50 to-accent/50 transition-transform duration-200 group-hover:scale-110" />
                                <span className="font-mono text-sm">{truncateAddress(lobby.host)}</span>
                              </div>
                            </td>
                            <td className="px-4 py-4">
                              <span className="font-mono text-sm text-primary transition-all duration-200 group-hover:text-shadow-glow">{lobby.buyIn} MON</span>
                            </td>
                            <td className="px-4 py-4">
                              <div className="flex items-center gap-1">
                                <Users className="w-3 h-3 text-muted-foreground" />
                                <span className="text-sm">{lobby.players.length}/{lobby.maxPlayers}</span>
                              </div>
                            </td>
                            <td className="px-4 py-4">
                              <span className="font-mono text-sm text-amber-400">{lobby.prizePool} MON</span>
                            </td>
                            <td className="px-4 py-4">
                              <span className={cn(
                                'inline-flex items-center gap-1 text-xs font-medium',
                                lobby.players.length < lobby.maxPlayers ? 'text-emerald-400' : 'text-amber-400'
                              )}>
                                {lobby.players.length < lobby.maxPlayers ? (
                                  'Open'
                                ) : (
                                  <><Clock className="w-3 h-3" /> Full</>
                                )}
                              </span>
                            </td>
                            <td className="px-4 py-4 text-right">
                              <Button
                                size="sm"
                                onClick={() => handleJoinLobby(lobby)}
                                disabled={gameLoading || lobby.players.length >= lobby.maxPlayers}
                                className="btn-cyan-gradient opacity-70 group-hover:opacity-100 transition-opacity duration-200"
                              >
                                {gameLoading ? 'Joining...' : (lobby.isFake ? 'Play' : 'Join')}
                              </Button>
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>

                  {/* Mobile Cards */}
                  <div className="md:hidden divide-y divide-border">
                    {filteredLobbies.map((lobby, index) => (
                      <div
                        key={lobby.id}
                        className="p-4 lobby-row-hover group"
                        style={{ animationDelay: `${index * 50}ms` }}
                      >
                        <div className="flex items-start justify-between mb-3">
                          <div className="flex items-center gap-2">
                            <div className="w-8 h-8 rounded-full bg-gradient-to-br from-primary/50 to-accent/50" />
                            <div>
                              <p className="font-mono text-sm">{truncateAddress(lobby.host)}</p>
                              <p className="text-xs text-muted-foreground">{lobby.players.length}/{lobby.maxPlayers} players</p>
                            </div>
                          </div>
                          <span className={cn(
                            'text-xs font-medium px-2 py-0.5 rounded',
                            lobby.players.length < lobby.maxPlayers
                              ? 'bg-emerald-500/10 text-emerald-400'
                              : 'bg-amber-500/10 text-amber-400'
                          )}>
                            {lobby.players.length < lobby.maxPlayers ? 'Open' : 'Full'}
                          </span>
                        </div>
                        <div className="flex items-center justify-between">
                          <div className="flex items-center gap-4 text-sm">
                            <span className="font-mono text-primary">{lobby.buyIn} MON</span>
                            <span className="font-mono text-xs text-amber-400">
                              Pool: {lobby.prizePool} MON
                            </span>
                          </div>
                          <Button
                            size="sm"
                            onClick={() => handleJoinLobby(lobby)}
                            disabled={gameLoading || lobby.players.length >= lobby.maxPlayers}
                            className="btn-cyan-gradient"
                          >
                            {lobby.isFake ? 'Play' : 'Join'}
                          </Button>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </>
          ) : (
            <div className="mt-4">
              <Leaderboard />
            </div>
          )}
        </div>
      </main>

      {/* Partners Banner */}
      <PartnersBanner className="mt-[520px] relative z-10" />

      {/* Footer */}
      <Footer className="relative z-10" />

      {/* Host Lobby Modal */}
      <HostLobbyModal
        open={hostModalOpen}
        onClose={() => setHostModalOpen(false)}
      />

      {/* Match Overlay */}
      <MatchOverlay
        open={matchOverlayOpen}
        onClose={() => setMatchOverlayOpen(false)}
        lobby={selectedLobby ? {
          stake: selectedLobby.buyIn,
          size: selectedLobby.maxPlayers,
          status: selectedLobby.active ? 'Open' : 'Closed',
          players: selectedLobby.players.map(addr => ({
            address: truncateAddress(addr),
            ready: true,
          })),
        } : undefined}
      />
    </div>
  );
};

export default Play;
