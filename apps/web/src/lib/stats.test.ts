import { describe, expect, it } from "vitest";
import { asPercent, barHeights, shortDay, toSegments } from "./stats";

const SPECS = [
  { key: "positive", label: "Positif", tone: "positive" as const },
  { key: "negative", label: "Négatif", tone: "negative" as const },
  { key: "uncertain", label: "Incertain", tone: "uncertain" as const },
];

describe("toSegments", () => {
  it("calcule la part de chaque catégorie", () => {
    const segments = toSegments({ positive: 3, negative: 1 }, SPECS);
    expect(segments.map((s) => s.count)).toEqual([3, 1, 0]);
    expect(segments[0]?.share).toBeCloseTo(0.75);
    expect(segments[2]?.share).toBe(0);
  });

  it("ne divise pas par zéro quand il n'y a rien", () => {
    expect(toSegments({}, SPECS).every((s) => s.share === 0)).toBe(true);
  });
});

describe("asPercent", () => {
  it("arrondit", () => {
    expect(asPercent(0.376)).toBe("38 %");
    expect(asPercent(0)).toBe("0 %");
  });
});

describe("barHeights", () => {
  it("met le jour le plus actif à 100 et garde une barre visible aux petits jours", () => {
    expect(barHeights([0, 1, 50, 100])).toEqual([0, 6, 50, 100]);
  });

  it("renvoie 0 partout s'il n'y a eu aucune analyse", () => {
    expect(barHeights([0, 0, 0])).toEqual([0, 0, 0]);
  });
});

describe("shortDay", () => {
  it("écrit le jour et le mois en français", () => {
    expect(shortDay("2026-11-15")).toBe("15 nov.");
    expect(shortDay("2026-01-03")).toBe("3 janv.");
  });
});
