"""Strategy scoring functions."""


def score_combo(metrics: dict, weights: dict) -> float:
    """Score a strategy from normalized metrics and profile weights."""
    return sum(float(metrics.get(key, 0.0)) * float(weight) for key, weight in weights.items())
