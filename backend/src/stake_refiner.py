"""Local stake refinement for top roulette strategies."""

from __future__ import annotations

import random
from typing import Any

from .bet_types import make_bet
from .evaluator import evaluate_combo


def refine_top_strategies(
    strategies: list[dict[str, Any]],
    config: dict[str, Any],
    seed: int | None = None,
) -> list[dict[str, Any]]:
    """Refine stake allocation on top strategy structures."""
    refinement = config.get("refinement", {})
    if not refinement.get("enabled", True) or not strategies:
        return strategies

    rng = random.Random(seed)
    top_n = int(refinement.get("top_n", min(5, len(strategies))))
    variants_per_strategy = int(refinement.get("variants_per_strategy", 500))
    keep_top_n = int(config.get("search", {}).get("keep_top_n", 10))
    bankroll = int(config.get("bankroll", {}).get("total", 100))
    min_stake = int(refinement.get("min_stake_per_bet", 0))
    max_stake = int(refinement.get("max_stake_per_bet", max(10, bankroll)))
    big_hit_threshold = float(config.get("objective", {}).get("big_hit_threshold", 100.0))
    profile_name = config.get("objective", {}).get("profile", "balanced")

    candidates: list[dict[str, Any]] = []
    for strategy in strategies[:top_n]:
        base_bets = strategy["bets"]
        candidates.append(enrich_ratio(strategy, "original", profile_name))
        for index in range(variants_per_strategy):
            variant = build_refined_combo(
                strategy["combo_id"],
                base_bets,
                bankroll,
                min_stake,
                max_stake,
                rng,
                index,
            )
            if not variant:
                continue
            evaluation = evaluate_combo(variant, big_hit_threshold=big_hit_threshold)
            if combo_is_within_constraints(evaluation, config):
                candidates.append(enrich_ratio(evaluation, "refined", profile_name))

    candidates.sort(key=lambda item: item["metrics"]["optimization_ratio"], reverse=True)
    refined = []
    for rank, candidate in enumerate(candidates[:keep_top_n], start=1):
        refined.append(
            {
                **candidate,
                "rank": rank,
                "profile": config.get("objective", {}).get("profile", "balanced"),
                "score": candidate["metrics"]["optimization_ratio"],
            }
        )
    return refined


def build_refined_combo(
    combo_id: str,
    base_bets: list[dict[str, Any]],
    bankroll: int,
    min_stake: int,
    max_stake: int,
    rng: random.Random,
    variant_index: int,
) -> dict[str, Any] | None:
    """Create one random stake allocation on the same bet structure."""
    shuffled = list(base_bets)
    rng.shuffle(shuffled)

    active_bets: list[dict[str, Any]] = []
    remaining = bankroll
    required_min = max(min_stake, 1)

    for bet in shuffled:
        slots_left = len(shuffled) - len(active_bets) - 1
        can_skip = min_stake == 0 and active_bets and rng.random() < 0.22
        if can_skip:
            continue

        reserve = slots_left * required_min if min_stake > 0 else 0
        available = min(max_stake, remaining - reserve)
        if available < required_min:
            continue

        if slots_left == 0:
            stake = min(available, remaining)
        else:
            bias = rng.random()
            if bias < 0.55:
                stake = rng.randint(required_min, min(available, max(required_min, max_stake // 2)))
            elif bias < 0.90:
                stake = rng.randint(required_min, available)
            else:
                stake = available
        stake = max(required_min, min(stake, remaining))
        active_bets.append({**bet, "stake": stake})
        remaining -= stake
        if remaining <= 0:
            break

    if remaining > 0 and active_bets:
        adjustable = [bet for bet in active_bets if bet["stake"] < max_stake]
        while remaining > 0 and adjustable:
            bet = rng.choice(adjustable)
            add = min(remaining, max_stake - bet["stake"])
            bet["stake"] += add
            remaining -= add
            adjustable = [item for item in active_bets if item["stake"] < max_stake]

    if remaining != 0 or not active_bets:
        return None

    normalized = [
        make_bet(bet["type"], bet["numbers"], int(bet["stake"]), bet["bet_id"]).to_dict()
        for bet in active_bets
        if int(bet["stake"]) > 0
    ]
    return {
        "combo_id": f"{combo_id}_refined_{variant_index}",
        "bets": normalized,
        "total_staked": sum(bet["stake"] for bet in normalized),
    }


def combo_is_within_constraints(evaluation: dict[str, Any], config: dict[str, Any]) -> bool:
    """Check coverage constraints for a refined combo."""
    metrics = evaluation["metrics"]
    min_coverage = float(config.get("objective", {}).get("min_coverage", 0.0))
    max_coverage = float(config.get("objective", {}).get("max_coverage", 1.0))
    return min_coverage <= metrics["coverage_probability"] <= max_coverage


def enrich_ratio(evaluation: dict[str, Any], source: str, profile_name: str = "balanced") -> dict[str, Any]:
    """Attach optimization ratio metrics."""
    metrics = evaluation["metrics"]
    optimization_ratio = calculate_optimization_ratio(metrics, profile_name)
    risk = abs(float(metrics.get("min_profit", 0.0))) or 1.0
    risk_reward = (float(metrics.get("avg_profit_if_win", 0.0)) + float(metrics.get("max_profit", 0.0))) / risk
    return {
        **evaluation,
        "refinement_source": source,
        "metrics": {
            **metrics,
            "optimization_ratio": optimization_ratio,
            "risk_reward_score": metrics.get("risk_reward_score", risk_reward),
        },
    }


def calculate_optimization_ratio(metrics: dict[str, Any], profile_name: str = "balanced") -> float:
    """Calculate a robust reward/risk ratio for stake refinement."""
    profit_probability = float(metrics.get("profit_probability", 0.0))
    big_hit_probability = float(metrics.get("big_hit_probability", 0.0))
    avg_profit_if_win = float(metrics.get("avg_profit_if_win", 0.0))
    max_profit = float(metrics.get("max_profit", 0.0))
    volatility = float(metrics.get("volatility", 0.0))
    min_profit = abs(float(metrics.get("min_profit", 0.0)))
    expected_loss = abs(min(float(metrics.get("expected_value", 0.0)), 0.0))
    loss_buffer_ratio = float(metrics.get("loss_buffer_ratio", 0.0))
    max_loss_cover = float(metrics.get("max_loss_cover", 0.0))

    weighted_reward = profit_probability * avg_profit_if_win
    explosive_reward = big_hit_probability * max_profit
    if profile_name == "recovery_hits":
        reward = weighted_reward + explosive_reward + max_profit * 0.12 + loss_buffer_ratio * 18.0 + max_loss_cover * 8.0
        risk = min_profit + volatility * 0.75 + expected_loss * 4.0
    else:
        reward = weighted_reward + explosive_reward + max_profit * 0.05 + loss_buffer_ratio * 5.0 + max_loss_cover * 2.0
        risk = min_profit + volatility + expected_loss * 5.0
    return reward / (risk or 1.0)
