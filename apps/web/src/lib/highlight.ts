import type { ExplanationItem } from "../types";

export interface Piece {
  text: string;
  /** Poids du mot dans la décision (positif : pousse vers la classe 1), ou null s'il n'a pas pesé. */
  weight: number | null;
}

const EDGE_PUNCTUATION = /^[^\p{L}\p{N}]+|[^\p{L}\p{N}]+$/gu;

/** Retire la ponctuation autour d'un mot : « بزاف، » devient « بزاف ». */
export function coreOf(token: string): string {
  return token.replace(EDGE_PUNCTUATION, "");
}

/**
 * Garde, parmi les éléments d'explication, ceux qui sont un mot entier.
 * Les morceaux de mots (« ش »), les débuts et fins de mots, et les paires de mots sont ignorés.
 */
export function wholeWordWeights(explanation: ExplanationItem[]): Map<string, number> {
  const weights = new Map<string, number>();
  for (const { feature, weight } of explanation) {
    const word = feature.trim();
    if (!word || /\s/.test(word)) continue;
    const spaceBefore = feature.startsWith(" ");
    const spaceAfter = feature.endsWith(" ");
    if (spaceBefore !== spaceAfter) continue;
    weights.set(word, (weights.get(word) ?? 0) + weight);
  }
  return weights;
}

/** Découpe le texte en morceaux (mots et espaces) et indique le poids de chaque mot. */
export function highlight(text: string, explanation: ExplanationItem[]): Piece[] {
  const weights = wholeWordWeights(explanation);
  return text
    .split(/(\s+)/)
    .filter((part) => part !== "")
    .map((part) => {
      const weight = /^\s+$/.test(part) ? undefined : weights.get(coreOf(part));
      return { text: part, weight: weight ?? null };
    });
}

/** Intensité entre 0,25 et 1 d'un poids, par rapport au plus grand poids du texte. */
export function intensity(weight: number, pieces: Piece[]): number {
  const largest = Math.max(...pieces.map((piece) => Math.abs(piece.weight ?? 0)), 1e-9);
  return 0.25 + 0.75 * Math.min(Math.abs(weight) / largest, 1);
}
