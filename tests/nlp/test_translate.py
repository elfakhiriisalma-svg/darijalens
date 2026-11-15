"""Tests des parties de la traduction qui ne demandent pas le modèle."""

import pytest

from darijalens_nlp.translate import (
    TARGET_CODES,
    NllbTranslator,
    clean_translation,
    prepare_source,
)


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        ("Combien coûte cette voiture ?", "Combien coûte cette voiture?"),
        ("I don 't like this movie .", "I don't like this movie."),
        ("Je veux aller à l'école demain .", "Je veux aller à l'école demain."),
        ("La météo est bonne aujourd'hui", "La météo est bonne aujourd'hui"),
        ("  Bonjour , ça va ?  ", "Bonjour, ça va?"),
    ],
)
def test_clean_translation(raw: str, expected: str) -> None:
    assert clean_translation(raw) == expected


def test_prepare_source_keeps_arabic_text() -> None:
    source, transliterated = prepare_source("شحال هاد الطوموبيل؟")
    assert source == "شحال هاد الطوموبيل؟"
    assert transliterated is False


@pytest.mark.parametrize("text", ["الله يعطيك الصحة", "بغيت نمشي للمدرسة", "هاد الفيلم ممتاز"])
def test_prepare_source_keeps_legitimate_double_letters(text: str) -> None:
    assert prepare_source(text)[0] == text


def test_prepare_source_still_shortens_elongations() -> None:
    assert prepare_source("ممتاز جداااااا")[0] == "ممتاز جدا"
    assert prepare_source("ممتاااز")[0] == "ممتاز"


def test_prepare_source_transliterates_arabizi() -> None:
    source, transliterated = prepare_source("wach nta mzyan")
    assert transliterated is True
    assert not any("a" <= char.lower() <= "z" for char in source)


def test_prepare_source_of_empty_text_is_empty() -> None:
    assert prepare_source("   ") == ("", False)


def test_translator_rejects_unknown_target() -> None:
    translator = NllbTranslator.__new__(NllbTranslator)  # sans charger le modèle
    with pytest.raises(ValueError, match="Langue cible inconnue"):
        translator.translate("شحال", ["de"])


def test_arabic_target_returns_text_in_arabic_letters_without_model() -> None:
    translator = NllbTranslator.__new__(NllbTranslator)  # sans charger le modèle
    result = translator.translate("wach nta mzyan", ["ar"])
    assert result.texts == {"ar": "واش نتا مزيان"}
    assert result.transliterated is True


def test_modern_standard_arabic_is_a_supported_translation_target() -> None:
    assert TARGET_CODES["msa"] == "arb_Arab"
