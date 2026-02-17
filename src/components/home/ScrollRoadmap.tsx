import { useEffect, useRef, useState } from 'react';
import { cn } from '@/lib/utils';
import { Wallet, RefreshCw, TrendingUp, Gamepad2, Trophy, Shield, Pizza } from 'lucide-react';
import { GlassPanel } from '@/components/AnimatedBackground';

const roadmapSteps = [
  {
    id: 1,
    title: 'Deposit Monad',
    description: 'Send MON to your Pie Stack vault — non-custodial and always in your control.',
    icon: Wallet,
    visual: 'deposit',
  },
  {
    id: 2,
    title: 'Stake & Receive sMON',
    description: 'Your Monad is automatically staked. You receive sMON — liquid staked Monad that earns baseline yield.',
    icon: RefreshCw,
    visual: 'stake',
  },
  {
    id: 3,
    title: 'Awards Accumulate',
    description: 'Staking yield drips into your Pending Awards balance over time. Your MON principal stays untouched.',
    icon: TrendingUp,
    visual: 'accumulate',
  },
  {
    id: 4,
    title: 'Play Competitive Games',
    description: 'Join lobbies and compete against other players — only your accumulated awards are at stake, never your deposit.',
    icon: Gamepad2,
    visual: 'play',
  },
  {
    id: 5,
    title: 'Win Outsized Yield',
    description: 'Victory means claiming MON awards from the prize pool, multiplying what staking alone would earn.',
    icon: Trophy,
    visual: 'win',
  },
  {
    id: 6,
    title: 'Zero Downside Risk',
    description: 'Your sMON stays staked and protected throughout. You compete only with yield — your Monad is never at risk.',
    icon: Shield,
    visual: 'safe',
  },
];

const DriftingToken = ({ delay, children, isActive }: { delay: number; children: React.ReactNode; isActive: boolean }) => (
  <div
    className={cn(
      'px-2 py-1 rounded bg-surface-3 text-xs font-mono transition-all duration-500',
      isActive && 'token-drift'
    )}
    style={{ animationDelay: `${delay}ms` }}
  >
    {children}
  </div>
);

