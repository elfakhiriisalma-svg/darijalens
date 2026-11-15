/**
 * Résultats mesurés sur des données de test jamais vues pendant l'entraînement.
 * Sources : ml/reports/*.json et ml/reports/darijabert_sentiment_results.md.
 * Ces chiffres sont écrits ici à la main : à mettre à jour si on réentraîne un modèle.
 */

export interface ScriptScore {
  script: string;
  /** Nombre de textes de test. */
  n: number;
  /** F1 macro, entre 0 et 1. */
  simple?: number;
  bert?: number;
  /** Si vrai, trop peu de textes pour que le chiffre soit fiable. */
  fragile?: boolean;
}

export const SENTIMENT_SCORES: ScriptScore[] = [
  { script: "Arabe", n: 1731, simple: 0.845, bert: 0.861 },
  { script: "Latin (arabizi)", n: 662, simple: 0.719, bert: 0.811 },
  { script: "Mixte", n: 64, simple: 0.614, bert: 0.671, fragile: true },
];

export const OFFENSIVE_SCORES: ScriptScore[] = [
  { script: "Arabe", n: 0, simple: 0.832 },
  { script: "Latin (arabizi)", n: 0, simple: 0.9 },
  { script: "Mixte", n: 0, simple: 0.864 },
];

export const OFFENSIVE_OVERALL = 0.856;
/** Score d'un « modèle » qui ne regarde que l'écriture : sert de point de comparaison. */
export const OFFENSIVE_SCRIPT_ONLY = 0.58;

export const TRANSLITERATION = [
  { label: "Erreur par lettre", value: "11 %" },
  { label: "Phrases entièrement exactes", value: "22 %" },
  { label: "Mots faux", value: "33 %" },
];

export const CAVEATS: string[] = [
  "Les textes du corpus de sentiment contiennent beaucoup d'emojis. Les scores sont donc donnés sans emojis : avec, le modèle simple monterait à 0,92, ce qui serait trompeur.",
  "DarijaBERT : moyenne de deux entraînements pour l'arabe (0,859 et 0,863) et un seul pour l'arabizi. Le résultat varie d'environ 0,01 d'un entraînement à l'autre.",
  "Le groupe « Mixte » ne compte que 64 textes de test : ses scores sont indicatifs.",
  "Les étiquettes du corpus de langage offensant ont été produites par un modèle de langage, pas par des annotateurs humains.",
  "Les négations avec « ماشي » suivi d'un adjectif sont encore mal comprises, même par DarijaBERT.",
  "Le sentiment ne distingue que positif et négatif. Il n'y a pas encore de vraie classe neutre.",
];
