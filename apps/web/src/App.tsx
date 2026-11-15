import { useEffect, useState } from "react";
import { API_URL, addHistory, analyze, checkHealth, offensive, sentiment, translate } from "./api";
import { Brand, Nav, type View } from "./components/Brand";
import { Dashboard } from "./components/Dashboard";
import { ReadingPane, type Lens } from "./components/ReadingPane";
import { ResultSection } from "./components/ResultSection";
import { Spectrum } from "./components/Spectrum";
import { TranslationPanel } from "./components/TranslationPanel";
import { offensiveVerdict, sentimentVerdict, toHistoryEntry } from "./lib/format";
import { SAMPLES } from "./samples";
import type {
  AnalyzeResponse,
  ClassifierResponse,
  Outcome,
  TargetCode,
  TranslateResponse,
} from "./types";

const MAX_LENGTH = 5000;

interface Analysis {
  text: string;
  analysis: Outcome<AnalyzeResponse>;
  sentiment: Outcome<ClassifierResponse>;
  offensive: Outcome<ClassifierResponse>;
}

type ApiStatus = "checking" | "up" | "down";

export function App() {
  const [text, setText] = useState("");
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<Analysis | null>(null);
  const [lens, setLens] = useState<Lens>("sentiment");
  const [targets, setTargets] = useState<TargetCode[]>(["fr", "en"]);
  const [translating, setTranslating] = useState(false);
  const [translation, setTranslation] = useState<Outcome<TranslateResponse> | null>(null);
  const [apiStatus, setApiStatus] = useState<ApiStatus>("checking");
  const [view, setView] = useState<View>(() =>
    window.location.hash === "#/dashboard" ? "dashboard" : "analysis",
  );

  useEffect(() => {
    window.history.replaceState(null, "", view === "dashboard" ? "#/dashboard" : window.location.pathname);
  }, [view]);

  useEffect(() => {
    checkHealth().then((outcome) => setApiStatus(outcome.ok ? "up" : "down"));
  }, []);

  const trimmed = text.trim();

  async function runAnalysis() {
    if (!trimmed || loading) return;
    setLoading(true);
    const [analysisOutcome, sentimentOutcome, offensiveOutcome] = await Promise.all([
      analyze(trimmed),
      sentiment(trimmed),
      offensive(trimmed),
    ]);
    setResult({
      text: trimmed,
      analysis: analysisOutcome,
      sentiment: sentimentOutcome,
      offensive: offensiveOutcome,
    });
    setApiStatus(analysisOutcome.ok || sentimentOutcome.ok || offensiveOutcome.ok ? "up" : "down");
    const entry = toHistoryEntry(trimmed, analysisOutcome, sentimentOutcome, offensiveOutcome);
    if (entry) void addHistory(entry); // l'historique est un plus : une erreur ne bloque pas l'analyse
    setTranslation(null);
    setLoading(false);
  }

  async function runTranslation() {
    if (!trimmed || translating || targets.length === 0) return;
    setTranslating(true);
    setTranslation(await translate(trimmed, targets));
    setTranslating(false);
  }

  if (view === "dashboard") {
    return (
      <div className="dash-shell">
        <header className="dash-header">
          <Brand />
          <Nav view={view} onChange={setView} />
        </header>
        <Dashboard onGoToAnalysis={() => setView("analysis")} />
      </div>
    );
  }

  return (
    <div className="layout">
      <main className="lens-panel">
        <header className="brand">
          <Brand />
          <Nav view={view} onChange={setView} />
        </header>

        <div className="input-block">
          <h1>Collez un texte en darija</h1>
          <p className="intro">En lettres arabes, en arabizi (3jebni) ou un mélange des deux.</p>

          <label htmlFor="text" className="visually-hidden">
            Texte à analyser
          </label>
          <textarea
            id="text"
            dir="auto"
            value={text}
            maxLength={MAX_LENGTH}
            placeholder="Écrivez ou collez votre texte ici"
            onChange={(event) => setText(event.target.value)}
            onKeyDown={(event) => {
              if ((event.ctrlKey || event.metaKey) && event.key === "Enter") void runAnalysis();
            }}
          />
          <div className="input-foot">
            <div className="samples">
              <span>Essayer avec</span>
              {SAMPLES.map((sample) => (
                <button key={sample.text} type="button" className="chip-light" onClick={() => setText(sample.text)}>
                  {sample.label}
                </button>
              ))}
            </div>
            <span className="count">
              {text.length} / {MAX_LENGTH}
            </span>
          </div>

          <div className="actions">
            <button type="button" className="button primary" onClick={() => void runAnalysis()} disabled={!trimmed || loading}>
              {loading ? "Analyse en cours…" : "Analyser"}
            </button>
            {text && (
              <button
                type="button"
                className="button ghost"
                onClick={() => {
                  setText("");
                  setResult(null);
                  setTranslation(null);
                }}
              >
                Effacer
              </button>
            )}
          </div>
        </div>

        {result && (
          <ReadingPane
            analysis={result.analysis}
            sentiment={result.sentiment}
            offensive={result.offensive}
            lens={lens}
            onLensChange={setLens}
          />
        )}
      </main>

      <aside className="results-panel">
        <div className={`api-status ${apiStatus}`} role="status">
          <span className="dot" />
          {apiStatus === "checking" && "Connexion à l'API…"}
          {apiStatus === "up" && "API connectée"}
          {apiStatus === "down" && `API injoignable (${API_URL})`}
        </div>

        {!result ? (
          <div className="empty">
            <h2>Les résultats s'affichent ici</h2>
            <p>
              Écrivez un texte à gauche, puis cliquez sur Analyser (ou Ctrl+Entrée). Vous verrez le sentiment, le
              langage offensant et les mots qui ont pesé dans la décision.
            </p>
            <p>La traduction se lance à part, car le modèle est plus lent.</p>
          </div>
        ) : (
          <>
            <ResultSection
              title="Sentiment"
              question="Le texte est-il positif ou négatif ?"
              outcome={result.sentiment}
              verdict={sentimentVerdict}
            >
              {(data) => (
                <Spectrum
                  score={data.score}
                  ariaLabel={`Score de sentiment : ${data.score.toFixed(2)} sur 1`}
                  zones={[
                    { from: 0, to: 0.4, tone: "negative" },
                    { from: 0.4, to: 0.6, tone: "uncertain" },
                    { from: 0.6, to: 1, tone: "positive" },
                  ]}
                  ticks={[
                    { at: 0, label: "Négatif" },
                    { at: 0.5, label: "Doute" },
                    { at: 1, label: "Positif" },
                  ]}
                />
              )}
            </ResultSection>

            <ResultSection
              title="Langage offensant"
              question="Le texte contient-il des insultes ou des propos agressifs ?"
              outcome={result.offensive}
              verdict={offensiveVerdict}
            >
              {(data) => (
                <Spectrum
                  score={data.score}
                  ariaLabel={`Score de langage offensant : ${data.score.toFixed(2)} sur 1`}
                  zones={[
                    { from: 0, to: 0.5, tone: "positive" },
                    { from: 0.5, to: 1, tone: "negative" },
                  ]}
                  ticks={[
                    { at: 0, label: "Non offensant" },
                    { at: 1, label: "Offensant" },
                  ]}
                />
              )}
            </ResultSection>

            <TranslationPanel
              selected={targets}
              onSelectedChange={setTargets}
              onTranslate={() => void runTranslation()}
              loading={translating}
              canTranslate={Boolean(trimmed)}
              outcome={translation}
            />

            <details className="limits">
              <summary>Limites connues</summary>
              <ul>
                <li>Le sentiment ne distingue que positif et négatif ; la zone de doute signale un texte ambigu.</li>
                <li>Certaines négations sont mal comprises, surtout « ماشي » suivi d'un adjectif.</li>
                <li>Le texte en arabizi est transcrit par des règles : des erreurs d'orthographe sont possibles.</li>
              </ul>
            </details>
          </>
        )}
      </aside>
    </div>
  );
}
