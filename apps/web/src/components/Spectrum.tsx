interface Zone {
  from: number;
  to: number;
  tone: "negative" | "uncertain" | "positive";
}

interface Tick {
  at: number;
  label: string;
}

interface SpectrumProps {
  /** Score entre 0 et 1. */
  score: number;
  zones: Zone[];
  ticks: Tick[];
  ariaLabel: string;
}

/** Échelle de 0 à 1 découpée en zones de décision, avec un repère à la position du score. */
export function Spectrum({ score, zones, ticks, ariaLabel }: SpectrumProps) {
  const position = `${Math.min(Math.max(score, 0), 1) * 100}%`;
  return (
    <div className="spectrum" role="img" aria-label={ariaLabel}>
      <div className="spectrum-track">
        {zones.map((zone) => (
          <span
            key={`${zone.from}-${zone.to}`}
            className={`zone zone-${zone.tone}`}
            style={{ left: `${zone.from * 100}%`, width: `${(zone.to - zone.from) * 100}%` }}
          />
        ))}
        <span className="marker" style={{ left: position }} />
      </div>
      <div className="spectrum-ticks" aria-hidden="true">
        {ticks.map((tick) => (
          <span key={tick.at} style={{ left: `${tick.at * 100}%` }}>
            {tick.label}
          </span>
        ))}
      </div>
    </div>
  );
}
