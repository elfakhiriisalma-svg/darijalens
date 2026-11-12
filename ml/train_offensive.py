"""Entraîne et évalue le détecteur de langage offensant.

Usage (depuis la racine du projet) :
    python ml/train_offensive.py

Entrée  : data/raw/offensive/DarLoad_Dataset.csv (colonnes `text` et `label`)
Sorties : models/offensive.joblib       (modèle, non versionné)
          ml/reports/offensive_metrics.json (résultats, versionnés)
"""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import asdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "packages" / "nlp"))

import sklearn  # noqa: E402

from darijalens_nlp.offensive import (  # noqa: E402
    SEED,
    OffensiveClassifier,
    build_pipeline,
    clean_examples,
    evaluate,
    load_rows,
    script_only_baseline,
    split_examples,
)

CANDIDATE_C = [0.5, 1.0, 2.0, 4.0, 8.0]


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--csv", type=Path, default=Path("data/raw/offensive/DarLoad_Dataset.csv"))
    parser.add_argument("--model", type=Path, default=Path("models/offensive.joblib"))
    parser.add_argument("--report", type=Path, default=Path("ml/reports/offensive_metrics.json"))
    args = parser.parse_args()

    examples, cleaning = clean_examples(load_rows(args.csv))
    train, validation, test = split_examples(examples)
    print(
        f"Lus : {cleaning.read} | gardés : {cleaning.kept} | "
        f"vides : {cleaning.empty} | doublons : {cleaning.duplicates} | "
        f"contradictoires : {cleaning.contradictory_texts}"
    )
    print(f"Entraînement : {len(train)} | validation : {len(validation)} | test : {len(test)}")

    # Réglage sur la VALIDATION uniquement : le test reste intact.
    validation_scores: dict[float, float] = {}
    for c in CANDIDATE_C:
        candidate = build_pipeline(c).fit([e.text for e in train], [e.label for e in train])
        validation_scores[c] = evaluate(candidate, validation)["macro_f1"]
        print(f"  C = {c:<4} -> F1 macro validation : {validation_scores[c]:.3f}")
    best_c = max(validation_scores, key=validation_scores.__getitem__)

    model = build_pipeline(best_c).fit([e.text for e in train], [e.label for e in train])
    test_metrics = evaluate(model, test)
    baseline = script_only_baseline(train, test)

    print(f"\nMeilleur C : {best_c}")
    print(
        f"TEST - exactitude : {test_metrics['accuracy']:.3f} | "
        f"F1 macro : {test_metrics['macro_f1']:.3f}"
    )
    print(f"Base « écriture seule » - F1 macro : {baseline['macro_f1']:.3f}")
    for script, metrics in test_metrics["by_script"].items():
        print(f"  écriture {script:<8} n={metrics['n']:<5} F1 macro : {metrics['macro_f1']:.3f}")

    OffensiveClassifier(model).save(args.model)
    args.report.parent.mkdir(parents=True, exist_ok=True)
    report = {
        "seed": SEED,
        "scikit_learn": sklearn.__version__,
        "cleaning": asdict(cleaning),
        "sizes": {"train": len(train), "validation": len(validation), "test": len(test)},
        "validation_macro_f1_by_c": {str(c): s for c, s in validation_scores.items()},
        "best_c": best_c,
        "test": test_metrics,
        "script_only_baseline_test": baseline,
    }
    args.report.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\nModèle : {args.model}\nRésultats : {args.report}")


if __name__ == "__main__":
    main()