const StepVisual = ({ type, isActive }: { type: string; isActive: boolean }) => (
  <div className={cn(
    'w-full h-44 rounded-lg border transition-all duration-500 overflow-hidden relative',
    isActive
      ? 'bg-surface-2 border-primary/30 shadow-[0_0_30px_hsl(217_100%_61%/0.12)]'
      : 'bg-surface-1 border-border'
  )}>
    {type === 'deposit' && (
      <div className="absolute inset-0 flex items-center justify-center gap-5">
        <div className={cn(
          'w-12 h-12 rounded-lg flex items-center justify-center transition-all duration-500',
          isActive ? 'bg-primary/20' : 'bg-surface-3'
        )}>
          <Wallet className={cn('w-6 h-6 transition-all duration-500', isActive ? 'text-primary scale-110' : 'text-muted-foreground')} />
        </div>
        <div className="flex flex-col gap-1">
          {[0, 1, 2].map((i) => (
            <div
              key={i}
              className={cn('h-1.5 rounded-full transition-all duration-500', isActive ? 'bg-primary' : 'bg-muted-foreground/30')}
              style={{ width: isActive ? `${32 - i * 4}px` : '8px', transitionDelay: `${i * 80}ms`, opacity: isActive ? 1 - i * 0.2 : 0.3 }}
            />
          ))}
        </div>
        <div className={cn(
          'w-14 h-14 rounded-lg flex flex-col items-center justify-center gap-0.5 transition-all duration-500',
          isActive ? 'bg-primary text-primary-foreground shadow-[0_0_20px_hsl(217_100%_61%/0.4)]' : 'bg-surface-3 text-muted-foreground'
        )}>
          <span className="text-[9px] font-bold tracking-wider">VAULT</span>
        </div>
        <div className={cn(
          'absolute bottom-3 left-1/2 -translate-x-1/2 flex gap-2 transition-all duration-500',
          isActive ? 'opacity-100 translate-y-0' : 'opacity-0 translate-y-2'
        )}>
          <DriftingToken delay={0} isActive={isActive}>MON</DriftingToken>
        </div>
      </div>
    )}

    {type === 'stake' && (
      <div className="absolute inset-0 flex items-center justify-center">
        <div className="flex items-center gap-5">
          <div className={cn(
            'px-3 py-2 rounded-lg text-sm font-mono font-medium transition-all duration-500',
            isActive ? 'bg-surface-3 text-foreground transform-pulse' : 'bg-surface-3/50 text-muted-foreground'
          )}>
            MON
          </div>
          <div className={cn('text-2xl transition-all duration-500', isActive ? 'text-primary scale-125' : 'text-muted-foreground/30')}>→</div>
          <div className={cn(
            'w-20 h-20 rounded-xl flex flex-col items-center justify-center gap-1.5 transition-all duration-500',
            isActive ? 'bg-primary/10 border border-primary/30 shadow-[0_0_20px_hsl(217_100%_61%/0.2)]' : 'bg-surface-3'
          )}>
            <span className="text-[9px] font-bold text-muted-foreground tracking-wider">VAULT</span>
            <div className={cn(
              'px-2 py-1 rounded text-xs font-mono font-medium transition-all duration-500',
              isActive ? 'bg-primary/20 text-primary scale-105' : 'bg-surface-2 text-muted-foreground'
            )}>
              sMON
            </div>
          </div>
        </div>
      </div>
    )}

    {type === 'accumulate' && (
      <div className="absolute inset-0 flex items-center justify-center">
        <div className="flex flex-col items-center gap-3">
          <p className={cn('text-xs font-medium uppercase tracking-wider transition-all duration-500', isActive ? 'text-muted-foreground' : 'text-muted-foreground/40')}>
            Pending Awards
          </p>
          <div className={cn('text-3xl font-bold font-mono tabular-nums transition-all duration-500', isActive ? 'text-primary' : 'text-muted-foreground/40')}>
            {isActive ? <AnimatedCounter /> : '0.0000'}
            <span className="text-base ml-1 font-medium">MON</span>
          </div>
          <div className="flex items-end gap-1 h-10">
            {[20, 30, 35, 42, 48, 55, 62, 70].map((h, i) => (
              <div
                key={i}
                className={cn('w-3 rounded-t transition-all duration-500 origin-bottom', isActive ? 'bg-primary' : 'bg-muted-foreground/20')}
                style={{ height: isActive ? `${h}%` : '20%', opacity: isActive ? 0.4 + i * 0.075 : 0.3, transitionDelay: `${i * 50}ms` }}
              />
            ))}
          </div>
        </div>
      </div>
    )}

    {type === 'play' && (
      <div className="absolute inset-0 flex items-center justify-center">
        <div className="flex items-center gap-3">
          {['VAULT', 'LOBBY'].map((label, i) => (
            <>
              <div
                key={label}
                className={cn(
                  'w-12 h-12 rounded-lg flex items-center justify-center text-[9px] font-bold tracking-wide transition-all duration-500',
                  isActive ? (i === 0 ? 'bg-primary/20 text-primary' : 'bg-surface-3 text-foreground scale-105') : 'bg-surface-3 text-muted-foreground'
                )}
                style={{ transitionDelay: `${i * 150}ms` }}
              >
                {label}
              </div>
              <div className={cn('text-lg transition-all duration-300', isActive ? 'text-primary' : 'text-muted-foreground/30')}
                style={{ transitionDelay: `${i * 150 + 75}ms` }}>→</div>
            </>
          ))}
          <div className={cn(
            'w-14 h-14 rounded-lg flex items-center justify-center transition-all duration-500',
            isActive ? 'bg-primary text-primary-foreground shadow-[0_0_25px_hsl(217_100%_61%/0.5)]' : 'bg-surface-3 text-muted-foreground'
          )}
          style={{ transitionDelay: '300ms' }}>
            <Gamepad2 className={cn('w-6 h-6 transition-transform duration-500', isActive && 'scale-110')} />
          </div>
        </div>
      </div>
    )}

    {type === 'win' && (
      <div className="absolute inset-0 flex items-center justify-center">
        <div className="flex flex-col items-center gap-3">
          <div className={cn(
            'w-14 h-14 rounded-full flex items-center justify-center transition-all duration-500',
            isActive ? 'bg-amber-500/20 shadow-[0_0_30px_rgba(245,158,11,0.35)]' : 'bg-surface-3'
          )}>
            <Trophy className={cn('w-7 h-7 transition-all duration-500', isActive ? 'text-amber-400 scale-110' : 'text-muted-foreground')} />
          </div>
          <div className={cn(
            'px-4 py-2 rounded-lg text-sm font-bold font-mono transition-all duration-500',
            isActive ? 'bg-primary/20 text-primary scale-105 shadow-[0_0_12px_hsl(217_100%_61%/0.3)]' : 'bg-surface-3 text-muted-foreground'
          )}>
            + 2.45 MON
          </div>
          <p className={cn('text-xs transition-all duration-500', isActive ? 'text-muted-foreground opacity-100' : 'opacity-0')}>
            Prize pool multiplier
          </p>
        </div>
      </div>
    )}

    {type === 'safe' && (
      <div className="absolute inset-0 flex items-center justify-center gap-6">
        <div className={cn(
          'w-20 h-20 rounded-xl flex flex-col items-center justify-center gap-1.5 relative transition-all duration-500',
          isActive ? 'bg-emerald-500/10 border border-emerald-500/30 shadow-[0_0_20px_rgba(16,185,129,0.2)]' : 'bg-surface-3'
        )}>
          <Shield className={cn('w-5 h-5 transition-all duration-500', isActive ? 'text-emerald-400 scale-110' : 'text-muted-foreground')} />
          <span className={cn('text-[9px] font-bold font-mono tracking-wider transition-colors duration-500', isActive ? 'text-emerald-400' : 'text-muted-foreground')}>
            sMON
          </span>
          <div className={cn(
            'absolute -top-1 -right-1 w-4 h-4 rounded-full bg-emerald-500 flex items-center justify-center transition-all duration-300',
            isActive ? 'scale-100 opacity-100' : 'scale-0 opacity-0'
          )}>
            <span className="text-[8px] text-emerald-950 font-bold">✓</span>
          </div>
        </div>
        <div className="flex flex-col gap-1 text-center">
          <span className={cn('text-sm font-medium transition-all duration-500', isActive ? 'text-foreground' : 'text-muted-foreground')}>
            Always safe
          </span>
          <span className={cn('text-xs transition-all duration-500', isActive ? 'text-muted-foreground opacity-100' : 'opacity-0')}>
            Yield competes, not principal
          </span>
        </div>
      </div>
    )}
  </div>
);

