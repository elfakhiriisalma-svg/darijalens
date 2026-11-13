"""Entraîne et évalue le modèle de sentiment (positif / négatif) sur le corpus MYC.

Usage (depuis la racine du projet) :
    python ml/train_sentiment.py

Entrée  : data/raw/myc/DATA_RAW.csv
Sorties : models/sentiment.joblib          (modèle, non versionné)
          ml/reports/sentiment_metrics.json (résultats, versionnés)
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
    build_pipeline,
    clean_examples,
    evaluate,
    script_only_baseline,
    split_examples,
)
from darijalens_nlp.sentiment import (  # noqa: E402
    SENTIMENT_NAMES,
    SentimentClassifier,
    emoji_bias,
    has_emoji,
    load_myc_rows,
    without_emojis,
)

CANDIDATE_C = [0.5, 1.0, 2.0, 4.0, 8.0]


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--csv", type=Path, default=Path("data/raw/myc/DATA_RAW.csv"))
    parser.add_argument("--model", type=Path, default=Path("models/sentiment.joblib"))
    parser.add_argument("--report", type=Path, default=Path("ml/reports/sentiment_metrics.json"))
    args = parser.parse_args()

    examples, cleaning = clean_examples(load_myc_rows(args.csv))
    train, validation, test = split_examples(examples)
    print(
        f"Lus : {cleaning.read} | gardés : {cleaning.kept} | vides : {cleaning.empty} | "
        f"doublons : {cleaning.duplicates} | contradictoires : {cleaning.contradictory_texts}"
    )
    print(f"Entraînement : {len(train)} | validation : {len(validation)} | test : {len(test)}")

    bias = emoji_bias(examples)
    print(f"Étiquettes selon la présence d'emojis : {bias}")

    # Les emojis donnent un raccourci trop facile (voir `emoji_bias`). On entraîne donc aussi
    # sur des copies sans emojis, et on règle le modèle sur une validation SANS emojis :
    # c'est la mesure qui reflète le vrai signal du texte.
    train_texts = train + without_emojis([e for e in train if has_emoji(e.text)])
    validation_no_emoji = without_emojis(validation)
    test_no_emoji = without_emojis(test)

    validation_scores: dict[float, float] = {}
    for c in CANDIDATE_C:
        candidate = build_pipeline(c).fit(
            [e.text for e in train_texts], [e.label for e in train_texts]
        )
        validation_scores[c] = evaluate(candidate, validation_no_emoji, SENTIMENT_NAMES)["macro_f1"]
        print(f"  C = {c:<4} -> F1 macro validation (sans emojis) : {validation_scores[c]:.3f}")
    best_c = max(validation_scores, key=validation_scores.__getitem__)

    model = build_pipeline(best_c).fit(
        [e.text for e in train_texts], [e.label for e in train_texts]
    )
    test_metrics = evaluate(model, test, SENTIMENT_NAMES)
    test_no_emoji_metrics = evaluate(model, test_no_emoji, SENTIMENT_NAMES)
    baseline = script_only_baseline(train, test, SENTIMENT_NAMES)

    print(f"\nMeilleur C : {best_c}")
    print(f"TEST normal       - F1 macro : {test_metrics['macro_f1']:.3f} (gonflé par les emojis)")
    print(
        f"TEST SANS EMOJIS  - F1 macro : {test_no_emoji_metrics['macro_f1']:.3f} "
        f"| exactitude : {test_no_emoji_metrics['accuracy']:.3f}   <- mesure à retenir"
    )
    print(f"Base « écriture seule » - F1 macro : {baseline['macro_f1']:.3f}")
    for script, metrics in test_no_emoji_metrics["by_script"].items():
        print(
            f"  (sans emojis) écriture {script:<8} n={metrics['n']:<5} "
            f"F1 macro : {metrics['macro_f1']:.3f}"
        )

    SentimentClassifier(model).save(args.model)
    args.report.parent.mkdir(parents=True, exist_ok=True)
    report = {
        "seed": SEED,
        "scikit_learn": sklearn.__version__,
        "dataset": "MYC (Moroccan YouTube Corpus), DATA_RAW.csv",
        "cleaning": asdict(cleaning),
        "sizes": {"train": len(train), "validation": len(validation), "test": len(test)},
        "emoji_bias_in_dataset": bias,
        "validation_without_emojis_macro_f1_by_c": {
            str(c): s for c, s in validation_scores.items()
        },
        "best_c": best_c,
        "test": test_metrics,
        "test_without_emojis": test_no_emoji_metrics,
        "script_only_baseline_test": baseline,
    }
    args.report.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\nModèle : {args.model}\nRésultats : {args.report}")


if __name__ == "__main__":
    main()
