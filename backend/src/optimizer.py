"""Optimization pipeline orchestration."""

from __future__ import annotations

from typing import Any

from .combo_generator import generate_combos
from .evaluator import evaluate_combo
from .scoring import score_evaluations
from .stake_refiner import refine_top_strategies


def optimize(config: dict[str, Any], seed: int | None = None) -> list[dict[str, Any]]:
    """Run strategy generation, evaluation, scoring and top-N selection."""
    combos = generate_combos(config, seed=seed)
    big_hit_threshold = float(config.get("objective", {}).get("big_hit_threshold", 100.0))
    evaluations = [evaluate_combo(combo, big_hit_threshold=big_hit_threshold) for combo in combos]

    profile_name = config.get("objective", {}).get("profile", "balanced")
    profiles = config.get("profiles", {})
    if profile_name not in profiles:
        raise ValueError(f"missing scoring profile: {profile_name}")

    scored = score_evaluations(evaluations, profiles[profile_name])
    scored.sort(key=lambda evaluation: evaluation["score"], reverse=True)

    keep_top_n = int(config.get("search", {}).get("keep_top_n", 10))
    ranked = [
        {
            **evaluation,
            "rank": rank,
            "profile": profile_name,
        }
        for rank, evaluation in enumerate(scored[:keep_top_n], start=1)
    ]
    return refine_top_strategies(ranked, config, seed=seed)
