import { useCallback, useEffect, useState } from "react";
import { clearHistory, getStats } from "../api";
import { asPercent, toSegments, type SegmentSpec } from "../lib/stats";
import type { Outcome, StatsResponse } from "../types";
import { DailyChart } from "./DailyChart";
import { Performance } from "./Performance";
import { StackedBar } from "./StackedBar";

const SENTIMENT_SPECS: SegmentSpec[] = [
  { key: "positive", label: "Positif", tone: "positive" },
  { key: "negative", label: "Négatif", tone: "negative" },
  { key: "uncertain", label: "Incertain", tone: "uncertain" },
];

const OFFENSIVE_SPECS: SegmentSpec[] = [
  { key: "non_offensive", label: "Non offensant", tone: "positive" },
  { key: "offensive", label: "Offensant", tone: "negative" },
];

const SCRIPT_SPECS: SegmentSpec[] = [
  { key: "arabic", label: "Arabe", tone: "blue" },
  { key: "latin", label: "Latin (arabizi)", tone: "saffron" },
  { key: "mixed", label: "Mixte", tone: "neutral" },
  { key: "unknown", label: "Inconnue", tone: "faint" },
];

const SENTIMENT_NAMES: Record<string, string> = { positive: "Positif", negative: "Négatif", uncertain: "Incertain" };
const OFFENSIVE_NAMES: Record<string, string> = { offensive: "Offensant", non_offensive: "Non offensant" };
const SCRIPT_NAMES: Record<string, string> = { arabic: "Arabe", latin: "Latin", mixed: "Mixte", unknown: "Inconnue" };

function when(iso: string): string {
  return new Date(iso).toLocaleString("fr-FR", { day: "numeric", month: "short", hour: "2-digit", minute: "2-digit" });
}

interface DashboardProps {
  onGoToAnalysis: () => void;
}

export function Dashboard({ onGoToAnalysis }: DashboardProps) {
  const [stats, setStats] = useState<Outcome<StatsResponse> | null>(null);
  const [confirming, setConfirming] = useState(false);

  const load = useCallback(async () => {
    setStats(await getStats());
  }, []);

  useEffect(() => {
    void load();
  }, [load]);

  async function erase() {
    setConfirming(false);
    await clearHistory();
    await load();
  }

  return (
    <main className="dash">
      <h1>Tableau de bord</h1>

      <section className="dash-section" aria-labelledby="usage-title">
        <div className="dash-head">
          <h2 id="usage-title">Vos analyses</h2>
          <div className="dash-actions">
            <button type="button" className="link" onClick={() => void load()}>
              Actualiser
            </button>
            {stats?.ok && stats.data.total > 0 &&
              (confirming ? (
                <>
                  <button type="button" className="link danger" onClick={() => void erase()}>
                    Confirmer l'effacement
                  </button>
                  <button type="button" className="link" onClick={() => setConfirming(false)}>
                    Annuler
                  </button>
                </>
              ) : (
                <button type="button" className="link" onClick={() => setConfirming(true)}>
                  Effacer l'historique
                </button>
              ))}
          </div>
        </div>

        {stats === null && <p className="dash-intro">Chargement…</p>}

        {stats && !stats.ok && (
          <p className="problem" role="alert">
            {stats.message}
          </p>
        )}

        {stats?.ok && stats.data.total === 0 && (
          <div className="dash-empty">
            <p>Aucune analyse enregistrée pour l'instant.</p>
            <button type="button" className="button secondary" onClick={onGoToAnalysis}>
              Analyser un texte
            </button>
          </div>
        )}

        {stats?.ok && stats.data.total > 0 && (
          <>
            <div className="usage-top">
              <div className="big-number">
                <span className="big-value">{stats.data.total}</span>
                <span className="big-label">{stats.data.total > 1 ? "textes analysés" : "texte analysé"}</span>
                <span className="big-sub">
                  dont {asPercent(
                    (stats.data.sentiment.negative ?? 0) / Math.max(1, stats.data.total),
                  )}{" "}
                  jugés négatifs
                </span>
              </div>
              <DailyChart daily={stats.data.daily} />
            </div>

            <div className="usage-bars">
              <StackedBar title="Sentiment" segments={toSegments(stats.data.sentiment, SENTIMENT_SPECS)} />
              <StackedBar title="Langage offensant" segments={toSegments(stats.data.offensive, OFFENSIVE_SPECS)} />
              <StackedBar title="Écriture des textes" segments={toSegments(stats.data.scripts, SCRIPT_SPECS)} />
            </div>

            <h3 className="recent-title">Dernières analyses</h3>
            <div className="table-wrap">
              <table className="recent">
                <thead>
                  <tr>
                    <th scope="col">Quand</th>
                    <th scope="col">Texte</th>
                    <th scope="col">Écriture</th>
                    <th scope="col">Sentiment</th>
                    <th scope="col">Langage offensant</th>
                  </tr>
                </thead>
                <tbody>
                  {stats.data.recent.map((row) => (
                    <tr key={row.id}>
                      <td className="when">{when(row.created_at)}</td>
                      <td className="text-cell" dir="auto">
                        {row.text}
                      </td>
                      <td>{SCRIPT_NAMES[row.script] ?? row.script}</td>
                      <td>
                        {row.sentiment ? (
                          <span className={`pill pill-${row.sentiment}`}>{SENTIMENT_NAMES[row.sentiment]}</span>
                        ) : (
                          "—"
                        )}
                      </td>
                      <td>
                        {row.offensive ? (
                          <span className={`pill pill-${row.offensive}`}>{OFFENSIVE_NAMES[row.offensive]}</span>
                        ) : (
                          "—"
                        )}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
            <p className="privacy">
              Les textes sont gardés dans la base de données de l'API (300 caractères au maximum chacun). Ne saisissez
              pas de données personnelles.
            </p>
          </>
        )}
      </section>

      <Performance />
    </main>
  );
}
