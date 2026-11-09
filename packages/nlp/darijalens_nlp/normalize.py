"""Normalisation de textes en darija (arabe, arabizi, mixte).

Chaque règle peut être activée ou désactivée séparément avec NormalizationConfig.
Cela permet de mesurer l'effet de chaque règle sur les modèles (étude d'ablation).

Choix de conception importants :
- La normalisation est prudente : on ne corrige pas l'orthographe et on ne devine pas
  les mots, car cela demande un lexique issu de vraies données.
- Les allongements sont réduits à `max_repeat` lettres (1 par défaut : « mzyaaaan » devient
  « mzyan »). Attention : cela abîme les doublons légitimes (« belle » devient « bele »).
  On peut passer max_repeat=2 pour les garder, ou None pour désactiver la règle.
- Les emojis sont conservés par défaut, car ils portent souvent le sentiment.
- Les données personnelles (liens, e-mails, mentions, téléphones) sont remplacées par des
  marqueurs, ce qui aide aussi à respecter l'anonymisation exigée par le cahier des charges.
"""

from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass

URL_TOKEN = "<url>"
EMAIL_TOKEN = "<email>"
USER_TOKEN = "<user>"
PHONE_TOKEN = "<phone>"

# Nombre maximal de fois qu'une même lettre peut se répéter d'affilée.
DEFAULT_MAX_REPEAT = 1

_URL = re.compile(r"(?:https?://|www\.)\S*[^\s.,;:!?)\]}»]", re.IGNORECASE)
_EMAIL = re.compile(r"[\w.+-]+@[\w-]+(?:\.[\w-]+)+")
_USER = re.compile(r"(?<![\w.])@\w+")
# Numéros marocains : 06 12 34 56 78, 0612345678, +212 6 12 34 56 78, 00212612345678.
_PHONE = re.compile(r"(?<!\d)(?:(?:\+|00)212[\s.-]?|0)[5-7](?:[\s.-]?\d){8}(?!\d)")

_PUNCTUATION_RUN = re.compile(r"([!?.,;:،؛؟\-])\1+")

# Caractères invisibles ou de contrôle de direction du texte, sans valeur pour l'analyse.
_INVISIBLE = {
    0x00AD,  # trait d'union conditionnel
    0x200B,  # espace de largeur nulle
    0x200C,  # antiliant de largeur nulle
    0x200E,  # marque gauche-droite
    0x200F,  # marque droite-gauche
    0xFEFF,  # marque d'ordre des octets
    *range(0x202A, 0x202F),  # contrôles de direction
    *range(0x2066, 0x206A),  # isolats de direction
}
_INVISIBLE_TABLE = dict.fromkeys(_INVISIBLE)

# Voyelles courtes (harakat), signe de gémination, petit alef et tatwil (allongement graphique).
_ARABIC_MARKS = {*range(0x064B, 0x0660), 0x0670, 0x0640}
_ARABIC_VARIANTS = {
    "أ": "ا",
    "إ": "ا",
    "آ": "ا",
    "ٱ": "ا",
    "ى": "ي",
    "ی": "ي",  # ya persan
    "ک": "ك",  # kaf persan
}
_ARABIC_TABLE = {
    **dict.fromkeys(_ARABIC_MARKS),
    **{ord(source): target for source, target in _ARABIC_VARIANTS.items()},
}


@dataclass(frozen=True)
class NormalizationConfig:
    """Règles de normalisation à appliquer. Tout est activé par défaut, sauf les emojis."""

    unicode_normalize: bool = True
    convert_digits: bool = True
    remove_invisible: bool = True
    lowercase: bool = True
    mask_private: bool = True
    normalize_arabic: bool = True
    remove_emojis: bool = False
    max_repeat: int | None = DEFAULT_MAX_REPEAT
    collapse_punctuation: bool = True
    collapse_whitespace: bool = True

    def __post_init__(self) -> None:
        if self.max_repeat is not None and self.max_repeat < 1:
            raise ValueError("max_repeat doit être au moins 1, ou None pour désactiver")


DEFAULT_CONFIG = NormalizationConfig()


def _convert_digits(text: str) -> str:
    """Convertit les chiffres arabo-indiens et persans (٠-٩, ۰-۹) en chiffres 0-9."""
    return "".join(
        str(unicodedata.decimal(char)) if char.isdecimal() and not char.isascii() else char
        for char in text
    )


def _mask_private(text: str) -> str:
    """Remplace liens, e-mails, mentions et téléphones par des marqueurs."""
    text = _URL.sub(URL_TOKEN, text)
    text = _EMAIL.sub(EMAIL_TOKEN, text)
    text = _USER.sub(USER_TOKEN, text)
    return _PHONE.sub(PHONE_TOKEN, text)


def _remove_emojis(text: str) -> str:
    """Retire les symboles (emojis, pictogrammes) et leurs liants invisibles."""
    return "".join(
        char
        for char in text
        if unicodedata.category(char) not in {"So", "Sk"} and char not in {"‍", "️"}
    )


def _collapse_repeats(text: str, max_repeat: int) -> str:
    """Réduit toute lettre répétée plus de max_repeat fois. Les chiffres ne sont pas touchés."""
    pattern = re.compile(rf"([^\W\d_])\1{{{max_repeat},}}")
    return pattern.sub(lambda match: match.group(1) * max_repeat, text)


def normalize_text(text: str, config: NormalizationConfig = DEFAULT_CONFIG) -> str:
    """Nettoie un texte selon la configuration donnée.

    Args:
        text: le texte brut.
        config: les règles à appliquer.

    Returns:
        Le texte normalisé.

    Raises:
        TypeError: si text n'est pas une chaîne de caractères.
    """
    if not isinstance(text, str):
        raise TypeError(f"text doit être une chaîne, reçu : {type(text).__name__}")

    if config.unicode_normalize:
        text = unicodedata.normalize("NFKC", text)
    if config.convert_digits:
        text = _convert_digits(text)
    if config.remove_invisible:
        text = text.translate(_INVISIBLE_TABLE)
    if config.lowercase:
        text = text.lower()
    if config.mask_private:
        text = _mask_private(text)
    if config.normalize_arabic:
        text = text.translate(_ARABIC_TABLE)
    if config.remove_emojis:
        text = _remove_emojis(text)
    if config.max_repeat is not None:
        text = _collapse_repeats(text, config.max_repeat)
    if config.collapse_punctuation:
        text = _PUNCTUATION_RUN.sub(r"\1", text)
    if config.collapse_whitespace:
        text = " ".join(text.split())
    return text
