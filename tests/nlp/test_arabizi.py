"""Tests de la transcription arabizi -> arabe."""

import pytest

from darijalens_nlp import normalize_text, transliterate_arabizi


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        ("3ndi", "عندي"),
        ("wach", "واش"),
        ("mzyan", "مزيان"),
        ("kifach", "كيفاش"),
        ("chkoun", "شكون"),
        ("chno", "شنو"),
        ("3lach", "علاش"),
        ("hna", "هنا"),
        ("nta", "نتا"),
        ("fin", "فين"),
        ("ghir", "غير"),
        ("kayn", "كاين"),
        ("dyal", "ديال"),
        ("zwin", "زوين"),
        ("wakha", "واخا"),
        ("mr7ba", "مرحبا"),
        ("bzaf", "بزاف"),
        ("hiya", "هيا"),
        ("ouled", "ولد"),
    ],
)
def test_common_words(raw: str, expected: str) -> None:
    assert transliterate_arabizi(raw) == expected


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        ("2", "2"),
        ("3'ndi", "غندي"),
        ("7'ir", "خير"),
    ],
)
def test_digits_and_apostrophes(raw: str, expected: str) -> None:
    assert transliterate_arabizi(raw) == expected


def test_sentence_keeps_punctuation_and_masks() -> None:
    assert transliterate_arabizi("wach nta mzyan?") == "واش نتا مزيان?"
    assert transliterate_arabizi("chouf <url> zwin") == "شوف <url> زوين"


def test_arabic_words_are_left_unchanged() -> None:
    assert transliterate_arabizi("wach نتا") == "واش نتا"


def test_numbers_are_not_transliterated() -> None:
    assert transliterate_arabizi("b 150 dh") == "ب 150 ده"
    assert transliterate_arabizi("1000") == "1000"


def test_accented_words_are_considered_french() -> None:
    assert transliterate_arabizi("très") == "très"


def test_empty_text() -> None:
    assert transliterate_arabizi("") == ""


@pytest.mark.parametrize(
    "raw",
    ["Wach NTA mzyaaaan!!!", "3ndi 7ta l9ahwa", "chouf https://x.com zwin", "wach نتا"],
)
def test_pipeline_with_normalization_is_idempotent(raw: str) -> None:
    once = transliterate_arabizi(normalize_text(raw))
    assert transliterate_arabizi(once) == once


def test_rejects_non_string_input() -> None:
    with pytest.raises(TypeError):
        transliterate_arabizi(None)  # type: ignore[arg-type]
