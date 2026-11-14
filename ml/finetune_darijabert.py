"""Fine-tuning de DarijaBERT pour l'analyse de sentiment (corpus MYC), à lancer sur Kaggle (GPU).

Mêmes données, même découpage et mêmes règles que le modèle simple (TF-IDF)
de `train_sentiment.py` : la comparaison est donc équitable.
On mesure surtout le TEST SANS EMOJIS (voir `emoji_bias`).

Usage dans un notebook Kaggle (le dataset `darijalens-kaggle` étant branché) :
    # essai rapide (1 epoch, petit échantillon)
    run("SI2M-Lab/DarijaBERT", scripts={"arabic", "mixed"}, tag="arabic", quick=True)
    # vrai entraînement
    run("SI2M-Lab/DarijaBERT", scripts={"arabic", "mixed"}, tag="arabic")
    run("SI2M-Lab/DarijaBERT-arabizi", scripts={"latin"}, tag="latin")

Avec des phrases de négation en plus (voir `ml/data/negation_phrases.csv`) :
    run("SI2M-Lab/DarijaBERT", scripts={"arabic", "mixed"}, tag="arabic_neg",
        negation_csv="/kaggle/working/negation.csv")

Modèles : DarijaBERT et DarijaBERT-arabizi (Gaanoun, Naira, Allak, Benelallam, 2023).
"""

from __future__ import annotations

import csv
import glob
import inspect
import json
import os
import sys
from pathlib import Path

SEED = 42
EPOCHS = 3
LEARNING_RATE = 2e-5
BATCH_SIZE = 32
MAX_LENGTH = 128
OUTPUT_DIR = Path("/kaggle/working")

# Résultats du modèle simple (TF-IDF), test sans emojis, pour la comparaison finale.
BASELINE_MACRO_F1 = {"arabic": 0.845, "latin": 0.719, "mixed": 0.614}


def _find(pattern: str) -> Path:
    matches = glob.glob(pattern, recursive=True)
    if not matches:
        raise FileNotFoundError(f"Introuvable : {pattern} (le dataset est-il branché ?)")
    return Path(matches[0])


def _setup_paths() -> Path:
    code_dir = Path(os.environ.get("CODE_DIR") or _find("/kaggle/input/**/darijalens_nlp").parent)
    sys.path.insert(0, str(code_dir))
    return Path(os.environ.get("MYC_CSV") or _find("/kaggle/input/**/DATA_RAW.csv"))


def load_negation(path: str | Path):
    """Lit les phrases de négation. Une ligne sur quatre est gardée de côté pour le test.

    Retourne (phrases d'entraînement, phrases de test). Les phrases de test ne servent
    jamais à entraîner : elles mesurent si le modèle a vraiment appris la négation.
    """
    from darijalens_nlp.offensive import Example, preprocess
    from darijalens_nlp.script import detect_script

    with open(path, encoding="utf-8", newline="") as file:
        rows = list(csv.DictReader(file))
    train, holdout = [], []
    for index, row in enumerate(rows):
        text = preprocess(row["texte"])
        example = Example(text, int(row["label"]), detect_script(text).script.value)
        (holdout if index % 4 == 0 else train).append(example)
    return train, holdout


def prepare_data(
    scripts: set[str], negation_csv: str | None = None, negation_repeat: int = 3
) -> dict:
    """Prépare les données comme pour le modèle simple, puis garde les écritures demandées."""
    myc_csv = _setup_paths()
    from darijalens_nlp.offensive import clean_examples, split_examples
    from darijalens_nlp.sentiment import has_emoji, load_myc_rows, without_emojis

    examples, _ = clean_examples(load_myc_rows(myc_csv))
    train, validation, test = split_examples(examples)
    train = train + without_emojis([e for e in train if has_emoji(e.text)])

    def keep(items):
        return [e for e in items if e.script in scripts]

    data = {
        "train": keep(train),
        "validation": keep(without_emojis(validation)),
        "test": keep(test),
        "test_no_emoji": keep(without_emojis(test)),
    }
    if negation_csv:
        negation_train, negation_holdout = load_negation(negation_csv)
        data["train"] = data["train"] + negation_train * negation_repeat
        data["negation_holdout"] = negation_holdout
    return data


def _metrics(y_true, y_pred) -> dict:
    from sklearn.metrics import accuracy_score, f1_score

    return {
        "n": len(y_true),
        "accuracy": float(accuracy_score(y_true, y_pred)),
        "macro_f1": float(f1_score(y_true, y_pred, average="macro")),
    }


