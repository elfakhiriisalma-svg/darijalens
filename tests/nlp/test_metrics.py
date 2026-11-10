"""Tests des mesures d'erreur."""

import pytest

from darijalens_nlp import character_error_rate, edit_distance


@pytest.mark.parametrize(
    ("reference", "hypothesis", "expected"),
    [
        ("", "", 0),
        ("abc", "abc", 0),
        ("abc", "", 3),
        ("", "abc", 3),
        ("kitten", "sitting", 3),
        ("خدمة", "خدما", 1),
    ],
)
def test_edit_distance(reference: str, hypothesis: str, expected: int) -> None:
    assert edit_distance(reference, hypothesis) == expected


def test_character_error_rate_is_zero_when_identical() -> None:
    assert character_error_rate(["واش", "نتا"], ["واش", "نتا"]) == 0


def test_character_error_rate_counts_errors_over_all_characters() -> None:
    # 1 erreur sur 4 + 0 erreur sur 4 = 1 erreur sur 8 caractères
    assert character_error_rate(["خدمة", "مزيان"[:4]], ["خدما", "مزيا"]) == pytest.approx(1 / 8)


def test_character_error_rate_rejects_different_lengths() -> None:
    with pytest.raises(ValueError):
        character_error_rate(["a"], [])


def test_character_error_rate_rejects_empty_references() -> None:
    with pytest.raises(ValueError):
        character_error_rate([""], [""])
