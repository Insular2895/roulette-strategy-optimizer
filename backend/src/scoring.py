"""Strategy scoring functions."""


def score_combo(metrics: dict, weights: dict) -> float:
    """Score a strategy from normalized metrics and profile weights."""
    return sum(float(metrics.get(key, 0.0)) * float(weight) for key, weight in weights.items())


def risk_reward_score(metrics: dict) -> float:
    """Calculate a simple theoretical risk/reward ratio."""
    risk = abs(float(metrics.get("min_profit", 0.0))) or 1.0
    reward = float(metrics.get("avg_profit_if_win", 0.0)) + float(metrics.get("max_profit", 0.0))
    return reward / risk
