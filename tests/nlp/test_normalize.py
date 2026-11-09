"""Tests de la normalisation."""

import pytest

from darijalens_nlp import NormalizationConfig, normalize_text


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        ("Wach NTA mzyan", "wach nta mzyan"),
        ("  wach   nta \n mzyan  ", "wach nta mzyan"),
        ("", ""),
        ("ｗach", "wach"),  # lettre latine pleine largeur
        ("wa​ch", "wach"),  # espace de largeur nulle
        ("très bien", "très bien"),  # les accents sont conservés
        ("3ndi 7ta l9ahwa", "3ndi 7ta l9ahwa"),  # les chiffres de l'arabizi sont conservés
    ],
)
def test_basic_cleaning(raw: str, expected: str) -> None:
    assert normalize_text(raw) == expected


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        ("mzyaaaan", "mzyan"),
        ("bzzaf", "bzaf"),  # limite connue : un doublon légitime est aussi réduit
        ("belle", "bele"),
        ("مزيااااان", "مزيان"),
        ("1000 dh", "1000 dh"),  # les chiffres ne sont jamais réduits
    ],
)
def test_elongation_is_limited_to_one_letter(raw: str, expected: str) -> None:
    assert normalize_text(raw) == expected


def test_elongation_can_keep_two_letters() -> None:
    config = NormalizationConfig(max_repeat=2)
    assert normalize_text("mzyaaaan", config) == "mzyaan"
    assert normalize_text("belle", config) == "belle"


def test_elongation_can_be_disabled() -> None:
    assert normalize_text("mzyaaaan", NormalizationConfig(max_repeat=None)) == "mzyaaaan"


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        ("bzaf!!!", "bzaf!"),
        ("wach???", "wach?"),
        ("واش؟؟؟", "واش؟"),
        ("ok...", "ok."),
    ],
)
def test_repeated_punctuation_is_collapsed(raw: str, expected: str) -> None:
    assert normalize_text(raw) == expected


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        ("مَرْحَبًا", "مرحبا"),  # voyelles courtes retirées
        ("مـــزيان", "مزيان"),  # tatwil retiré
        ("أحمد إبراهيم آمنة", "احمد ابراهيم امنة"),  # variantes de l'alef
        ("على", "علي"),  # alef maqsura
        ("کتاب", "كتاب"),  # kaf persan
        ("٣ndi", "3ndi"),  # chiffre arabo-indien
        ("۷ta", "7ta"),  # chiffre persan
    ],
)
def test_arabic_normalization(raw: str, expected: str) -> None:
    assert normalize_text(raw) == expected


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        ("chouf https://example.com/x?a=1 zwin", "chouf <url> zwin"),
        ("chouf www.site.ma. zwin", "chouf <url>. zwin"),
        ("contact a.b@mail.com merci", "contact <email> merci"),
        ("@user123 merci", "<user> merci"),
        ("3tini 0612345678", "3tini <phone>"),
        ("3tini 06 12 34 56 78", "3tini <phone>"),
        ("3tini +212 6 12 34 56 78", "3tini <phone>"),
        ("3tini 00212612345678", "3tini <phone>"),
    ],
)
def test_private_data_is_masked(raw: str, expected: str) -> None:
    assert normalize_text(raw) == expected


def test_ordinary_numbers_are_not_masked_as_phones() -> None:
    assert normalize_text("had l7aja b 150 dh") == "had l7aja b 150 dh"


def test_masking_can_be_disabled() -> None:
    config = NormalizationConfig(mask_private=False)
    assert normalize_text("@user123", config) == "@user123"


def test_emojis_are_kept_by_default() -> None:
    assert normalize_text("zwin 😀😀") == "zwin 😀😀"


def test_emojis_can_be_removed() -> None:
    assert normalize_text("zwin 😀😀 👍🏽", NormalizationConfig(remove_emojis=True)) == "zwin"


def test_each_rule_can_be_disabled() -> None:
    config = NormalizationConfig(lowercase=False)
    assert normalize_text("Wach", config) == "Wach"


@pytest.mark.parametrize(
    "raw",
    [
        "Wach NTA mzyaaaan!!! https://x.com @user 0612345678",
        "مَـــرحبااااا يا أحمد؟؟؟",
        "wach نتا mzyan 😀",
        "",
    ],
)
def test_normalization_is_idempotent(raw: str) -> None:
    once = normalize_text(raw)
    assert normalize_text(once) == once


def test_rejects_non_string_input() -> None:
    with pytest.raises(TypeError):
        normalize_text(None)  # type: ignore[arg-type]


def test_rejects_invalid_max_repeat() -> None:
    with pytest.raises(ValueError):
        NormalizationConfig(max_repeat=0)
