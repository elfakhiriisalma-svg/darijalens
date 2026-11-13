"""Tests de l'analyse de sentiment (lecture de MYC, emojis, classes)."""

from pathlib import Path

from darijalens_nlp.offensive import Example, build_pipeline
from darijalens_nlp.sentiment import (
    SentimentClassifier,
    emoji_bias,
    has_emoji,
    load_myc_rows,
    without_emojis,
)


def _write_myc(path: Path) -> None:
    content = (
        '"sentence,polarity"\r\n'
        '"zwin bzaf 😍,1 "\r\n'
        '"khayb had lvideo,-1 "\r\n'
        '"ligne sans etiquette"\r\n'
        '"etiquette inconnue,5"\r\n'
        '",1"\r\n'
    )
    path.write_text(content, encoding="utf-16")


def test_load_myc_rows_reads_utf16_and_maps_labels(tmp_path: Path) -> None:
    path = tmp_path / "DATA_RAW.csv"
    _write_myc(path)
    assert load_myc_rows(path) == [("zwin bzaf 😍", 1), ("khayb had lvideo", 0)]


def test_has_emoji() -> None:
    assert has_emoji("zwin 😍")
    assert not has_emoji("zwin")


def test_without_emojis_strips_and_drops_empty_texts() -> None:
    examples = [Example("zwin 😍", 1, "latin"), Example("😂😂", 1, "unknown")]
    assert [e.text for e in without_emojis(examples)] == ["zwin"]


def test_emoji_bias_counts_labels_by_emoji_presence() -> None:
    examples = [
        Example("zwin 😍", 1, "latin"),
        Example("khayb", 0, "latin"),
        Example("khayb bzaf", 0, "latin"),
    ]
    assert emoji_bias(examples) == {
        "with_emoji": {"positive": 1},
        "without_emoji": {"negative": 2},
    }


def test_sentiment_classifier_uses_sentiment_names() -> None:
    positive = [Example(f"zwin bzaf numero{i}", 1, "latin") for i in range(30)]
    negative = [Example(f"khayb bzaf numero{i}", 0, "latin") for i in range(30)]
    data = positive + negative
    model = build_pipeline().fit([e.text for e in data], [e.label for e in data])
    classifier = SentimentClassifier(model)
    assert classifier.predict("zwin bzaf").name == "positive"
    assert classifier.predict("khayb bzaf").name == "negative"
