/** Formats renvoyés par l'API DarijaLens (voir apps/api/app/schemas.py). */

export interface ExplanationItem {
  feature: string;
  weight: number;
}

export interface AnalyzeResponse {
  script: "arabic" | "latin" | "mixed" | "unknown";
  arabic_letters: number;
  latin_letters: number;
  normalized_text: string;
  arabic_text: string;
}

export interface ClassifierResponse {
  label: number;
  name: string;
  score: number;
  explanation: ExplanationItem[];
}

export type TargetCode = "fr" | "en" | "ar" | "msa";

export interface TranslateResponse {
  translations: Partial<Record<TargetCode, string>>;
  source_used: string;
  transliterated: boolean;
}

/** Résultat d'un appel : soit les données, soit un message d'erreur lisible. */
export type Outcome<T> = { ok: true; data: T } | { ok: false; message: string };

export interface HistoryEntry {
  text: string;
  script: AnalyzeResponse["script"];
  sentiment: "positive" | "negative" | "uncertain" | null;
  sentiment_score: number | null;
  offensive: "offensive" | "non_offensive" | null;
  offensive_score: number | null;
}

export interface RecentAnalysis {
  id: number;
  created_at: string;
  text: string;
  script: string;
  sentiment: string | null;
  offensive: string | null;
}

export interface StatsResponse {
  total: number;
  sentiment: Record<string, number>;
  offensive: Record<string, number>;
  scripts: Record<string, number>;
  daily: { date: string; count: number }[];
  recent: RecentAnalysis[];
}
