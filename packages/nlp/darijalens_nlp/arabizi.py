"""Transcription de l'arabizi (darija en lettres latines et chiffres) vers l'écriture arabe.

C'est une version de départ à base de règles (« baseline »). Elle sert de point de comparaison :
on mesurera ses erreurs sur de vrais exemples avant de la remplacer par un modèle appris.

Règles principales :
- Les chiffres de l'arabizi sont des lettres : 3 = ع, 7 = ح, 9 = ق, 5 = خ, 6 = ط, 8 = غ, 2 = ء.
- Des groupes de lettres donnent une seule lettre arabe : ch = ش, kh = خ, gh = غ, ou = و.
- Les voyelles : a = ا, i = ي, o/u = و ; le « e » à l'intérieur d'un mot est ignoré ;
  au début d'un mot, toute voyelle devient ا.
- Les nombres (deux chiffres ou plus) ne sont jamais transformés.
- Un mot avec une lettre accentuée (é, è, à...) est vu comme français : il reste tel quel.

Limites connues, volontairement non cachées :
- Une lettre latine peut correspondre à plusieurs lettres arabes
  (s = س ou ص, t = ت ou ط, d = د ou ض). On choisit toujours la plus fréquente.
- Les mots français ou anglais écrits sans accent (« merci », « ok ») sont transcrits comme
  s'ils étaient de la darija. Il faudra identifier la langue des mots pour les éviter.
"""

from __future__ import annotations

import re

_WORD = re.compile(r"[0-9A-Za-zÀ-ÖØ-öø-ÿ'’]+")
_MASK = re.compile(r"<(?:url|email|user|phone)>")

_DIGITS = {"2": "ء", "3": "ع", "5": "خ", "6": "ط", "7": "ح", "8": "غ", "9": "ق"}
# Chiffre suivi d'une apostrophe : 3' = غ, 7' = خ.
_APOSTROPHE_DIGITS = {"3": "غ", "7": "خ"}

_FIXED_GROUPS = {
    "ch": "ش",
    "sh": "ش",
    "kh": "خ",
    "gh": "غ",
    "ou": "و",
    "oo": "و",
    "uu": "و",
    "aa": "ا",
    "ee": "ي",
    "ii": "ي",
}

_CONSONANTS = {
    "b": "ب", "t": "ت", "j": "ج", "d": "د", "r": "ر", "z": "ز", "s": "س", "f": "ف",
    "q": "ق", "k": "ك", "l": "ل", "m": "م", "n": "ن", "h": "ه", "w": "و", "y": "ي",
    "g": "ڭ", "p": "ب", "v": "ف", "c": "ك", "x": "كس",
}  # fmt: skip

_VOWELS = set("aeiou")
_APOSTROPHES = {"'", "’"}
_REPEATED_ARABIC = re.compile(r"([ء-ي])\1+")

# Types d'éléments d'un mot : lettre fixe, voyelle à décider, texte à conserver tel quel.
_FIXED, _VOWEL, _KEEP = "fixed", "vowel", "keep"


def _split_word(word: str) -> list[tuple[str, str]]:
    """Découpe un mot en éléments (type, valeur)."""
    has_letter = any(char.isalpha() for char in word)
    items: list[tuple[str, str]] = []
    i = 0
    while i < len(word):
        char = word[i]
        if char.isdigit():
            j = i
            while j < len(word) and word[j].isdigit():
                j += 1
            run = word[i:j]
            followed_by_apostrophe = j < len(word) and word[j] in _APOSTROPHES
            if len(run) >= 2 or not has_letter:
                items.append((_KEEP, run))
            elif followed_by_apostrophe and run in _APOSTROPHE_DIGITS:
                items.append((_FIXED, _APOSTROPHE_DIGITS[run]))
                j += 1
            elif run in _DIGITS:
                items.append((_FIXED, _DIGITS[run]))
            else:
                items.append((_KEEP, run))
            i = j
            continue
        pair = word[i : i + 2]
        if pair in _FIXED_GROUPS:
            items.append((_FIXED, _FIXED_GROUPS[pair]))
            i += 2
        elif char in _VOWELS:
            items.append((_VOWEL, char))
            i += 1
        elif char in _CONSONANTS:
            items.append((_FIXED, _CONSONANTS[char]))
            i += 1
        elif char in _APOSTROPHES:
            i += 1
        else:
            items.append((_KEEP, char))
            i += 1
    return items


def _resolve_vowel(vowel: str, is_first: bool) -> str:
    if is_first:
        return "ا"
    if vowel == "a":
        return "ا"
    if vowel == "i":
        return "ي"
    if vowel in {"o", "u"}:
        return "و"
    return ""  # « e » à l'intérieur ou à la fin d'un mot : ignoré


def _transliterate_word(word: str) -> str:
    lowered = word.lower()
    if not lowered.isascii():
        return word  # lettre accentuée : probablement du français
    pieces = []
    for index, (kind, value) in enumerate(_split_word(lowered)):
        pieces.append(_resolve_vowel(value, index == 0) if kind == _VOWEL else value)
    return _REPEATED_ARABIC.sub(r"\1", "".join(pieces))


def transliterate_arabizi(text: str) -> str:
    """Transcrit en arabe les mots écrits en lettres latines et chiffres.

    Les mots déjà en arabe, la ponctuation, les emojis et les marqueurs
    (<url>, <email>, <user>, <phone>) ne sont pas modifiés.

    Args:
        text: le texte, de préférence déjà normalisé.

    Returns:
        Le texte dont les mots latins ont été transcrits.

    Raises:
        TypeError: si text n'est pas une chaîne de caractères.
    """
    if not isinstance(text, str):
        raise TypeError(f"text doit être une chaîne, reçu : {type(text).__name__}")

    def convert(chunk: str) -> str:
        return _WORD.sub(lambda match: _transliterate_word(match.group()), chunk)

    result = []
    position = 0
    for mask in _MASK.finditer(text):
        result.append(convert(text[position : mask.start()]))
        result.append(mask.group())
        position = mask.end()
    result.append(convert(text[position:]))
    return "".join(result)
