"""Bibliothèque de traitement automatique de la darija écrite."""

from darijalens_nlp.arabizi import transliterate_arabizi
from darijalens_nlp.metrics import character_error_rate, edit_distance
from darijalens_nlp.normalize import DEFAULT_CONFIG, NormalizationConfig, normalize_text
from darijalens_nlp.script import Script, ScriptResult, detect_script

__all__ = [
    "DEFAULT_CONFIG",
    "NormalizationConfig",
    "Script",
    "ScriptResult",
    "character_error_rate",
    "detect_script",
    "edit_distance",
    "normalize_text",
    "transliterate_arabizi",
]
