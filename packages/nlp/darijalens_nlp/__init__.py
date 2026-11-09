"""Bibliothèque de traitement automatique de la darija écrite."""

from darijalens_nlp.arabizi import transliterate_arabizi
from darijalens_nlp.normalize import DEFAULT_CONFIG, NormalizationConfig, normalize_text
from darijalens_nlp.script import Script, ScriptResult, detect_script

__all__ = [
    "DEFAULT_CONFIG",
    "NormalizationConfig",
    "Script",
    "ScriptResult",
    "detect_script",
    "normalize_text",
    "transliterate_arabizi",
]
