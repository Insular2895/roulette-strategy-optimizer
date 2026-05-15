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
    selected = select_candidate_pool(scored, config, profile_name, keep_top_n)
    ranked = [
        {
            **evaluation,
            "rank": rank,
            "profile": profile_name,
        }
        for rank, evaluation in enumerate(selected, start=1)
    ]
    return refine_top_strategies(ranked, config, seed=seed)


def select_candidate_pool(
    scored: list[dict[str, Any]],
    config: dict[str, Any],
    profile_name: str,
    keep_top_n: int,
) -> list[dict[str, Any]]:
    """Select candidates before stake refinement, optionally using a Pareto frontier."""
    pareto_config = config.get("pareto", {})
    enabled = bool(pareto_config.get("enabled", profile_name == "robust_balanced"))
    if not enabled:
        return scored[:keep_top_n]

    pool_size = int(pareto_config.get("candidate_pool_size", max(keep_top_n, 25)))
    frontier = pareto_frontier(scored)
    by_id = {candidate["combo_id"]: candidate for candidate in scored[:pool_size]}
    for candidate in frontier:
        by_id[candidate["combo_id"]] = candidate

    candidates = list(by_id.values())
    candidates.sort(key=robust_candidate_sort_key, reverse=True)
    return candidates[:pool_size]


def pareto_frontier(candidates: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Return non-dominated candidates on reward, coverage and risk dimensions."""
    frontier: list[dict[str, Any]] = []
    for candidate in candidates:
        if not any(dominates(other, candidate) for other in candidates if other is not candidate):
            frontier.append(candidate)
    return frontier


def dominates(left: dict[str, Any], right: dict[str, Any]) -> bool:
    """Return whether left dominates right in the theoretical objective space."""
    left_metrics = left["metrics"]
    right_metrics = right["metrics"]
    maximize = ("coverage_probability", "profit_probability", "big_hit_probability", "avg_profit_if_win", "max_profit")
    minimize = ("volatility", "theoretical_drawdown")

    no_worse = all(float(left_metrics[name]) >= float(right_metrics[name]) for name in maximize)
    no_worse = no_worse and all(float(left_metrics[name]) <= float(right_metrics[name]) for name in minimize)
    strictly_better = any(float(left_metrics[name]) > float(right_metrics[name]) for name in maximize)
    strictly_better = strictly_better or any(float(left_metrics[name]) < float(right_metrics[name]) for name in minimize)
    return no_worse and strictly_better


def robust_candidate_sort_key(candidate: dict[str, Any]) -> float:
    """Sort theoretical candidates for robust refinement."""
    metrics = candidate["metrics"]
    reward = (
        float(metrics["coverage_probability"]) * 0.75
        + float(metrics["profit_probability"]) * 1.6
        + float(metrics["big_hit_probability"]) * 0.8
        + float(metrics["avg_profit_if_win"]) / 300.0
        + float(metrics["max_profit"]) / 900.0
    )
    risk = float(metrics["volatility"]) / 350.0 + float(metrics["theoretical_drawdown"]) / 160.0
    return reward - risk + float(candidate.get("score", 0.0)) * 0.25
