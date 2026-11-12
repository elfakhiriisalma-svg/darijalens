"""Tests du détecteur de langage offensant (sur de petites données fabriquées)."""

import pytest

from darijalens_nlp.offensive import (
    CleaningReport,
    Example,
    OffensiveClassifier,
    build_pipeline,
    clean_examples,
    evaluate,
    preprocess,
    script_only_baseline,
    split_examples,
)


def _toy_examples(n_per_class: int = 30) -> list[Example]:
    gentle = [f"merci beaucoup bonne journee numero{i}" for i in range(n_per_class)]
    rude = [f"tu es nul et stupide numero{i}" for i in range(n_per_class)]
    return [Example(t, 0, "latin") for t in gentle] + [Example(t, 1, "latin") for t in rude]


def test_preprocess_removes_asterisks_and_normalizes() -> None:
    assert preprocess("*شخص*  Wach   ZWIN") == "شخص wach zwin"


def test_clean_examples_removes_empty_duplicate_and_contradictory() -> None:
    rows = [
        ("wach zwin", 0),
        ("Wach  ZWIN", 0),  # doublon après normalisation
        ("", 0),  # vide
        ("***", 1),  # vide après préparation
        ("texte ambigu", 0),
        ("texte ambigu", 1),  # contradiction : les deux sont retirés
        ("autre texte", 1),
    ]
    examples, report = clean_examples(rows)
    assert [e.text for e in examples] == ["wach zwin", "autre texte"]
    assert report == CleaningReport(read=7, empty=2, duplicates=1, contradictory_texts=1, kept=2)


def test_clean_examples_detects_script() -> None:
    examples, _ = clean_examples([("wach zwin", 0), ("واش زوين", 0)])
    assert [e.script for e in examples] == ["latin", "arabic"]


def test_split_is_disjoint_complete_and_reproducible() -> None:
    examples = _toy_examples()
    train, validation, test = split_examples(examples)
    assert len(train) + len(validation) + len(test) == len(examples)
    texts = [{e.text for e in part} for part in (train, validation, test)]
    assert not (texts[0] & texts[1]) and not (texts[0] & texts[2]) and not (texts[1] & texts[2])
    again = split_examples(examples)
    assert [e.text for e in again[0]] == [e.text for e in train]


def test_split_keeps_both_classes_in_every_part() -> None:
    for part in split_examples(_toy_examples()):
        assert {e.label for e in part} == {0, 1}


def test_model_learns_a_simple_pattern() -> None:
    train, _, test = split_examples(_toy_examples())
    model = build_pipeline().fit([e.text for e in train], [e.label for e in train])
    metrics = evaluate(model, test)
    assert metrics["accuracy"] == 1.0
    assert set(metrics["by_script"]) == {"latin"}


def test_script_only_baseline_cannot_separate_a_single_script() -> None:
    train, _, test = split_examples(_toy_examples())
    baseline = script_only_baseline(train, test)
    assert baseline["accuracy"] == pytest.approx(0.5, abs=0.1)


def test_classifier_predict_and_explain() -> None:
    examples = _toy_examples()
    model = build_pipeline().fit([e.text for e in examples], [e.label for e in examples])
    classifier = OffensiveClassifier(model)

    rude = classifier.predict("Tu es NUL et stupide")
    gentle = classifier.predict("merci beaucoup")
    assert rude.label == 1 and rude.name == "offensive" and rude.score > 0.5
    assert gentle.label == 0 and gentle.score < 0.5

    explanation = classifier.explain("tu es nul", top_k=3)
    assert 1 <= len(explanation) <= 3
    assert all(isinstance(name, str) and isinstance(value, float) for name, value in explanation)


def test_classifier_save_and_load(tmp_path) -> None:
    examples = _toy_examples()
    model = build_pipeline().fit([e.text for e in examples], [e.label for e in examples])
    original = OffensiveClassifier(model)
    path = tmp_path / "models" / "offensive.joblib"
    original.save(path)
    loaded = OffensiveClassifier.load(path)
    assert loaded.predict("tu es nul").score == pytest.approx(original.predict("tu es nul").score)
