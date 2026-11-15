"""Réglages communs aux tests."""

import pytest


@pytest.fixture(autouse=True)
def rules_only_transliteration(monkeypatch):
    """Les tests vérifient les règles de transcription, pas le contenu du dictionnaire.

    Sans cela, ajouter ou régénérer `arabizi_lexicon.json` ferait changer les résultats.
    Les tests du dictionnaire passent leur propre dictionnaire à `transliterate_arabizi`.
    """
    monkeypatch.setattr("darijalens_nlp.arabizi.default_lexicon", lambda: {})
