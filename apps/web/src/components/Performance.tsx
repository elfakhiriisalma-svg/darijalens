import {
  CAVEATS,
  OFFENSIVE_OVERALL,
  OFFENSIVE_SCORES,
  OFFENSIVE_SCRIPT_ONLY,
  SENTIMENT_SCORES,
  TRANSLITERATION,
  type ScriptScore,
} from "../data/performance";

const f1 = (value: number) => value.toFixed(2).replace(".", ",");

function Bar({ label, value, kind }: { label: string; value: number; kind: "simple" | "bert" }) {
  return (
    <div className="perf-row">
      <span className="perf-name">{label}</span>
      <span className="perf-track">
        <span className={`perf-fill perf-${kind}`} style={{ width: `${value * 100}%` }} />
      </span>
      <span className="perf-value">{f1(value)}</span>
    </div>
  );
}

function ScoreGroup({ score, simpleLabel }: { score: ScriptScore; simpleLabel: string }) {
  return (
    <li className="perf-group">
      <div className="perf-group-head">
        <span>{score.script}</span>
        {score.n > 0 && (
          <small>
            {score.n} textes de test{score.fragile ? " : peu fiable" : ""}
          </small>
        )}
      </div>
      {score.simple !== undefined && <Bar label={simpleLabel} value={score.simple} kind="simple" />}
      {score.bert !== undefined && <Bar label="DarijaBERT" value={score.bert} kind="bert" />}
    </li>
  );
}

/** Résultats des modèles sur des données de test, avec leurs limites. */
export function Performance() {
  return (
    <section className="dash-section" aria-labelledby="perf-title">
      <h2 id="perf-title">Performance des modèles</h2>
      <p className="dash-intro">
        Mesurée sur des textes que les modèles n'ont jamais vus. Le score est le F1 macro : 1 serait parfait, 0,5
        correspond presque au hasard pour deux classes.
      </p>

      <div className="perf-grid">
        <div>
          <h3>Sentiment</h3>
          <ul className="perf-list">
            {SENTIMENT_SCORES.map((score) => (
              <ScoreGroup key={score.script} score={score} simpleLabel="Modèle simple" />
            ))}
          </ul>
        </div>

        <div>
          <h3>Langage offensant</h3>
          <ul className="perf-list">
            {OFFENSIVE_SCORES.map((score) => (
              <ScoreGroup key={score.script} score={score} simpleLabel="Modèle simple" />
            ))}
          </ul>
          <p className="perf-note">
            Ensemble : {f1(OFFENSIVE_OVERALL)}. Un « modèle » qui ne regarde que l'écriture obtient seulement{" "}
            {f1(OFFENSIVE_SCRIPT_ONLY)}, donc le modèle lit bien le contenu.
          </p>
        </div>

        <div>
          <h3>Transcription de l'arabizi en arabe</h3>
          <dl className="stat-list">
            {TRANSLITERATION.map((item) => (
              <div key={item.label}>
                <dt>{item.label}</dt>
                <dd>{item.value}</dd>
              </div>
            ))}
          </dl>
          <p className="perf-note">Mesurée sur les phrases du corpus DODa, écrites par des humains.</p>
        </div>
      </div>

      <h3 className="caveats-title">À savoir avant de lire ces chiffres</h3>
      <ul className="caveats">
        {CAVEATS.map((caveat) => (
          <li key={caveat}>{caveat}</li>
        ))}
      </ul>
    </section>
  );
}
