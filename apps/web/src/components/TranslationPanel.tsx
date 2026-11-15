import { useState } from "react";
import { TARGETS } from "../lib/format";
import type { Outcome, TargetCode, TranslateResponse } from "../types";

interface TranslationPanelProps {
  selected: TargetCode[];
  onSelectedChange: (targets: TargetCode[]) => void;
  onTranslate: () => void;
  loading: boolean;
  canTranslate: boolean;
  outcome: Outcome<TranslateResponse> | null;
}

export function TranslationPanel({
  selected,
  onSelectedChange,
  onTranslate,
  loading,
  canTranslate,
  outcome,
}: TranslationPanelProps) {
  const [copied, setCopied] = useState<TargetCode | null>(null);

  const toggle = (code: TargetCode) =>
    onSelectedChange(selected.includes(code) ? selected.filter((c) => c !== code) : [...selected, code]);

  const copy = async (code: TargetCode, text: string) => {
    try {
      await navigator.clipboard.writeText(text);
      setCopied(code);
      window.setTimeout(() => setCopied(null), 1500);
    } catch {
      setCopied(null);
    }
  };

  return (
    <section className="result translation" aria-label="Traduction">
      <h2>Traduction</h2>
      <p className="question">Que dit ce texte dans une autre langue ou un autre alphabet ?</p>

      <fieldset className="targets">
        <legend className="visually-hidden">Langues de sortie</legend>
        {TARGETS.map((target) => (
          <label key={target.code} className={selected.includes(target.code) ? "chip on" : "chip"}>
            <input
              type="checkbox"
              checked={selected.includes(target.code)}
              onChange={() => toggle(target.code)}
            />
            <span>{target.label}</span>
          </label>
        ))}
      </fieldset>

      <button
        type="button"
        className="button secondary"
        onClick={onTranslate}
        disabled={loading || !canTranslate || selected.length === 0}
      >
        {loading ? "Traduction en cours…" : "Traduire"}
      </button>
      {loading && (
        <p className="note" role="status">
          La première traduction peut durer plusieurs minutes : le modèle se télécharge puis se charge.
        </p>
      )}

      {outcome && !outcome.ok && (
        <p className="problem" role="alert">
          {outcome.message}
        </p>
      )}

      {outcome?.ok && (
        <>
          <ul className="translations">
            {TARGETS.filter((target) => outcome.data.translations[target.code] !== undefined).map((target) => {
              const text = outcome.data.translations[target.code] ?? "";
              return (
                <li key={target.code}>
                  <div className="translation-head">
                    <span>{target.label}</span>
                    <button type="button" className="link" onClick={() => copy(target.code, text)}>
                      {copied === target.code ? "Copié" : "Copier"}
                    </button>
                  </div>
                  <p
                    className={target.rtl ? "translated arabic" : "translated"}
                    dir={target.rtl ? "rtl" : "ltr"}
                    lang={target.rtl ? "ar" : target.code}
                  >
                    {text}
                  </p>
                </li>
              );
            })}
          </ul>
          {outcome.data.transliterated && (
            <p className="note">
              Le texte latin a d'abord été transcrit en arabe avant la traduction :{" "}
              <span dir="rtl" lang="ar" className="inline-arabic">
                {outcome.data.source_used}
              </span>
              . Une erreur de transcription peut se retrouver dans la traduction.
            </p>
          )}
        </>
      )}
    </section>
  );
}
