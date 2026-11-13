"""Analyse de sentiment (positif / négatif) : modèle de référence sur le corpus MYC.

Réutilise tout le dispositif du détecteur de langage offensant (nettoyage, découpage sans
fuite, TF-IDF + régression logistique, explication), avec d'autres noms de classes.
Le score est la probabilité que le texte soit POSITIF.

Corpus MYC (Moroccan YouTube Corpus) : commentaires YouTube en arabe et en arabizi, annotés
« positif » (1) ou « négatif » (-1) par cinq locuteurs natifs. Dans ce module, le négatif
devient la classe 0 et le positif la classe 1.
"""

from __future__ import annotations

import csv
import io
import unicodedata
from collections import Counter
from collections.abc import Sequence
from pathlib import Path

from darijalens_nlp.normalize import NormalizationConfig, normalize_text
from darijalens_nlp.offensive import Example, OffensiveClassifier

SENTIMENT_NAMES = {0: "negative", 1: "positive"}
_MYC_LABELS = {"-1": 0, "1": 1}
_WITHOUT_EMOJIS = NormalizationConfig(remove_emojis=True)


def load_myc_rows(path: Path) -> list[tuple[str, int]]:
    """Lit DATA_RAW.csv de MYC et retourne (texte, étiquette 0 ou 1).

    Le fichier est en UTF-16 et chaque ligne est un seul champ « texte,étiquette ».
    Les lignes mal formées (étiquette absente ou inconnue) sont ignorées.
    """
    content = Path(path).read_text(encoding="utf-16")
    rows: list[tuple[str, int]] = []
    for index, record in enumerate(csv.reader(io.StringIO(content, newline=""))):
        if index == 0 or len(record) != 1 or "," not in record[0]:
            continue
        text, _, raw_label = record[0].rpartition(",")
        label = _MYC_LABELS.get(raw_label.strip())
        if label is not None and text.strip():
            rows.append((text.strip(), label))
    return rows


class SentimentClassifier(OffensiveClassifier):
    """Modèle de sentiment : même mécanique, classes « negative » et « positive »."""

    label_names = SENTIMENT_NAMES


def has_emoji(text: str) -> bool:
    """Vrai si le texte contient au moins un emoji ou pictogramme."""
    return any(unicodedata.category(char) in {"So", "Sk"} for char in text)


def without_emojis(examples: Sequence[Example]) -> list[Example]:
    """Copie des exemples dont les emojis sont retirés (les textes devenus vides disparaissent)."""
    stripped = (
        Example(normalize_text(e.text, _WITHOUT_EMOJIS), e.label, e.script) for e in examples
    )
    return [e for e in stripped if e.text]


def emoji_bias(examples: Sequence[Example]) -> dict[str, dict[str, int]]:
    """Compte les étiquettes selon la présence d'emojis.

    Dans MYC, presque tous les textes sans emoji sont négatifs : un modèle peut donc réussir
    en partie grâce à ce seul indice. On le mesure pour pouvoir le dire dans le rapport.
    """
    result: dict[str, Counter[str]] = {"with_emoji": Counter(), "without_emoji": Counter()}
    for example in examples:
        group = "with_emoji" if has_emoji(example.text) else "without_emoji"
        result[group][SENTIMENT_NAMES[example.label]] += 1
    return {group: dict(counts) for group, counts in result.items()}
