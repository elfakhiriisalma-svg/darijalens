"""Mesures d'erreur pour comparer un texte produit à un texte de référence."""

from __future__ import annotations

from collections.abc import Sequence


def edit_distance(reference: str, hypothesis: str) -> int:
    """Distance de Levenshtein : nombre minimal d'insertions, suppressions et remplacements."""
    previous = list(range(len(hypothesis) + 1))
    for i, ref_char in enumerate(reference, start=1):
        current = [i]
        for j, hyp_char in enumerate(hypothesis, start=1):
            current.append(
                min(
                    previous[j] + 1,  # suppression
                    current[j - 1] + 1,  # insertion
                    previous[j - 1] + (ref_char != hyp_char),  # remplacement
                )
            )
        previous = current
    return previous[-1]


def character_error_rate(references: Sequence[str], hypotheses: Sequence[str]) -> float:
    """Taux d'erreur par caractère (CER) sur l'ensemble du corpus.

    CER = (somme des distances d'édition) / (nombre total de caractères de référence).
    0 signifie aucune erreur. La valeur peut dépasser 1 si le texte produit est très long.

    Raises:
        ValueError: si les deux listes n'ont pas la même longueur, ou si les références
            ne contiennent aucun caractère.
    """
    if len(references) != len(hypotheses):
        raise ValueError("references et hypotheses doivent avoir la même longueur")
    total_chars = sum(len(reference) for reference in references)
    if total_chars == 0:
        raise ValueError("les références ne contiennent aucun caractère")
    total_errors = sum(edit_distance(r, h) for r, h in zip(references, hypotheses, strict=True))
    return total_errors / total_chars
