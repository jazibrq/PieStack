import chainlinkLogo from '@/assets/chainlink-logo.svg';
import uniswapLogo from '@/assets/uniswap-logo.svg';

// Monad inline logo
const MonadLogo = () => (
  <svg viewBox="0 0 32 32" className="w-auto h-6">
    <circle cx="16" cy="16" r="16" fill="#836EF9"/>
    <text x="16" y="21" textAnchor="middle" fontSize="13" fontWeight="bold" fill="white" fontFamily="sans-serif">M</text>
  </svg>
);

// sMON inline logo
const StMonadLogo = () => (
  <svg viewBox="0 0 32 32" className="w-auto h-6">
    <circle cx="16" cy="16" r="16" fill="#FF9F1C"/>
    <text x="16" y="20" textAnchor="middle" fontSize="9" fontWeight="bold" fill="white" fontFamily="sans-serif">sMON</text>
  </svg>
);

// ETH diamond logo
const EthLogo = () => (
  <svg viewBox="0 0 32 32" className="w-auto h-6">
    <g transform="translate(16, 16)">
      <polygon points="0,-14 8,0 0,4 -8,0" fill="#627EEA" />
      <polygon points="0,4 8,0 0,14 -8,0" fill="#3C3C3D" />
      <polygon points="0,-14 0,4 -8,0" fill="#8A92B2" opacity="0.6" />
      <polygon points="0,4 0,14 -8,0" fill="#8A92B2" opacity="0.6" />
    </g>
  </svg>
);

const partners = [
  { name: 'Ethereum', logo: EthLogo, height: 'h-6', isComponent: true },
  { name: 'ChainLink', logo: chainlinkLogo, height: 'h-6', isComponent: false },
  { name: 'UniSwap', logo: uniswapLogo, height: 'h-5', isComponent: false },
  { name: 'MON', logo: MonadLogo, height: 'h-6', isComponent: true },
  { name: 'sMON', logo: StMonadLogo, height: 'h-6', isComponent: true },
];

// Duplicate for seamless loop
const items = [...partners, ...partners, ...partners, ...partners];

export const PartnersBanner = ({ className = '' }: { className?: string }) => {
  return (
    <section className={`bg-black py-6 overflow-hidden ${className}`}>
      <div className="relative">
        <div className="flex animate-scroll-x gap-6 w-max">
          {items.map((partner, i) => (
            <div
              key={i}
              className="flex items-center gap-3 px-6 py-3 rounded-xl border border-white/10 bg-white/5 backdrop-blur-sm whitespace-nowrap shrink-0"
            >
              {partner.isComponent ? (
                <partner.logo />
              ) : (
                <img src={partner.logo} alt={partner.name} className={`${partner.height} w-auto`} />
              )}
              <span className="text-sm font-medium text-foreground">
                {partner.name}
              </span>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
};
