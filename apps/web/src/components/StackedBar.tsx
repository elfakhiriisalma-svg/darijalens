import { asPercent, type Segment } from "../lib/stats";

interface StackedBarProps {
  title: string;
  segments: Segment[];
}

/** Une barre découpée en parts, avec la légende chiffrée dessous. */
export function StackedBar({ title, segments }: StackedBarProps) {
  const total = segments.reduce((sum, segment) => sum + segment.count, 0);
  return (
    <div className="stacked">
      <h3>{title}</h3>
      <div
        className="stacked-track"
        role="img"
        aria-label={segments.map((s) => `${s.label} : ${s.count}`).join(", ")}
      >
        {segments
          .filter((segment) => segment.count > 0)
          .map((segment) => (
            <span key={segment.key} className={`seg seg-${segment.tone}`} style={{ width: `${segment.share * 100}%` }} />
          ))}
      </div>
      {total === 0 ? (
        <p className="legend-empty">Aucune donnée.</p>
      ) : (
        <ul className="stacked-legend">
          {segments.map((segment) => (
            <li key={segment.key}>
              <span className={`swatch-dot seg-${segment.tone}`} aria-hidden="true" />
              <span className="legend-label">{segment.label}</span>
              <span className="legend-value">
                {segment.count} <small>({asPercent(segment.share)})</small>
              </span>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
