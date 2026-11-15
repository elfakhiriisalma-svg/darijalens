"""Construit le dictionnaire arabizi -> arabe à partir des phrases alignées de DODa.

Usage (depuis la racine du projet) :
    python ml/build_lexicon.py

Une phrase sur cinq est gardée de côté et ne sert PAS à construire le dictionnaire :
elle permet de mesurer honnêtement le gain avec
    python ml/evaluate_transliteration.py --holdout --rules-only
    python ml/evaluate_transliteration.py --holdout
"""

from __future__ import annotations

import argparse
import csv
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "packages" / "nlp"))

from darijalens_nlp.lexicon import LEXICON_FILE, aligned_pairs, build_lexicon  # noqa: E402

DEFAULT_CSV = Path("data/raw/doda/sentences/sentences.csv")
HOLDOUT_EVERY = 5
OUTPUT = Path("packages/nlp/darijalens_nlp") / LEXICON_FILE


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--csv", type=Path, default=DEFAULT_CSV)
    parser.add_argument("--min-count", type=int, default=2)
    parser.add_argument("--min-share", type=float, default=0.6)
    args = parser.parse_args()

    with args.csv.open(encoding="utf-8", newline="") as file:
        rows = list(csv.DictReader(file))

    pairs: list[tuple[str, str]] = []
    for index, row in enumerate(rows):
        if index % HOLDOUT_EVERY == 0:
            continue  # phrase gardée de côté pour l'évaluation
        pairs.extend(aligned_pairs(row["darija"], row["darija_ar"]))

    lexicon = build_lexicon(pairs, args.min_count, args.min_share)
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(json.dumps(lexicon, ensure_ascii=False, indent=0), encoding="utf-8")
    print(f"{len(pairs)} paires de mots, {len(lexicon)} mots dans le dictionnaire -> {OUTPUT}")


if __name__ == "__main__":
    main()
