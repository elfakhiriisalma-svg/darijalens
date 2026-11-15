export interface SegmentSpec {
  key: string;
  label: string;
  tone: "positive" | "negative" | "uncertain" | "neutral" | "blue" | "saffron" | "faint";
}

export interface Segment extends SegmentSpec {
  count: number;
  /** Part du total, entre 0 et 1 (0 si le total est nul). */
  share: number;
}

/** Associe à chaque catégorie son nombre et sa part du total. */
export function toSegments(counts: Record<string, number>, specs: SegmentSpec[]): Segment[] {
  const total = specs.reduce((sum, spec) => sum + (counts[spec.key] ?? 0), 0);
  return specs.map((spec) => {
    const count = counts[spec.key] ?? 0;
    return { ...spec, count, share: total === 0 ? 0 : count / total };
  });
}

/** Pourcentage arrondi, par exemple « 38 % ». */
export const asPercent = (share: number): string => `${Math.round(share * 100)} %`;

/** Largeur de barre (0 à 100) d'un jour par rapport au jour le plus actif. */
export function barHeights(counts: number[]): number[] {
  const largest = Math.max(...counts, 0);
  return counts.map((count) => (largest === 0 ? 0 : Math.max((count / largest) * 100, count > 0 ? 6 : 0)));
}

const MONTHS = ["janv.", "févr.", "mars", "avr.", "mai", "juin", "juil.", "août", "sept.", "oct.", "nov.", "déc."];

/** « 2026-11-15 » devient « 15 nov. ». */
export function shortDay(isoDay: string): string {
  const [, month, day] = isoDay.split("-").map(Number);
  return `${day} ${MONTHS[(month ?? 1) - 1]}`;
}
