"""Strategy scoring functions."""

from __future__ import annotations

from typing import Any


PROFILE_METRIC_MAP = {
    "coverage_weight": "coverage_probability",
    "profit_probability_weight": "profit_probability",
    "avg_win_weight": "avg_profit_if_win",
    "big_hit_weight": "big_hit_probability",
    "max_profit_weight": "max_profit",
    "loss_buffer_weight": "loss_buffer_ratio",
    "max_loss_cover_weight": "max_loss_cover",
}

MINIMIZE_METRIC_MAP = {
    "volatility_weight": "volatility",
    "drawdown_weight": "theoretical_drawdown",
}


def score_combo(metrics: dict, weights: dict) -> float:
    """Score a strategy from normalized metrics and profile weights."""
    return sum(float(metrics.get(key, 0.0)) * float(weight) for key, weight in weights.items())


def risk_reward_score(metrics: dict) -> float:
    """Calculate a simple theoretical risk/reward ratio."""
    risk = abs(float(metrics.get("min_profit", 0.0))) or 1.0
    reward = float(metrics.get("avg_profit_if_win", 0.0)) + float(metrics.get("max_profit", 0.0))
    return reward / risk


def score_evaluations(evaluations: list[dict[str, Any]], profile_weights: dict[str, float]) -> list[dict[str, Any]]:
    """Attach normalized score values to evaluated combos."""
    ranges = build_metric_ranges([evaluation["metrics"] for evaluation in evaluations])
    scored: list[dict[str, Any]] = []

    for evaluation in evaluations:
        metrics = evaluation["metrics"]
        components: dict[str, float] = {}
        score = 0.0

        for weight_name, metric_name in PROFILE_METRIC_MAP.items():
            weight = float(profile_weights.get(weight_name, 0.0))
            normalized = normalize_metric(float(metrics.get(metric_name, 0.0)), ranges[metric_name])
            components[metric_name] = normalized
            score += normalized * weight

        for weight_name, metric_name in MINIMIZE_METRIC_MAP.items():
            weight = float(profile_weights.get(weight_name, 0.0))
            normalized = 1.0 - normalize_metric(float(metrics.get(metric_name, 0.0)), ranges[metric_name])
            components[metric_name] = normalized
            score += normalized * weight

        risk_weight = float(profile_weights.get("risk_weight", 0.0))
        risk_component = 1.0 - normalize_metric(float(metrics.get("theoretical_drawdown", 0.0)), ranges["theoretical_drawdown"])
        components["risk"] = risk_component
        score += risk_component * risk_weight

        enriched = {**evaluation, "score": score, "score_components": components}
        enriched["metrics"] = {**metrics, "risk_reward_score": risk_reward_score(metrics)}
        scored.append(enriched)

    return scored


def build_metric_ranges(metrics_list: list[dict[str, Any]]) -> dict[str, tuple[float, float]]:
    """Build min/max ranges for every metric used in scoring."""
    metric_names = set(PROFILE_METRIC_MAP.values()) | set(MINIMIZE_METRIC_MAP.values()) | {"theoretical_drawdown"}
    ranges: dict[str, tuple[float, float]] = {}
    for metric_name in metric_names:
        values = [float(metrics.get(metric_name, 0.0)) for metrics in metrics_list]
        ranges[metric_name] = (min(values), max(values)) if values else (0.0, 0.0)
    return ranges


def normalize_metric(value: float, metric_range: tuple[float, float]) -> float:
    """Normalize a metric value to 0-1."""
    minimum, maximum = metric_range
    if maximum == minimum:
        return 1.0
    return (value - minimum) / (maximum - minimum)
