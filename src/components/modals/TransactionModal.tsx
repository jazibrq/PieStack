import { useState } from 'react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Modal, ModalContent, ModalHeader, ModalFooter } from '@/components/ui/modal';
import { Info, Loader2, CheckCircle, ArrowRight } from 'lucide-react';
import { cn } from '@/lib/utils';
import { useStaking } from '@/hooks/useStaking';
import { useWallet } from '@/contexts/WalletContext';

interface TransactionModalProps {
  open: boolean;
  onClose: () => void;
  type: 'deposit' | 'withdraw';
  maxAmount?: string;
  onSuccess?: () => void;
}

export const TransactionModal = ({
  open,
  onClose,
  type,
  maxAmount = '0',
  onSuccess,
}: TransactionModalProps) => {
  const [amount, setAmount] = useState('');
  const [step, setStep] = useState<'input' | 'approving' | 'confirming' | 'success' | 'error'>('input');
  const [errorMsg, setErrorMsg] = useState('');
  const { deposit, withdraw } = useStaking();
  const { isConnected, balance } = useWallet();

  const titles = {
    deposit: 'Deposit to Vault',
    withdraw: 'Withdraw from Vault',
  };

  const displayMax = type === 'deposit' ? balance : maxAmount;

  const handleConfirm = async () => {
    if (!isConnected) return;

    setStep('approving');
    setErrorMsg('');

    try {
      setStep('confirming');

      if (type === 'deposit') {
        await deposit(amount);
      } else {
        await withdraw();
      }

      setStep('success');
      onSuccess?.();
    } catch (error: unknown) {
      console.error('Transaction failed:', error);
      const err = error as { reason?: string; message?: string };
      setErrorMsg(err.reason || err.message || 'Transaction failed');
      setStep('error');
    }
  };

  const handleClose = () => {
    setStep('input');
    setAmount('');
    setErrorMsg('');
    onClose();
  };

  return (
    <Modal open={open} onClose={handleClose}>
      <ModalContent>
        <ModalHeader onClose={handleClose}>{titles[type]}</ModalHeader>

        {step === 'input' && (
          <>
            <div className="space-y-4">
              {type === 'deposit' ? (
                <div className="space-y-2">
                  <label className="text-sm text-muted-foreground">Amount (MON)</label>
                  <div className="relative">
                    <Input
                      type="number"
                      placeholder="0.00"
                      value={amount}
                      onChange={(e) => setAmount(e.target.value)}
                      className="pr-16 text-lg font-mono"
                    />
                    <button
                      onClick={() => setAmount(parseFloat(displayMax) > 0.002 ? (parseFloat(displayMax) - 0.002).toFixed(6) : '0')}
                      className="absolute right-2 top-1/2 -translate-y-1/2 text-xs font-medium text-primary hover:text-primary/80 transition-colors"
                    >
                      MAX
                    </button>
                  </div>
                  <p className="text-xs text-muted-foreground">
                    Wallet Balance: {parseFloat(displayMax).toFixed(6)} MON
                  </p>
                </div>
              ) : (
                <div className="space-y-2">
                  <p className="text-sm text-muted-foreground">
                    Withdraw your entire staking position (principal + unclaimed rewards).
                  </p>
                  <div className="p-4 rounded-lg bg-surface-2">
                    <div className="flex justify-between text-sm">
                      <span className="text-muted-foreground">Total to receive</span>
                      <span className="font-mono text-primary">{parseFloat(maxAmount).toFixed(6)} MON</span>
                    </div>
                  </div>
                </div>
              )}

              {type === 'withdraw' && (
                <div className="flex gap-2 p-3 rounded-lg bg-amber-500/10 border border-amber-500/20">
                  <Info className="w-4 h-4 text-amber-400 shrink-0 mt-0.5" />
                  <p className="text-xs text-amber-200">
                    Withdrawing removes your full staking position. You will receive your principal plus any unclaimed rewards.
                  </p>
                </div>
              )}

              <div className="p-3 rounded-lg bg-surface-2 space-y-2">
                <div className="flex justify-between text-sm">
                  <span className="text-muted-foreground">Estimated Gas</span>
                  <span className="font-mono">~0.002 MON</span>
                </div>
                <div className="flex justify-between text-sm">
                  <span className="text-muted-foreground">Network</span>
                  <span>Monad Testnet</span>
                </div>
              </div>
            </div>

            <ModalFooter>
              <Button variant="outline" onClick={handleClose} className="flex-1">
                Cancel
              </Button>
              <Button
                onClick={handleConfirm}
                disabled={type === 'deposit' ? (!amount || parseFloat(amount) <= 0) : parseFloat(maxAmount) <= 0}
                className="flex-1 btn-cyan-gradient"
              >
                Confirm {type.charAt(0).toUpperCase() + type.slice(1)}
              </Button>
            </ModalFooter>
          </>
        )}

        {(step === 'approving' || step === 'confirming') && (
          <div className="py-8 text-center">
            <div className="flex justify-center mb-4">
              <div className="relative">
                <Loader2 className="w-12 h-12 text-primary animate-spin" />
                <div className="absolute inset-0 rounded-full animate-glow-pulse" />
              </div>
            </div>

            <div className="space-y-4">
              <div className="flex items-center justify-center gap-3">
                <div className={cn(
                  'w-8 h-8 rounded-full flex items-center justify-center text-sm font-medium',
                  step === 'approving' ? 'bg-primary text-primary-foreground' : 'bg-emerald-500 text-white'
                )}>
                  {step === 'confirming' ? <CheckCircle className="w-4 h-4" /> : '1'}
                </div>
                <ArrowRight className="w-4 h-4 text-muted-foreground" />
                <div className={cn(
                  'w-8 h-8 rounded-full flex items-center justify-center text-sm font-medium',
                  step === 'confirming' ? 'bg-primary text-primary-foreground' : 'bg-surface-3 text-muted-foreground'
                )}>
                  2
                </div>
              </div>

              <p className="text-sm text-muted-foreground">
                {step === 'approving' ? 'Waiting for wallet approval...' : 'Confirming on Monad...'}
              </p>
            </div>
          </div>
        )}

        {step === 'success' && (
          <div className="py-8 text-center">
            <div className="flex justify-center mb-4">
              <div className="w-16 h-16 rounded-full bg-emerald-500/20 flex items-center justify-center">
                <CheckCircle className="w-8 h-8 text-emerald-400" />
              </div>
            </div>
            <h3 className="text-lg font-semibold mb-2">Transaction Successful!</h3>
            <p className="text-sm text-muted-foreground mb-6">
              {type === 'deposit'
                ? `${amount} MON has been deposited and staked.`
                : 'Your full position has been withdrawn.'}
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
            <h3 className="text-lg font-semibold mb-2">Transaction Failed</h3>
            <p className="text-sm text-muted-foreground mb-6">
              {errorMsg}
            </p>
            <Button onClick={() => setStep('input')} className="btn-cyan-gradient">
              Try Again
            </Button>
          </div>
        )}
      </ModalContent>
    </Modal>
  );
};
