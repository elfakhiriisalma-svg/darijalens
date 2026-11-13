"""Détection de langage offensant : modèle de référence (baseline) TF-IDF + régression logistique.

Ce module n'est volontairement pas importé par `darijalens_nlp/__init__.py` : il demande
scikit-learn, alors que le reste de la bibliothèque n'a aucune dépendance.

Principes retenus :
- Les doublons et les textes aux étiquettes contradictoires sont retirés AVANT le découpage,
  pour qu'un même texte ne se retrouve jamais à la fois dans l'entraînement et dans le test.
- Le test n'est utilisé qu'une seule fois, à la fin. Le réglage se fait sur la validation.
- On compare toujours le modèle à une base trop simple (deviner d'après l'écriture seule),
  pour savoir s'il apprend autre chose qu'un raccourci.
- Le modèle est linéaire : on peut expliquer chaque prédiction par les mots et suites de
  lettres qui ont pesé dans la décision.

Sécurité : `OffensiveClassifier.load` utilise joblib (pickle). Ne chargez que des modèles
que vous avez vous-même entraînés, jamais un fichier reçu d'une source inconnue.
"""

from __future__ import annotations

import csv
import re
from collections import Counter, defaultdict
from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import joblib
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, confusion_matrix, precision_recall_fscore_support
from sklearn.model_selection import train_test_split
from sklearn.pipeline import FeatureUnion, Pipeline

from darijalens_nlp.normalize import normalize_text
from darijalens_nlp.script import detect_script

LABEL_NAMES = {0: "non_offensive", 1: "offensive"}
SEED = 42

# Dans le jeu de données, les emojis sont remplacés par une description entre astérisques.
_ASTERISKS = re.compile(r"\*+")
# Une combinaison (étiquette, écriture) trop rare est regroupée pour pouvoir stratifier.
_MIN_STRATUM_SIZE = 10


def preprocess(text: str) -> str:
    """Prépare un texte pour le modèle (astérisques retirées, puis normalisation)."""
    return normalize_text(_ASTERISKS.sub(" ", text))


@dataclass(frozen=True)
class Example:
    """Un texte déjà préparé, avec son étiquette (0 ou 1) et son écriture."""

    text: str
    label: int
    script: str


@dataclass(frozen=True)
class CleaningReport:
    """Ce qui a été retiré du jeu de données, pour pouvoir le citer dans le rapport."""

    read: int
    empty: int
    duplicates: int
    contradictory_texts: int
    kept: int


def load_rows(path: Path) -> list[tuple[str, int]]:
    """Lit le fichier CSV (colonnes `text` et `label`) et retourne (texte, étiquette)."""
    with Path(path).open(encoding="utf-8", newline="") as file:
        return [(row["text"], int(row["label"])) for row in csv.DictReader(file)]


def clean_examples(rows: Sequence[tuple[str, int]]) -> tuple[list[Example], CleaningReport]:
    """Prépare les textes, retire les vides, les doublons et les textes contradictoires."""
    prepared = [(preprocess(text), label) for text, label in rows]
    non_empty = [(text, label) for text, label in prepared if text]

    labels_by_text: dict[str, set[int]] = defaultdict(set)
    for text, label in non_empty:
        labels_by_text[text].add(label)

    contradictory = {text for text, labels in labels_by_text.items() if len(labels) > 1}
    seen: set[str] = set()
    kept: list[Example] = []
    duplicates = 0
    for text, label in non_empty:
        if text in contradictory:
            continue
        if text in seen:
            duplicates += 1
            continue
        seen.add(text)
        kept.append(Example(text, label, detect_script(text).script.value))

    report = CleaningReport(
        read=len(rows),
        empty=len(prepared) - len(non_empty),
        duplicates=duplicates,
        contradictory_texts=len(contradictory),
        kept=len(kept),
    )
    return kept, report


def split_examples(
    examples: Sequence[Example],
    seed: int = SEED,
    validation_size: float = 0.15,
    test_size: float = 0.15,
) -> tuple[list[Example], list[Example], list[Example]]:
    """Découpe en entraînement / validation / test, en gardant les proportions."""
    strata = [f"{e.label}-{e.script}" for e in examples]
    counts = Counter(strata)
    keys = [s if counts[s] >= _MIN_STRATUM_SIZE else s.split("-")[0] for s in strata]

    train_val, test, keys_train_val, _ = train_test_split(
        list(examples), keys, test_size=test_size, random_state=seed, stratify=keys
    )
    relative_validation = validation_size / (1 - test_size)
    train, validation = train_test_split(
        train_val, test_size=relative_validation, random_state=seed, stratify=keys_train_val
    )
    return list(train), list(validation), list(test)


