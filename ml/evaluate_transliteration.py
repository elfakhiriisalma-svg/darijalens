"""Mesure la qualité de la transcription arabizi -> arabe sur DODa.

Usage (depuis la racine du projet) :
    python ml/evaluate_transliteration.py
    python ml/evaluate_transliteration.py --examples 10

Le fichier attendu a les colonnes `darija` (arabizi) et `darija_ar` (référence en arabe).
La référence et la sortie passent par la même normalisation, et la ponctuation est ignorée :
on mesure la transcription des lettres, pas le style de ponctuation.
"""

from __future__ import annotations

import argparse
import csv
import random
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "packages" / "nlp"))

from darijalens_nlp import (  # noqa: E402
    character_error_rate,
    normalize_text,
    transliterate_arabizi,
)

DEFAULT_CSV = Path("data/raw/doda/sentences/sentences.csv")
HOLDOUT_EVERY = 5  # une phrase sur cinq est gardée de côté (voir build_lexicon.py)
_NOT_WORD = re.compile(r"[^\w\s]")


def _clean(text: str) -> str:
    return " ".join(_NOT_WORD.sub("", normalize_text(text)).split())


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--csv", type=Path, default=DEFAULT_CSV, help="fichier sentences.csv")
    parser.add_argument("--examples", type=int, default=5, help="nombre d'exemples affichés")
    parser.add_argument(
        "--holdout",
        action="store_true",
        help="n'évalue que les phrases NON utilisées pour construire le dictionnaire",
    )
    parser.add_argument(
        "--rules-only", action="store_true", help="ignore le dictionnaire (règles seules)"
    )
    args = parser.parse_args()

    with args.csv.open(encoding="utf-8", newline="") as file:
        rows = list(csv.DictReader(file))
    if args.holdout:
        rows = [row for index, row in enumerate(rows) if index % HOLDOUT_EVERY == 0]
    lexicon = {} if args.rules_only else None

    sources = [row["darija"] for row in rows]
    references = [_clean(row["darija_ar"]) for row in rows]
    hypotheses = [_clean(transliterate_arabizi(normalize_text(text), lexicon)) for text in sources]

    cer = character_error_rate(references, hypotheses)
    exact = sum(ref == hyp for ref, hyp in zip(references, hypotheses, strict=True))

    aligned_words = wrong_words = 0
    for ref, hyp in zip(references, hypotheses, strict=True):
        ref_words, hyp_words = ref.split(), hyp.split()
        if len(ref_words) == len(hyp_words):
            aligned_words += len(ref_words)
            wrong_words += sum(r != h for r, h in zip(ref_words, hyp_words, strict=True))

    print(f"Phrases évaluées                 : {len(rows)}")
    print(f"CER (erreur par caractère)       : {cer:.1%}")
    print(f"Phrases parfaitement transcrites : {exact / len(rows):.1%}")
    print(f"Mots faux (phrases alignées)     : {wrong_words / aligned_words:.1%}")

    if args.examples > 0:
        print("\nExemples tirés au hasard (source | référence | sortie) :")
        rng = random.Random(1)
        for index in rng.sample(range(len(rows)), min(args.examples, len(rows))):
            print(f"  {sources[index]} | {references[index]} | {hypotheses[index]}")


if __name__ == "__main__":
    main()