def run(
    model_name: str,
    scripts: set[str],
    tag: str,
    quick: bool = False,
    negation_csv: str | None = None,
    negation_repeat: int = 3,
) -> dict:
    """Fine-tune `model_name` sur les textes des écritures `scripts`, puis évalue sur le test."""
    import numpy as np
    import torch
    from transformers import (
        AutoModelForSequenceClassification,
        AutoTokenizer,
        DataCollatorWithPadding,
        Trainer,
        TrainingArguments,
        set_seed,
    )

    set_seed(SEED)
    data = prepare_data(scripts, negation_csv, negation_repeat)
    if quick:  # essai de 1 minute : petit échantillon, une seule époque
        data = {name: items[:300] for name, items in data.items()}
    print({name: len(items) for name, items in data.items()})

    tokenizer = AutoTokenizer.from_pretrained(model_name)
    model = AutoModelForSequenceClassification.from_pretrained(model_name, num_labels=2)

    class TextDataset(torch.utils.data.Dataset):
        def __init__(self, items):
            self.encodings = tokenizer(
                [e.text for e in items], truncation=True, max_length=MAX_LENGTH
            )
            self.labels = [e.label for e in items]

        def __len__(self):
            return len(self.labels)

        def __getitem__(self, index):
            item = {key: values[index] for key, values in self.encodings.items()}
            item["labels"] = self.labels[index]
            return item

    def compute_metrics(eval_prediction):
        logits, labels = eval_prediction
        return _metrics(labels, np.argmax(logits, axis=-1))

    parameters = inspect.signature(TrainingArguments.__init__).parameters
    settings = {
        "output_dir": str(OUTPUT_DIR / f"checkpoints_{tag}"),
        "num_train_epochs": 1 if quick else EPOCHS,
        "learning_rate": LEARNING_RATE,
        "per_device_train_batch_size": BATCH_SIZE,
        "per_device_eval_batch_size": 64,
        "weight_decay": 0.01,
        "save_strategy": "epoch",
        "load_best_model_at_end": True,
        "metric_for_best_model": "macro_f1",
        "greater_is_better": True,
        "save_total_limit": 1,
        "fp16": torch.cuda.is_available(),
        "seed": SEED,
        "report_to": "none",
        "logging_steps": 50,
    }
    settings["eval_strategy" if "eval_strategy" in parameters else "evaluation_strategy"] = "epoch"
    if "warmup_ratio" in parameters:
        settings["warmup_ratio"] = 0.1

    trainer = Trainer(
        model=model,
        args=TrainingArguments(**settings),
        train_dataset=TextDataset(data["train"]),
        eval_dataset=TextDataset(data["validation"]),
        data_collator=DataCollatorWithPadding(tokenizer),
        compute_metrics=compute_metrics,
    )
    trainer.train()

    def evaluate_on(trainer, items) -> dict:
        predictions = trainer.predict(TextDataset(items)).predictions.argmax(axis=-1)
        y_true = [e.label for e in items]
        result = _metrics(y_true, predictions)
        result["by_script"] = {}
        for script in sorted({e.script for e in items}):
            rows = [i for i, e in enumerate(items) if e.script == script]
            result["by_script"][script] = _metrics(
                [y_true[i] for i in rows], [int(predictions[i]) for i in rows]
            )
        return result

    report = {
        "model": model_name,
        "scripts": sorted(scripts),
        "quick_run": quick,
        "sizes": {name: len(items) for name, items in data.items()},
        "test": evaluate_on(trainer, data["test"]),
        "test_without_emojis": evaluate_on(trainer, data["test_no_emoji"]),
    }
    if "negation_holdout" in data:
        report["negation_holdout"] = evaluate_on(trainer, data["negation_holdout"])
    (OUTPUT_DIR / f"darijabert_{tag}_metrics.json").write_text(
        json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    if not quick:
        trainer.save_model(str(OUTPUT_DIR / f"darijabert_{tag}"))
        tokenizer.save_pretrained(str(OUTPUT_DIR / f"darijabert_{tag}"))

    print("\n=== RÉSULTAT (test sans emojis) ===")
    for script, metrics in report["test_without_emojis"]["by_script"].items():
        baseline = BASELINE_MACRO_F1.get(script)
        print(
            f"écriture {script:<7} n={metrics['n']:<5} "
            f"DarijaBERT F1 macro : {metrics['macro_f1']:.3f}"
            + (f"  | modèle simple : {baseline:.3f}" if baseline else "")
        )
    if "negation_holdout" in report:
        holdout = report["negation_holdout"]
        print(f"négation (jamais vue) n={holdout['n']} exactitude : {holdout['accuracy']:.3f}")
    del trainer, model
    torch.cuda.empty_cache()
    return report
