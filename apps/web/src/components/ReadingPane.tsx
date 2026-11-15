import { SCRIPT_LABELS } from "../lib/format";
import { highlight, intensity } from "../lib/highlight";
import type { AnalyzeResponse, ClassifierResponse, Outcome } from "../types";

export type Lens = "sentiment" | "offensive";

interface ReadingPaneProps {
  analysis: Outcome<AnalyzeResponse>;
  sentiment: Outcome<ClassifierResponse>;
  offensive: Outcome<ClassifierResponse>;
  lens: Lens;
  onLensChange: (lens: Lens) => void;
}

/** Le texte tel que le modèle l'a lu, avec les mots qui ont pesé dans la décision. */
export function ReadingPane({ analysis, sentiment, offensive, lens, onLensChange }: ReadingPaneProps) {
  if (!analysis.ok) {
    return (
      <div className="reading">
        <p className="problem on-dark" role="alert">
          {analysis.message}
        </p>
      </div>
    );
  }
  const { script, arabic_letters, latin_letters, normalized_text, arabic_text } = analysis.data;
  const totalLetters = arabic_letters + latin_letters;
  const arabicShare = totalLetters === 0 ? 0 : (arabic_letters / totalLetters) * 100;

  const chosen = lens === "sentiment" ? sentiment : offensive;
  const explanation = chosen.ok ? chosen.data.explanation : [];
  const pieces = highlight(normalized_text, explanation);
  // Pour le sentiment, un poids positif va vers « positif » ; pour l'offensif, vers « offensant ».
  const goodWhenPositive = lens === "sentiment";

  return (
    <div className="reading">
      <h2>Ce que le modèle a lu</h2>

      <div className="script-line">
        <span className="script-name">Écriture : {SCRIPT_LABELS[script]}</span>
        <span className="script-count">
          {arabic_letters} lettres arabes, {latin_letters} latines
        </span>
      </div>
      <div
        className="share-bar"
        role="img"
        aria-label={`${Math.round(arabicShare)} % de lettres arabes`}
      >
        <span style={{ width: `${arabicShare}%` }} />
      </div>

      <div className="lens-switch" role="group" aria-label="Mots à mettre en évidence">
        <button type="button" aria-pressed={lens === "sentiment"} onClick={() => onLensChange("sentiment")}>
          Mots du sentiment
        </button>
        <button type="button" aria-pressed={lens === "offensive"} onClick={() => onLensChange("offensive")}>
          Mots du langage offensant
        </button>
      </div>

      <p className="read-text" dir="auto">
        {pieces.map((piece, index) => {
          if (piece.weight === null) return <span key={index}>{piece.text}</span>;
          const good = piece.weight > 0 === goodWhenPositive;
          return (
            <mark
              key={index}
              className={good ? "word-good" : "word-bad"}
              style={{ ["--strength" as string]: intensity(piece.weight, pieces) }}
              title={`${piece.weight > 0 ? "+" : ""}${piece.weight.toFixed(2)}`}
            >
              {piece.text}
            </mark>
          );
        })}
      </p>
      <p className="legend">
        <span className="swatch word-good" /> pousse vers {goodWhenPositive ? "positif" : "non offensant"}
        <span className="swatch word-bad" /> pousse vers {goodWhenPositive ? "négatif" : "offensant"}
      </p>

      {arabic_text !== normalized_text && (
        <div className="arabic-version">
          <h3>En lettres arabes</h3>
          <p dir="rtl" lang="ar">
            {arabic_text}
          </p>
        </div>
      )}
    </div>
  );
}
