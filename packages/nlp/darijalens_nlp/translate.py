"""Traduction de la darija vers le français et l'anglais (modèle NLLB-200 pré-entraîné).

Le modèle est chargé à la première demande. `torch`, `transformers` et `sentencepiece` ne sont
importés qu'à ce moment-là : le reste de la bibliothèque marche sans eux.

Limite : le texte en arabizi est d'abord transcrit en arabe par nos règles (CER 11 %),
puis traduit. Les erreurs de transcription se retrouvent donc dans la traduction.
"""

from __future__ import annotations

import re
from collections.abc import Sequence
from dataclasses import dataclass

from darijalens_nlp.arabizi import transliterate_arabizi
from darijalens_nlp.normalize import NormalizationConfig, normalize_text
from darijalens_nlp.script import Script, detect_script

DEFAULT_MODEL = "facebook/nllb-200-distilled-600M"
SOURCE_CODE = "ary_Arab"  # arabe marocain (darija)
TARGET_CODES = {"fr": "fra_Latn", "en": "eng_Latn", "msa": "arb_Arab"}  # msa : arabe standard
ARABIC_SCRIPT = "ar"  # pas une traduction : la même phrase en lettres arabes
SUPPORTED_TARGETS = (*TARGET_CODES, ARABIC_SCRIPT)

# On ne touche pas à la répétition des lettres dans `normalize_text` (max_repeat=None), car
# « الله », « للمدرسة » ou « ممتاز » ont des lettres doublées légitimes. On applique ensuite
# notre propre règle : 2 lettres identiques sont gardées, 3 ou plus (« جداااا », « mzyaaaan »)
# sont des allongements et deviennent 1 lettre.
_TRANSLATION_CONFIG = NormalizationConfig(max_repeat=None)
_ELONGATION = re.compile(r"([^\W\d_])\1{2,}")

_SPACE_BEFORE_PUNCT = re.compile(r"\s+([?!.,;:])")
_SPACE_IN_CONTRACTION = re.compile(r"(\w)\s+'(\w)")
_SPACE_AFTER_APOSTROPHE = re.compile(r"(\b[dlnjmstc]|qu)'\s+(\w)", re.IGNORECASE)


@dataclass(frozen=True)
class Translation:
    """Résultat d'une traduction."""

    texts: dict[str, str]  # traduction par langue : {"fr": "...", "en": "..."}
    source: str  # texte réellement envoyé au modèle (nettoyé, arabizi transcrit)
    transliterated: bool  # vrai si le texte d'origine contenait de l'écriture latine


def prepare_source(text: str) -> tuple[str, bool]:
    """Nettoie le texte et transcrit l'arabizi en arabe. Retourne (texte, transcrit ?)."""
    cleaned = _ELONGATION.sub(r"\1", normalize_text(text, _TRANSLATION_CONFIG))
    has_latin = detect_script(cleaned).script in (Script.LATIN, Script.MIXED)
    return transliterate_arabizi(cleaned), has_latin


def clean_translation(text: str) -> str:
    """Corrige les espaces que le modèle laisse autour de la ponctuation (« ? », « don 't »)."""
    text = _SPACE_BEFORE_PUNCT.sub(r"\1", text)
    text = _SPACE_IN_CONTRACTION.sub(r"\1'\2", text)
    text = _SPACE_AFTER_APOSTROPHE.sub(r"\1'\2", text)
    return text.strip()


class NllbTranslator:
    """Traducteur darija vers français / anglais."""

    def __init__(self, model_name: str = DEFAULT_MODEL, device: str | None = None) -> None:
        import torch
        from transformers import AutoModelForSeq2SeqLM, AutoTokenizer

        self._torch = torch
        self.device = device or ("cuda" if torch.cuda.is_available() else "cpu")
        self._tokenizer = AutoTokenizer.from_pretrained(model_name, src_lang=SOURCE_CODE)
        self._model = AutoModelForSeq2SeqLM.from_pretrained(model_name).to(self.device).eval()

    def translate(self, text: str, targets: Sequence[str] = ("fr", "en", "ar")) -> Translation:
        """Traduit `text` vers "fr", "en" ou "msa" (arabe standard).

        La cible "ar" n'est pas une traduction : elle renvoie la darija en lettres arabes.
        """
        unknown = [target for target in targets if target not in SUPPORTED_TARGETS]
        if unknown:
            raise ValueError(f"Langue cible inconnue : {unknown} (choix : {SUPPORTED_TARGETS})")
        source, transliterated = prepare_source(text)
        if not source:
            return Translation(
                texts={target: "" for target in targets}, source="", transliterated=False
            )
        texts = {
            target: source if target == ARABIC_SCRIPT else self._translate_one(source, target)
            for target in targets
        }
        return Translation(texts=texts, source=source, transliterated=transliterated)

    def _translate_one(self, source: str, target: str) -> str:
        batch = self._tokenizer(source, return_tensors="pt", truncation=True, max_length=256)
        batch = batch.to(self.device)
        with self._torch.no_grad():
            output = self._model.generate(
                **batch,
                forced_bos_token_id=self._tokenizer.convert_tokens_to_ids(TARGET_CODES[target]),
                max_new_tokens=256,
                num_beams=4,
            )
        return clean_translation(self._tokenizer.batch_decode(output, skip_special_tokens=True)[0])
