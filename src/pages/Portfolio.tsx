import { useState } from 'react';
import { Navigation } from '@/components/Navigation';
import { VideoBackground } from '@/components/VideoBackground';
import { GrainOverlay } from '@/components/GrainOverlay';
import { Button } from '@/components/ui/button';
import { MetricCard } from '@/components/ui/shared';
import { TransactionModal } from '@/components/modals/TransactionModal';
import { PartnersBanner } from '@/components/home/PartnersBanner';
import { Footer } from '@/components/layout/Footer';
import {
  Wallet, TrendingUp,
  ArrowUpRight, ArrowDownRight,
  Calendar
} from 'lucide-react';
import { useWallet } from '@/contexts/WalletContext';
import { useStaking } from '@/hooks/useStaking';

const Portfolio = () => {
  const [modalType, setModalType] = useState<'deposit' | 'withdraw' | null>(null);
  const { isConnected, balance, connect } = useWallet();
  const { principal, availableRewards, refreshBalances } = useStaking();

  const principalNum = parseFloat(principal);
  const rewardsNum = parseFloat(availableRewards);
  const walletBal = parseFloat(balance) || 0;
  const totalPosition = principalNum + walletBal;

  return (
    <div className="min-h-screen">
      <VideoBackground />
      <GrainOverlay />
      <Navigation />

      <main className="relative z-10 pt-24 pb-12">
        <div className="container mx-auto max-w-6xl px-4">
          {/* Header */}
          <div className="mb-8">
            <h1 className="text-3xl font-bold mb-2">Portfolio</h1>
            <p className="text-muted-foreground">Your vault performance and staking position</p>
          </div>

          {/* Not Connected State */}
          {!isConnected && (
            <div className="card-surface p-12 text-center mb-8">
              <div className="flex justify-center mb-4">
                <div className="w-16 h-16 rounded-full bg-surface-2 flex items-center justify-center text-muted-foreground">
                  <Wallet className="w-8 h-8" />
                </div>
              </div>
              <h3 className="text-lg font-semibold text-foreground mb-2">Connect Your Wallet</h3>
              <p className="text-sm text-muted-foreground max-w-sm mx-auto mb-6">
                Connect your wallet to view your staking position, accrued rewards, and manage deposits.
              </p>
              <Button onClick={connect} className="btn-cyan-gradient">
                Connect Wallet
              </Button>
            </div>
          )}

          {/* Metrics Strip */}
          <div className="grid grid-cols-2 lg:grid-cols-4 gap-4 mb-8">
            <MetricCard
              label="Total Deposited"
              value={isConnected ? `${principalNum.toFixed(4)} MON` : '0.00 MON'}
              subValue={isConnected ? 'Principal (staked)' : 'Connect wallet'}
              icon={<Wallet className="w-5 h-5" />}
              delay={0}
            />
            <MetricCard
              label="Available Rewards"
              value={isConnected ? `${rewardsNum.toFixed(6)} MON` : '0.00 MON'}
              subValue={isConnected ? 'Earned from games' : 'Connect wallet'}
              trend={isConnected && rewardsNum > 0 ? { value: 8.0, positive: true } : undefined}
              icon={<TrendingUp className="w-5 h-5" />}
              delay={100}
            />
            <MetricCard
              label="Total Position"
              value={isConnected ? `${totalPosition.toFixed(4)} MON` : '0.00 MON'}
              subValue={isConnected ? 'Deposited + wallet' : 'Connect wallet'}
              icon={<ArrowUpRight className="w-5 h-5" />}
              delay={200}
            />
            <MetricCard
              label="Wallet Balance"
              value={isConnected ? `${parseFloat(balance).toFixed(4)} MON` : '0.00 MON'}
              subValue={isConnected ? 'Available to deposit' : 'Connect wallet'}
              icon={<ArrowDownRight className="w-5 h-5" />}
              delay={300}
            />
          </div>

          {/* Main Grid */}
          <div className="grid lg:grid-cols-3 gap-6">
            {/* Left Column - Info */}
            <div className="lg:col-span-2 space-y-6">
              {/* Staking Info Card */}
              <div className="card-surface p-6">
                <h2 className="text-lg font-semibold mb-4">How It Works</h2>
                <div className="space-y-4">
                  <div className="flex items-start gap-3">
                    <div className="w-8 h-8 rounded-full bg-primary/10 flex items-center justify-center text-primary text-sm font-bold shrink-0">1</div>
                    <div>
                      <p className="text-sm font-medium">Deposit MON</p>
                      <p className="text-xs text-muted-foreground">Your MON is automatically staked as sMON. Principal is locked and cannot be used for games.</p>
                    </div>
                  </div>
                  <div className="flex items-start gap-3">
                    <div className="w-8 h-8 rounded-full bg-primary/10 flex items-center justify-center text-primary text-sm font-bold shrink-0">2</div>
                    <div>
                      <p className="text-sm font-medium">Earn Rewards</p>
                      <p className="text-xs text-muted-foreground">Staking rewards accrue at ~8% APY. Only these rewards can be used to enter game lobbies.</p>
                    </div>
                  </div>
                  <div className="flex items-start gap-3">
                    <div className="w-8 h-8 rounded-full bg-primary/10 flex items-center justify-center text-primary text-sm font-bold shrink-0">3</div>
                    <div>
                      <p className="text-sm font-medium">Play & Win</p>
                      <p className="text-xs text-muted-foreground">Use your rewards as buy-ins. Winners receive the full prize pool. Your principal remains safe.</p>
                    </div>
                  </div>
                  <div className="flex items-start gap-3">
                    <div className="w-8 h-8 rounded-full bg-primary/10 flex items-center justify-center text-primary text-sm font-bold shrink-0">4</div>
                    <div>
                      <p className="text-sm font-medium">Withdraw Anytime</p>
                      <p className="text-xs text-muted-foreground">Withdraw your full position (principal + unclaimed rewards) back to MON at any time.</p>
                    </div>
                  </div>
                </div>
              </div>

              {/* Position Breakdown */}
              {isConnected && principalNum > 0 && (
                <div className="card-surface p-6">
                  <h2 className="text-lg font-semibold mb-4">Position Breakdown</h2>
                  <div className="space-y-3">
                    <div className="flex justify-between items-center py-2 border-b border-border">
                      <span className="text-sm text-muted-foreground">Staked Principal (sMON)</span>
                      <span className="font-mono text-sm">{principalNum.toFixed(6)} MON</span>
                    </div>
                    <div className="flex justify-between items-center py-2 border-b border-border">
                      <span className="text-sm text-muted-foreground">Accrued Rewards</span>
                      <span className="font-mono text-sm text-primary">+{rewardsNum.toFixed(6)} MON</span>
                    </div>
                    <div className="flex justify-between items-center py-2">
                      <span className="text-sm font-medium">Total Position</span>
                      <span className="font-mono text-sm font-semibold">{totalPosition.toFixed(6)} MON</span>
                    </div>
                  </div>

                  {/* Progress bar showing rewards vs principal */}
                  {totalPosition > 0 && (
                    <div className="mt-4">
                      <div className="flex justify-between text-xs text-muted-foreground mb-1">
                        <span>Principal</span>
                        <span>Rewards</span>
                      </div>
                      <div className="h-2 rounded-full bg-surface-3 overflow-hidden">
                        <div
                          className="h-full bg-gradient-to-r from-primary to-emerald-400 rounded-full"
                          style={{ width: `${(principalNum / totalPosition) * 100}%` }}
                        />
                      </div>
                      <div className="flex justify-between text-xs mt-1">
                        <span className="text-primary">{((principalNum / totalPosition) * 100).toFixed(1)}%</span>
                        <span className="text-emerald-400">{((rewardsNum / totalPosition) * 100).toFixed(1)}%</span>
                      </div>
                    </div>
                  )}
                </div>
              )}
            </div>

            {/* Right Column - Vault Card */}
            <div className="space-y-6">
              {/* Vault Card */}
              <div className="card-surface-elevated p-6">
                <h2 className="text-lg font-semibold mb-6">Your Vault</h2>

                <div className="space-y-4 mb-6">
                  <div className="flex justify-between items-center">
                    <span className="text-sm text-muted-foreground">Staked Principal</span>
                    <span className="font-mono text-lg font-semibold">
                      {isConnected ? `${principalNum.toFixed(4)} MON` : '\u2014'}
                    </span>
                  </div>
                  <div className="flex justify-between items-center">
                    <span className="text-sm text-muted-foreground">Available Rewards</span>
                    <span className="font-mono text-lg text-primary">
                      {isConnected ? `+${rewardsNum.toFixed(6)} MON` : '\u2014'}
                    </span>
                  </div>
                  <div className="flex justify-between items-center">
                    <span className="text-sm text-muted-foreground">Wallet Balance</span>
                    <span className="font-mono text-lg text-muted-foreground">
                      {isConnected ? `${parseFloat(balance).toFixed(4)} MON` : '\u2014'}
                    </span>
                  </div>
                </div>

                <div className="space-y-3">
                  {isConnected ? (
                    <>
                      <Button
                        onClick={() => setModalType('deposit')}
                        className="w-full btn-cyan-gradient"
                      >
                        Deposit
                      </Button>
                      <Button
                        onClick={() => setModalType('withdraw')}
                        variant="outline"
                        className="w-full btn-outline-glow"
                        disabled={principalNum <= 0}
                      >
                        Withdraw
                      </Button>
                    </>
                  ) : (
                    <Button
                      onClick={connect}
                      className="w-full btn-cyan-gradient"
                    >
                      Connect Wallet
                    </Button>
                  )}
                </div>
              </div>

              {/* APY Info */}
              <div className="card-surface p-4">
                <div className="flex items-center gap-3">
                  <Calendar className="w-5 h-5 text-muted-foreground" />
                  <div>
                    <p className="text-sm font-medium">Current APY</p>
                    <p className="text-xs text-muted-foreground">~8% baseline yield</p>
                  </div>
                  <span className="ml-auto font-mono text-lg text-primary">8.0%</span>
                </div>
              </div>

            </div>
          </div>
        </div>

      </main>

      {/* Partners Banner */}
      <PartnersBanner className="mt-20 relative z-10" />

      {/* Footer */}
      <Footer className="relative z-10" />

      {/* Transaction Modal */}
      {modalType && (
        <TransactionModal
          open={!!modalType}
          onClose={() => setModalType(null)}
          type={modalType}
          maxAmount={totalPosition.toString()}
          onSuccess={refreshBalances}
        />
      )}
    </div>
  );
};

export default Portfolio;
