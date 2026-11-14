"""Tests des parties de la traduction qui ne demandent pas le modèle."""

import pytest

from darijalens_nlp.translate import NllbTranslator, clean_translation, prepare_source


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


def test_prepare_source_transliterates_arabizi() -> None:
    source, transliterated = prepare_source("wach nta mzyan")
    assert transliterated is True
    assert not any("a" <= char.lower() <= "z" for char in source)


def test_prepare_source_of_empty_text_is_empty() -> None:
    assert prepare_source("   ") == ("", False)


def test_translator_rejects_unknown_target() -> None:
    translator = NllbTranslator.__new__(NllbTranslator)  # sans charger le modèle
    with pytest.raises(ValueError, match="Langue cible inconnue"):
        translator.translate("شحال", "de")
