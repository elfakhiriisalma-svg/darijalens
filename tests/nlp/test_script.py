"""Tests de la détection d'écriture."""

import pytest

from darijalens_nlp import Script, detect_script


@pytest.mark.parametrize(
    ("text", "expected"),
    [
        ("واش نتا مزيان", Script.ARABIC),
        ("wach nta mzyan", Script.LATIN),
        ("wach نتا mzyan", Script.MIXED),
        ("Très bien, merci à vous", Script.LATIN),
    ],
)
def test_detects_main_scripts(text: str, expected: Script) -> None:
    assert detect_script(text).script is expected


def test_arabizi_digits_are_not_counted_as_letters() -> None:
    result = detect_script("3ndi mochkil 7ta l9ahwa")
    assert result.script is Script.LATIN
    assert result.arabic_letters == 0


def test_arabic_diacritics_do_not_change_result() -> None:
    assert detect_script("مَرْحَبًا").script is Script.ARABIC


@pytest.mark.parametrize("text", ["", "   ", "1234 !!! ???", "😀😀", "١٢٣", "привет"])
def test_unknown_when_no_arabic_or_latin_letters(text: str) -> None:
    result = detect_script(text)
    assert result.script is Script.UNKNOWN
    assert result.total_letters == 0
    assert result.arabic_ratio == 0.0


def test_ratios_are_computed_from_letters_only() -> None:
    result = detect_script("ab جد 12 !!")
    assert result.arabic_letters == 2
    assert result.latin_letters == 2
    assert result.arabic_ratio == pytest.approx(0.5)
    assert result.latin_ratio == pytest.approx(0.5)


def test_negligible_second_script_is_ignored() -> None:
    # 1 lettre latine sur 21 : sous le seuil de 10 %, le texte reste arabe.
    text = "واش نتا مزيان بزاف الحمد لله ok"
    assert detect_script(text).script is Script.ARABIC


def test_threshold_can_be_changed() -> None:
    text = "واش نتا مزيان بزاف الحمد لله ok"
    assert detect_script(text, mixed_threshold=0.0).script is Script.MIXED


def test_rejects_non_string_input() -> None:
    with pytest.raises(TypeError):
        detect_script(None)  # type: ignore[arg-type]


@pytest.mark.parametrize("threshold", [-0.1, 0.6])
def test_rejects_invalid_threshold(threshold: float) -> None:
    with pytest.raises(ValueError):
        detect_script("abc", mixed_threshold=threshold)
