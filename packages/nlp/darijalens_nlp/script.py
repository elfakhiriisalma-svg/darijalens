"""Détection de l'écriture (arabe, latin, mixte) d'un texte.

On compte les lettres de chaque écriture grâce à leur nom Unicode.
Les chiffres (3, 7, 9 de l'arabizi), la ponctuation et les emojis ne sont pas comptés :
ils n'appartiennent à aucune écriture en particulier.
"""

from __future__ import annotations

import unicodedata
from dataclasses import dataclass
from enum import StrEnum

# Part minimale de lettres de la seconde écriture pour parler de texte "mixte".
# En dessous, on considère que l'autre écriture est négligeable (ex. un "ok" isolé).
MIXED_THRESHOLD = 0.10


class Script(StrEnum):
    """Écritures reconnues."""

    ARABIC = "arabic"
    LATIN = "latin"
    MIXED = "mixed"
    UNKNOWN = "unknown"


@dataclass(frozen=True)
class ScriptResult:
    """Résultat de la détection, avec les détails du calcul."""

    script: Script
    arabic_letters: int
    latin_letters: int

    @property
    def total_letters(self) -> int:
        return self.arabic_letters + self.latin_letters

    @property
    def arabic_ratio(self) -> float:
        return self.arabic_letters / self.total_letters if self.total_letters else 0.0

    @property
    def latin_ratio(self) -> float:
        return self.latin_letters / self.total_letters if self.total_letters else 0.0


def _letter_script(char: str) -> Script | None:
    """Retourne l'écriture d'une lettre arabe ou latine, sinon None."""
    if not char.isalpha():
        return None
    name = unicodedata.name(char, "")
    if name.startswith("ARABIC"):
        return Script.ARABIC
    if name.startswith("LATIN"):
        return Script.LATIN
    return None


def detect_script(text: str, mixed_threshold: float = MIXED_THRESHOLD) -> ScriptResult:
    """Détecte l'écriture dominante d'un texte.

    Args:
        text: le texte à analyser.
        mixed_threshold: part minimale (entre 0 et 0,5) de la seconde écriture
            pour que le texte soit déclaré "mixte".

    Returns:
        Un ScriptResult. Le script vaut UNKNOWN s'il n'y a aucune lettre arabe ni latine.

    Raises:
        TypeError: si text n'est pas une chaîne de caractères.
        ValueError: si mixed_threshold est hors de l'intervalle [0, 0,5].
    """
    if not isinstance(text, str):
        raise TypeError(f"text doit être une chaîne, reçu : {type(text).__name__}")
    if not 0 <= mixed_threshold <= 0.5:
        raise ValueError("mixed_threshold doit être compris entre 0 et 0,5")

    arabic = latin = 0
    for char in text:
        found = _letter_script(char)
        if found is Script.ARABIC:
            arabic += 1
        elif found is Script.LATIN:
            latin += 1

    total = arabic + latin
    if total == 0:
        script = Script.UNKNOWN
    else:
        arabic_ratio = arabic / total
        latin_ratio = latin / total
        if arabic_ratio > mixed_threshold and latin_ratio > mixed_threshold:
            script = Script.MIXED
        elif arabic >= latin:
            script = Script.ARABIC
        else:
            script = Script.LATIN

    return ScriptResult(script=script, arabic_letters=arabic, latin_letters=latin)
