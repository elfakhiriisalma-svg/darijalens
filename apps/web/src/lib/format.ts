import type { AnalyzeResponse, ClassifierResponse, HistoryEntry, Outcome, TargetCode } from "../types";

export const SCRIPT_LABELS: Record<AnalyzeResponse["script"], string> = {
  arabic: "Arabe",
  latin: "Latin (arabizi)",
  mixed: "Mixte",
  unknown: "Inconnue",
};

export const TARGETS: { code: TargetCode; label: string; hint: string; rtl: boolean }[] = [
  { code: "fr", label: "Français", hint: "Traduction", rtl: false },
  { code: "en", label: "Anglais", hint: "Traduction", rtl: false },
  { code: "ar", label: "Darija en lettres arabes", hint: "Même phrase, autre alphabet", rtl: true },
  { code: "msa", label: "Arabe standard", hint: "Traduction", rtl: true },
];

export const percent = (value: number): string => `${Math.round(value * 100)} %`;

export interface Verdict {
  title: string;
  detail: string;
  tone: "positive" | "negative" | "uncertain";
}

/** Phrase de résultat du sentiment. `score` est la probabilité d'être positif. */
export function sentimentVerdict(result: ClassifierResponse): Verdict {
  const { name, score } = result;
  if (name === "uncertain") {
    return {
      title: "Incertain",
      detail: `Le modèle hésite : score de ${score.toFixed(2)} sur 1.`,
      tone: "uncertain",
    };
  }
  if (name === "positive") {
    return { title: "Positif", detail: `${percent(score)} de probabilité d'être positif.`, tone: "positive" };
  }
  return { title: "Négatif", detail: `${percent(1 - score)} de probabilité d'être négatif.`, tone: "negative" };
}

/** Phrase de résultat du langage offensant. `score` est la probabilité d'être offensant. */
export function offensiveVerdict(result: ClassifierResponse): Verdict {
  const { name, score } = result;
  if (name === "offensive") {
    return { title: "Offensant", detail: `${percent(score)} de probabilité d'être offensant.`, tone: "negative" };
  }
  return {
    title: "Non offensant",
    detail: `${percent(1 - score)} de probabilité de ne pas être offensant.`,
    tone: "positive",
  };
}

/** Prépare la ligne d'historique d'une analyse, ou null si rien n'est à enregistrer. */
export function toHistoryEntry(
  text: string,
  analysis: Outcome<AnalyzeResponse>,
  sentiment: Outcome<ClassifierResponse>,
  offensive: Outcome<ClassifierResponse>,
): HistoryEntry | null {
  if (!analysis.ok || (!sentiment.ok && !offensive.ok)) return null;
  const sentimentName = sentiment.ok ? sentiment.data.name : null;
  const offensiveName = offensive.ok ? offensive.data.name : null;
  return {
    text,
    script: analysis.data.script,
    sentiment:
      sentimentName === "positive" || sentimentName === "negative" || sentimentName === "uncertain"
        ? sentimentName
        : null,
    sentiment_score: sentiment.ok ? sentiment.data.score : null,
    offensive: offensiveName === "offensive" || offensiveName === "non_offensive" ? offensiveName : null,
    offensive_score: offensive.ok ? offensive.data.score : null,
  };
}
