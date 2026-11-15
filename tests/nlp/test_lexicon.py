"""Tests du dictionnaire arabizi -> arabe."""

import pytest

from darijalens_nlp import transliterate_arabizi
from darijalens_nlp.lexicon import aligned_pairs, build_lexicon, default_lexicon, split_words


def test_split_words_ignores_punctuation_and_case() -> None:
    assert split_words("Wach, nta mzyan?!") == ["wach", "nta", "mzyan"]


def test_aligned_pairs_match_words_one_to_one() -> None:
    pairs = aligned_pairs("salam hbiba", "سلام حبيبة")
    assert pairs == [("salam", "سلام"), ("hbiba", "حبيبة")]


def test_aligned_pairs_are_dropped_when_word_counts_differ() -> None:
    assert aligned_pairs("salam hbiba", "سلام") == []


def test_aligned_pairs_skip_numbers_and_arabic_source_words() -> None:
    pairs = aligned_pairs("3 hbiba", "3 حبيبة")
    assert pairs == [("hbiba", "حبيبة")]


def test_build_lexicon_keeps_the_most_frequent_spelling() -> None:
    pairs = [("hbiba", "حبيبة")] * 3 + [("hbiba", "حبيبا")]
    assert build_lexicon(pairs) == {"hbiba": "حبيبة"}


def test_build_lexicon_drops_rare_and_ambiguous_words() -> None:
    rare = [("nadir", "نادر")]
    ambiguous = [("sir", "سير")] * 2 + [("sir", "صير")] * 2
    assert build_lexicon(rare + ambiguous) == {}


def test_lexicon_overrides_the_rules_for_known_words() -> None:
    assert transliterate_arabizi("salam hbiba", lexicon={"hbiba": "حبيبة"}) == "سالام حبيبة"


def test_lexicon_is_case_insensitive_and_unknown_words_keep_using_rules() -> None:
    assert transliterate_arabizi("HBIBA bzaf", lexicon={"hbiba": "حبيبة"}) == "حبيبة بزاف"


def test_empty_lexicon_means_rules_only() -> None:
    assert transliterate_arabizi("hbiba", lexicon={}) == "هبيبا"


def test_default_lexicon_is_a_dict_of_text() -> None:
    from darijalens_nlp import lexicon

    lexicon.default_lexicon.cache_clear()
    loaded = lexicon.default_lexicon()
    assert isinstance(loaded, dict)
    assert all(isinstance(key, str) and isinstance(value, str) for key, value in loaded.items())


@pytest.mark.parametrize("word", ["hbiba", "salam"])
def test_default_lexicon_entries_do_not_contain_latin_letters(word: str) -> None:
    from darijalens_nlp import lexicon

    value = lexicon.default_lexicon().get(word, "")
    assert not any("a" <= char.lower() <= "z" for char in value)


def test_default_lexicon_function_exists() -> None:
    assert callable(default_lexicon)
