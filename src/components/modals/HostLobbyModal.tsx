import { useState } from 'react';
import { Button } from '@/components/ui/button';
import { Modal, ModalContent, ModalHeader, ModalFooter } from '@/components/ui/modal';
import { Input } from '@/components/ui/input';
import { Info, Loader2, CheckCircle } from 'lucide-react';
import { cn } from '@/lib/utils';
import { useGameManager } from '@/hooks/useGameManager';
import { useStaking } from '@/hooks/useStaking';

interface HostLobbyModalProps {
  open: boolean;
  onClose: () => void;
}

const lobbySizes = [2, 4, 8, 16];

export const HostLobbyModal = ({ open, onClose }: HostLobbyModalProps) => {
  const [stake, setStake] = useState('');
  const [size, setSize] = useState(4);
  const [step, setStep] = useState<'input' | 'confirming' | 'success' | 'error'>('input');
  const [errorMsg, setErrorMsg] = useState('');

  const { createLobby, loading } = useGameManager();
  const { availableRewards } = useStaking();

  const rewardsNum = parseFloat(availableRewards);
  const stakeNum = parseFloat(stake) || 0;
  const hasEnoughRewards = stakeNum > 0 && rewardsNum >= stakeNum;

  const handleHost = async () => {
    if (!hasEnoughRewards) return;

    setStep('confirming');
    setErrorMsg('');

    try {
      await createLobby(stake, size);
      setStep('success');
    } catch (error: unknown) {
      const err = error as { reason?: string; message?: string };
      setErrorMsg(err.reason || err.message || 'Failed to create lobby');
      setStep('error');
    }
  };

  const handleClose = () => {
    setStep('input');
    setStake('');
    setErrorMsg('');
    onClose();
  };

  return (
    <Modal open={open} onClose={handleClose}>
      <ModalContent>
        <ModalHeader onClose={handleClose}>Host New Lobby</ModalHeader>

        {step === 'input' && (
          <>
            <div className="space-y-6">
              {/* Buy-in Amount */}
              <div className="space-y-2">
                <label className="text-sm text-muted-foreground">Buy-in Amount (MON rewards)</label>
                <Input
                  type="number"
                  placeholder="0.00"
                  value={stake}
                  onChange={(e) => setStake(e.target.value)}
                  className="text-lg font-mono"
                />
                <p className="text-xs text-muted-foreground">
                  Available rewards: {rewardsNum.toFixed(6)} MON
                </p>
                {stakeNum > 0 && !hasEnoughRewards && (
                  <p className="text-xs text-red-400">
                    Insufficient rewards. You need {stakeNum.toFixed(6)} MON but have {rewardsNum.toFixed(6)} MON.
                  </p>
                )}
              </div>

              {/* Lobby Size */}
              <div className="space-y-2">
                <label className="text-sm text-muted-foreground">Lobby Size</label>
                <div className="grid grid-cols-4 gap-2">
                  {lobbySizes.map((s) => (
                    <button
                      key={s}
                      onClick={() => setSize(s)}
                      className={cn(
                        'py-2 rounded-lg text-sm font-medium transition-all',
                        size === s
                          ? 'bg-primary text-primary-foreground shadow-glow-cyan-subtle'
                          : 'bg-surface-2 text-muted-foreground hover:bg-surface-3 hover:text-foreground'
                      )}
                    >
                      {s}
                    </button>
                  ))}
                </div>
              </div>

              {/* Info */}
              <div className="flex gap-2 p-3 rounded-lg bg-primary/10 border border-primary/20">
                <Info className="w-4 h-4 text-primary shrink-0 mt-0.5" />
                <p className="text-xs text-foreground/80">
                  As the host, your buy-in ({stakeNum.toFixed(4)} MON) is deducted from your staking rewards when the lobby is created.
                  Only rewards are used — your principal is never touched.
                </p>
              </div>

              {/* Summary */}
              <div className="p-4 rounded-lg bg-surface-2 space-y-2">
                <div className="flex justify-between text-sm">
                  <span className="text-muted-foreground">Buy-in per player</span>
                  <span className="font-mono text-primary">
                    {stakeNum.toFixed(4)} MON
                  </span>
                </div>
                <div className="flex justify-between text-sm">
                  <span className="text-muted-foreground">Max Prize Pool</span>
                  <span className="font-mono text-amber-400">
                    {(stakeNum * size).toFixed(4)} MON
                  </span>
                </div>
                <div className="flex justify-between text-sm">
                  <span className="text-muted-foreground">Winner Takes</span>
                  <span className="font-mono font-semibold">
                    {(stakeNum * size).toFixed(4)} MON (100%)
                  </span>
                </div>
              </div>
            </div>

            <ModalFooter>
              <Button variant="outline" onClick={handleClose} className="flex-1">
                Cancel
              </Button>
              <Button
                onClick={handleHost}
                disabled={!hasEnoughRewards || loading}
                className="flex-1 btn-cyan-gradient"
              >
                {loading ? 'Creating...' : 'Create Lobby'}
              </Button>
            </ModalFooter>
          </>
        )}

        {step === 'confirming' && (
          <div className="py-8 text-center">
            <div className="flex justify-center mb-4">
              <Loader2 className="w-12 h-12 text-primary animate-spin" />
            </div>
            <p className="text-sm text-muted-foreground">Creating lobby on Monad...</p>
          </div>
        )}

        {step === 'success' && (
          <div className="py-8 text-center">
            <div className="flex justify-center mb-4">
              <div className="w-16 h-16 rounded-full bg-emerald-500/20 flex items-center justify-center">
                <CheckCircle className="w-8 h-8 text-emerald-400" />
              </div>
            </div>
            <h3 className="text-lg font-semibold mb-2">Lobby Created!</h3>
            <p className="text-sm text-muted-foreground mb-6">
              Your lobby is live. {stakeNum.toFixed(4)} MON was deducted from your rewards as buy-in.
            </p>
            <Button onClick={handleClose} className="btn-cyan-gradient">
              Done
            </Button>
          </div>
        )}

        {step === 'error' && (
          <div className="py-8 text-center">
            <div className="flex justify-center mb-4">
              <div className="w-16 h-16 rounded-full bg-red-500/20 flex items-center justify-center">
                <Info className="w-8 h-8 text-red-400" />
              </div>
            </div>
            <h3 className="text-lg font-semibold mb-2">Failed to Create Lobby</h3>
            <p className="text-sm text-muted-foreground mb-6">{errorMsg}</p>
            <Button onClick={() => setStep('input')} className="btn-cyan-gradient">
              Try Again
            </Button>
          </div>
        )}
      </ModalContent>
    </Modal>
  );
};
