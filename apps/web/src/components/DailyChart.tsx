import { barHeights, shortDay } from "../lib/stats";

interface DailyChartProps {
  daily: { date: string; count: number }[];
}

/** Nombre d'analyses par jour : une barre par jour. */
export function DailyChart({ daily }: DailyChartProps) {
  const heights = barHeights(daily.map((day) => day.count));
  const total = daily.reduce((sum, day) => sum + day.count, 0);
  const first = daily[0];
  const last = daily[daily.length - 1];
  return (
    <div className="daily">
      <h3>Activité des {daily.length} derniers jours</h3>
      <div className="daily-bars" role="img" aria-label={`${total} analyses sur ${daily.length} jours`}>
        {daily.map((day, index) => (
          <span key={day.date} className="daily-slot" title={`${shortDay(day.date)} : ${day.count}`}>
            <span className="daily-bar" style={{ height: `${heights[index]}%` }} />
          </span>
        ))}
      </div>
      {first && last && (
        <div className="daily-axis" aria-hidden="true">
          <span>{shortDay(first.date)}</span>
          <span>{shortDay(last.date)}</span>
        </div>
      )}
    </div>
  );
}