def build_pipeline(c: float = 4.0) -> Pipeline:
    """Mots + suites de lettres, pondérés par TF-IDF, puis régression logistique."""
    words = TfidfVectorizer(analyzer="word", ngram_range=(1, 2), min_df=2, sublinear_tf=True)
    letters = TfidfVectorizer(analyzer="char_wb", ngram_range=(2, 5), min_df=3, sublinear_tf=True)
    features = FeatureUnion([("word", words), ("char", letters)])
    classifier = LogisticRegression(C=c, max_iter=1000, solver="liblinear")
    return Pipeline([("features", features), ("classifier", classifier)])


def _metrics(
    y_true: Sequence[int], y_pred: Sequence[int], label_names: dict[int, str] = LABEL_NAMES
) -> dict[str, Any]:
    precision, recall, f1, support = precision_recall_fscore_support(
        y_true, y_pred, labels=[0, 1], zero_division=0
    )
    return {
        "n": len(y_true),
        "accuracy": float(accuracy_score(y_true, y_pred)),
        "macro_f1": float(np.mean(f1)),
        "per_class": {
            label_names[i]: {
                "precision": float(precision[i]),
                "recall": float(recall[i]),
                "f1": float(f1[i]),
                "support": int(support[i]),
            }
            for i in (0, 1)
        },
        "confusion_matrix": confusion_matrix(y_true, y_pred, labels=[0, 1]).tolist(),
    }


def evaluate(
    model: Pipeline, examples: Sequence[Example], label_names: dict[int, str] = LABEL_NAMES
) -> dict[str, Any]:
    """Mesure globale, puis séparément pour chaque écriture (arabe, latin, mixte...)."""
    y_true = [e.label for e in examples]
    y_pred = model.predict([e.text for e in examples]).tolist()
    result = _metrics(y_true, y_pred, label_names)
    by_script: dict[str, Any] = {}
    for script in sorted({e.script for e in examples}):
        indexes = [i for i, e in enumerate(examples) if e.script == script]
        by_script[script] = _metrics(
            [y_true[i] for i in indexes], [y_pred[i] for i in indexes], label_names
        )
    result["by_script"] = by_script
    return result


def script_only_baseline(
    train: Sequence[Example],
    test: Sequence[Example],
    label_names: dict[int, str] = LABEL_NAMES,
) -> dict[str, Any]:
    """Base trop simple : prédire, pour chaque écriture, l'étiquette la plus fréquente.

    Si le modèle ne fait pas nettement mieux, c'est qu'il apprend un raccourci.
    """
    labels_by_script: dict[str, Counter[int]] = defaultdict(Counter)
    for example in train:
        labels_by_script[example.script][example.label] += 1
    overall = Counter(e.label for e in train).most_common(1)[0][0]
    rule = {script: counts.most_common(1)[0][0] for script, counts in labels_by_script.items()}
    y_pred = [rule.get(e.script, overall) for e in test]
    return _metrics([e.label for e in test], y_pred, label_names)


@dataclass(frozen=True)
class Prediction:
    """Résultat d'une prédiction."""

    label: int
    name: str
    score: float  # probabilité de la classe 1 (offensant, ou positif), entre 0 et 1


class OffensiveClassifier:
    """Modèle entraîné, avec prédiction, explication, sauvegarde et chargement."""

    label_names: dict[int, str] = LABEL_NAMES

    def __init__(self, pipeline: Pipeline) -> None:
        self.pipeline = pipeline

    def predict(self, text: str) -> Prediction:
        score = float(self.pipeline.predict_proba([preprocess(text)])[0][1])
        label = int(score >= 0.5)
        return Prediction(label=label, name=self.label_names[label], score=score)

    def explain(self, text: str, top_k: int = 5) -> list[tuple[str, float]]:
        """Les éléments du texte qui ont le plus pesé : positif = vers « offensant »."""
        features = self.pipeline.named_steps["features"]
        coefficients = self.pipeline.named_steps["classifier"].coef_[0]
        row = features.transform([preprocess(text)])
        contributions = row.multiply(coefficients).tocoo()
        names = features.get_feature_names_out()
        pairs = [
            (str(names[col]).split("__", 1)[-1], float(value))
            for col, value in zip(contributions.col, contributions.data, strict=True)
        ]
        pairs.sort(key=lambda pair: abs(pair[1]), reverse=True)
        return pairs[:top_k]

    def save(self, path: Path) -> None:
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        joblib.dump(self.pipeline, path)

    @classmethod
    def load(cls, path: Path) -> OffensiveClassifier:
        return cls(joblib.load(path))
