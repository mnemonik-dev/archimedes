"""Tests for the #537 PROTOTYPE resolve_num_trials — DO NOT MERGE without Dan's sign-off.

Hermetic; documents the intended provenance-split semantics so the prototype
diff is reviewable as executable spec.
"""

from __future__ import annotations

from archimedes.services.rigor_evaluator import resolve_num_trials


def test_paper_grounded_uses_recorded_variant_count() -> None:
    # risk parity: 3 lookback combos actually tried (third-wave walk-forward run)
    assert resolve_num_trials("paper_grounded", n_variants_tried=3, library_size=23) == 3


def test_paper_grounded_single_faithful_implementation() -> None:
    assert resolve_num_trials("paper_grounded", n_variants_tried=1, library_size=23) == 1


def test_paper_grounded_without_recorded_trials_falls_back_to_library() -> None:
    # Unrecorded search history is treated as mined — conservative default.
    assert resolve_num_trials("paper_grounded", n_variants_tried=None, library_size=23) == 23
    assert resolve_num_trials("paper_grounded", n_variants_tried=0, library_size=23) == 23


def test_fusion_and_library_selected_use_full_library() -> None:
    assert resolve_num_trials("fusion", n_variants_tried=2, library_size=23) == 23
    assert resolve_num_trials("library_selected", n_variants_tried=1, library_size=23) == 23


def test_library_size_floor_is_one() -> None:
    assert resolve_num_trials("fusion", n_variants_tried=None, library_size=0) == 1
