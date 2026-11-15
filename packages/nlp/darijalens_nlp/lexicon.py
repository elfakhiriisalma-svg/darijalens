"""Dictionnaire mot à mot arabizi -> arabe, appris sur des phrases alignées (corpus DODa).

Les règles de `arabizi.py` devinent l'orthographe arabe lettre par lettre et se trompent sur
des détails fréquents (« hbiba » donne حبيبا au lieu de حبيبة, « lkhedma » donne لخدما au lieu de
الخدمة). Un dictionnaire des mots déjà vus, avec leur écriture arabe humaine, corrige ces cas.
Les mots inconnus restent traités par les règles.
"""

from __future__ import annotations

import json
import re
from collections import Counter, defaultdict
from collections.abc import Iterable
from functools import lru_cache
from importlib import resources

from darijalens_nlp.normalize import NormalizationConfig, normalize_text

LEXICON_FILE = "data/arabizi_lexicon.json"

# On garde les lettres doublées (« الله », « للمدرسة ») : seul le nettoyage de base est appliqué.
_KEEP_DOUBLES = NormalizationConfig(max_repeat=None)
_NOT_WORD = re.compile(r"[^\w\s]")


def split_words(text: str) -> list[str]:
    """Texte nettoyé, sans ponctuation, découpé en mots."""
    return _NOT_WORD.sub(" ", normalize_text(text, _KEEP_DOUBLES)).split()


def aligned_pairs(latin: str, arabic: str) -> list[tuple[str, str]]:
    """Associe les mots d'une phrase latine à ceux de sa version arabe.

    Si les deux phrases n'ont pas le même nombre de mots, l'alignement est incertain :
    on ne retourne rien plutôt que de risquer des paires fausses.
    """
    latin_words, arabic_words = split_words(latin), split_words(arabic)
    if len(latin_words) != len(arabic_words):
        return []
    return [
        (source.lower(), target)
        for source, target in zip(latin_words, arabic_words, strict=True)
        if source.isascii() and not source.isdigit() and not target.isascii()
    ]


def build_lexicon(
    pairs: Iterable[tuple[str, str]], min_count: int = 2, min_share: float = 0.6
) -> dict[str, str]:
    """Garde, pour chaque mot latin, son écriture arabe la plus fréquente.

    Args:
        pairs: couples (mot latin, mot arabe).
        min_count: nombre minimal d'occurrences du mot latin (évite les hasards).
        min_share: part minimale de l'écriture la plus fréquente (évite les mots ambigus).
    """
    counts: dict[str, Counter[str]] = defaultdict(Counter)
    for source, target in pairs:
        counts[source][target] += 1
    lexicon: dict[str, str] = {}
    for source, targets in counts.items():
        total = sum(targets.values())
        best, best_count = targets.most_common(1)[0]
        if total >= min_count and best_count / total >= min_share:
            lexicon[source] = best
    return dict(sorted(lexicon.items()))


@lru_cache
def default_lexicon() -> dict[str, str]:
    """Dictionnaire fourni avec la bibliothèque, ou un dictionnaire vide s'il est absent."""
    try:
        content = resources.files("darijalens_nlp").joinpath(LEXICON_FILE).read_text("utf-8")
    except (FileNotFoundError, OSError):
        return {}
    data = json.loads(content)
    return data if isinstance(data, dict) else {}