const AnimatedCounter = () => {
  const [value, setValue] = useState(0.3);
  const [tick, setTick] = useState(false);
  useEffect(() => {
    const interval = setInterval(() => {
      setValue(prev => (prev + 0.0012 > 1.5 ? 0.3 : prev + 0.0012));
      setTick(true);
      setTimeout(() => setTick(false), 150);
    }, 100);
    return () => clearInterval(interval);
  }, []);
  return <span className={tick ? 'counter-tick' : ''}>{value.toFixed(4)}</span>;
};

export const ScrollRoadmap = () => {
  const containerRef = useRef<HTMLDivElement>(null);
  const [activeStep, setActiveStep] = useState(1);
  const [scrollProgress, setScrollProgress] = useState(0);
  const prevActiveStep = useRef(1);

  useEffect(() => {
    const handleScroll = () => {
      if (!containerRef.current) return;
      const rect = containerRef.current.getBoundingClientRect();
      const scrollStart = rect.top - window.innerHeight * 0.5;
      const scrollEnd = rect.top + rect.height - window.innerHeight * 0.5;
      const progress = Math.max(0, Math.min(1, -scrollStart / (scrollEnd - scrollStart)));
      setScrollProgress(progress);
      const newStep = Math.max(1, Math.min(6, Math.ceil(progress * 6) || 1));
      if (newStep !== prevActiveStep.current) {
        prevActiveStep.current = newStep;
        setActiveStep(newStep);
      }
    };
    window.addEventListener('scroll', handleScroll, { passive: true });
    handleScroll();
    return () => window.removeEventListener('scroll', handleScroll);
  }, []);

  return (
    <section ref={containerRef} className="py-24 relative">
      <div className="container mx-auto max-w-6xl px-4">
        {/* Header */}
        <div className="text-center mb-16">
          <h2 className="text-3xl md:text-4xl font-bold tracking-tight mb-4">
            How <span className="text-gradient-cyan">Pie Stack</span> Works
          </h2>
          <p className="text-muted-foreground text-lg max-w-2xl mx-auto">
            Stake Monad, earn yield, compete — your principal is always protected.
          </p>
        </div>

        {/* Main layout: pizza rail + steps */}
        <div className="flex gap-6 md:gap-10">

          {/* Left: Pizza progress rail */}
          <div className="relative flex-shrink-0 w-16 hidden sm:block">
            {/* Background line — full height */}
            <div className="absolute left-1/2 -translate-x-1/2 top-0 bottom-0 w-px bg-surface-3" />

            {/* Filled line — tracks up to the pizza */}
            <div
              className="absolute left-1/2 -translate-x-1/2 top-0 w-px bg-gradient-to-b from-primary to-accent"
              style={{ height: `${scrollProgress * 100}%`, transition: 'height 0.3s ease-out' }}
            />

            {/* Pizza — moves down the rail as scroll progresses */}
            <div
              className="absolute left-1/2 -translate-x-1/2 -translate-y-1/2 z-10"
              style={{ top: `${Math.max(4, Math.min(96, scrollProgress * 100))}%`, transition: 'top 0.3s ease-out' }}
            >
              <div
                className="relative w-16 h-16"
                style={{
                  filter: scrollProgress > 0.02
                    ? `drop-shadow(0 0 ${6 + scrollProgress * 10}px rgba(255,159,28,${0.25 + scrollProgress * 0.55}))`
                    : undefined,
                }}
              >
                {/* Ghost pizza */}
                <Pizza className="absolute inset-0 w-16 h-16 text-surface-3" strokeWidth={1.5} />
                {/* Orange fill — reveals top-to-bottom as scroll increases */}
                <div
                  className="absolute inset-0 overflow-hidden"
                  style={{ clipPath: `inset(0 0 ${(1 - scrollProgress) * 100}% 0)` }}
                >
                  <Pizza className="w-16 h-16" strokeWidth={1.5} style={{ color: '#FF9F1C' }} />
                </div>
              </div>
            </div>
          </div>

          {/* Right: Steps */}
          <div className="flex-1 space-y-14 md:space-y-20">
            {roadmapSteps.map((step, index) => {
              const isActive = step.id === activeStep;
              const isPast = step.id < activeStep;
              const isFuture = step.id > activeStep;

              return (
                <div
                  key={step.id}
                  className={cn(
                    'transition-all duration-500',
                    isActive && 'scale-[1.01]',
                    isFuture && 'opacity-40'
                  )}
                >
                  <div className="grid md:grid-cols-2 gap-5 md:gap-8 items-center">
                    {/* Content panel */}
                    <div className={cn('transition-all duration-500', index % 2 === 1 && 'md:order-2')}>
                      <GlassPanel active={isActive} glow={isActive} className="p-5">
                        <div className={cn('flex items-center gap-3 mb-3 transition-all duration-500', isActive && 'translate-x-1')}>
                          <div className={cn(
                            'w-9 h-9 rounded-lg flex items-center justify-center transition-all duration-500',
                            isActive ? 'bg-primary/20 scale-110' : isPast ? 'bg-primary/10' : 'bg-surface-2/50'
                          )}>
                            {isPast
                              ? <span className="text-primary text-sm font-bold">✓</span>
                              : <step.icon className={cn('w-4 h-4 transition-all duration-500', isActive ? 'text-primary' : 'text-muted-foreground')} />
                            }
                          </div>
                          <h3 className={cn(
                            'text-lg font-semibold tracking-tight transition-colors duration-500',
                            isActive ? 'text-foreground' : 'text-muted-foreground'
                          )}>
                            {step.title}
                          </h3>
                        </div>
                        <p className={cn(
                          'text-sm leading-relaxed transition-colors duration-500',
                          isActive ? 'text-muted-foreground' : 'text-muted-foreground/50'
                        )}>
                          {step.description}
                        </p>
                      </GlassPanel>
                    </div>

                    {/* Visual */}
                    <div className={cn('transition-all duration-500', index % 2 === 1 && 'md:order-1')}>
                      <StepVisual type={step.visual} isActive={isActive} />
                    </div>
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      </div>
    </section>
  );
};
