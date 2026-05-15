"""Monte Carlo simulation for retained roulette strategies."""

from __future__ import annotations

import random
from statistics import mean, median
from typing import Any


def run_monte_carlo(
    strategies: list[dict[str, Any]],
    sessions: int = 10000,
    spins_per_session: int = 100,
    initial_bankroll: float = 1000.0,
    seed: int | None = None,
) -> dict[str, list[dict[str, Any]]]:
    """Run Monte Carlo validation for selected strategies."""
    rng = random.Random(seed)
    aggregate_results: list[dict[str, Any]] = []
    all_paths: list[dict[str, Any]] = []

    for strategy in strategies:
        simulation = simulate_strategy(strategy, sessions, spins_per_session, initial_bankroll, rng)
        aggregate_results.append(simulation["result"])
        all_paths.extend(simulation["paths"])

    return {"results": aggregate_results, "paths": all_paths}


def rerank_by_monte_carlo(
    strategies: list[dict[str, Any]],
    simulation: dict[str, list[dict[str, Any]]],
    robust_filter: dict[str, Any] | None = None,
) -> list[dict[str, Any]]:
    """Return strategies reranked by robust Monte Carlo behavior."""
    robust_filter = robust_filter or {}
    result_by_combo = {result["combo_id"]: result for result in simulation["results"]}
    enriched: list[dict[str, Any]] = []

    for strategy in strategies:
        result = result_by_combo[strategy["combo_id"]]
        robust_score = calculate_robust_score(result, strategy["metrics"])
        filter_pass, filter_reasons = evaluate_robust_filter(result, robust_filter)
        monte_carlo_metrics = {
            **result,
            "robust_score": robust_score,
            "robust_filter_pass": filter_pass,
            "robust_filter_reasons": filter_reasons,
        }
        enriched.append(
            {
                **strategy,
                "monte_carlo": monte_carlo_metrics,
                "score": robust_score,
            }
        )

    passing = [strategy for strategy in enriched if strategy["monte_carlo"]["robust_filter_pass"]]
    ranking_pool = passing or enriched
    ranking_pool.sort(key=lambda strategy: strategy["monte_carlo"]["robust_score"], reverse=True)
    return [
        {
            **strategy,
            "rank": rank,
        }
        for rank, strategy in enumerate(ranking_pool, start=1)
    ]


def evaluate_robust_filter(result: dict[str, Any], robust_filter: dict[str, Any]) -> tuple[bool, list[str]]:
    """Check hard Monte Carlo constraints."""
    if not robust_filter.get("enabled", True):
        return True, []

    checks = [
        ("probability_bust", "<=", robust_filter.get("max_probability_bust")),
        ("avg_max_drawdown", "<=", robust_filter.get("max_avg_drawdown")),
        ("max_drawdown_seen", "<=", robust_filter.get("max_drawdown_seen")),
        ("probability_profit", ">=", robust_filter.get("min_probability_profit")),
    ]
    reasons: list[str] = []
    for metric, operator, threshold in checks:
        if threshold is None:
            continue
        value = float(result.get(metric, 0.0))
        limit = float(threshold)
        if operator == "<=" and value > limit:
            reasons.append(f"{metric}={value:.4g} > {limit:.4g}")
        if operator == ">=" and value < limit:
            reasons.append(f"{metric}={value:.4g} < {limit:.4g}")

    return not reasons, reasons


def calculate_robust_score(result: dict[str, Any], metrics: dict[str, Any]) -> float:
    """Score a strategy by Monte Carlo resilience and theoretical upside."""
    final_bankroll_avg = float(result.get("final_bankroll_avg", 0.0))
    sessions = float(result.get("sessions", 1.0)) or 1.0
    spins = float(result.get("spins_per_session", 1.0)) or 1.0
    expected_start = final_bankroll_avg - float(metrics.get("expected_value", 0.0)) * spins

    bankroll_retention = final_bankroll_avg / (expected_start or 1.0)
    profit_component = float(result.get("probability_profit", 0.0)) * 2.0
    hit_component = float(result.get("big_hit_frequency", 0.0)) * 1.2
    bust_penalty = float(result.get("probability_bust", 0.0)) * 2.5
    drawdown_penalty = float(result.get("avg_max_drawdown", 0.0)) / (expected_start or 1.0)
    worst_drawdown_penalty = float(result.get("max_drawdown_seen", 0.0)) / ((expected_start or 1.0) * max(sessions**0.5, 1.0))
    theory_component = float(metrics.get("optimization_ratio", metrics.get("risk_reward_score", 0.0))) * 0.25

    return bankroll_retention + profit_component + hit_component + theory_component - bust_penalty - drawdown_penalty - worst_drawdown_penalty


def simulate_strategy(
    strategy: dict[str, Any],
    sessions: int,
    spins_per_session: int,
    initial_bankroll: float,
    rng: random.Random,
) -> dict[str, Any]:
    """Simulate one strategy across many random sessions."""
    outcome_by_number = {outcome["number"]: outcome for outcome in strategy["outcomes"]}
    total_staked = float(strategy["metrics"]["total_staked"])
    big_hit_threshold = min(outcome["net_profit"] for outcome in strategy["outcomes"] if outcome["is_big_hit"]) if any(
        outcome["is_big_hit"] for outcome in strategy["outcomes"]
    ) else float("inf")

    final_bankrolls: list[float] = []
    max_drawdowns: list[float] = []
    busted_sessions = 0
    profitable_sessions = 0
    biggest_hit_seen = 0.0
    hit_frequencies: list[float] = []
    big_hit_frequencies: list[float] = []
    paths: list[dict[str, Any]] = []

    for session_id in range(sessions):
        bankroll = float(initial_bankroll)
        peak = bankroll
        max_drawdown = 0.0
        hit_count = 0
        big_hit_count = 0
        busted = False

        for spin_index in range(1, spins_per_session + 1):
            if bankroll >= total_staked:
                number = rng.randint(0, 36)
                outcome = outcome_by_number[number]
                net_profit = float(outcome["net_profit"])
                bankroll += net_profit
                if outcome["is_covered"]:
                    hit_count += 1
                if net_profit >= big_hit_threshold:
                    big_hit_count += 1
                biggest_hit_seen = max(biggest_hit_seen, net_profit)
            else:
                busted = True

            peak = max(peak, bankroll)
            max_drawdown = max(max_drawdown, peak - bankroll)
            paths.append(
                {
                    "combo_id": strategy["combo_id"],
                    "session_id": session_id,
                    "spin_index": spin_index,
                    "bankroll": bankroll,
                }
            )

        final_bankrolls.append(bankroll)
        max_drawdowns.append(max_drawdown)
        hit_frequencies.append(hit_count / spins_per_session)
        big_hit_frequencies.append(big_hit_count / spins_per_session)
        busted_sessions += int(busted or bankroll < total_staked)
        profitable_sessions += int(bankroll > initial_bankroll)

    result = {
        "combo_id": strategy["combo_id"],
        "sessions": sessions,
        "spins_per_session": spins_per_session,
        "final_bankroll_avg": mean(final_bankrolls) if final_bankrolls else 0.0,
        "final_bankroll_median": median(final_bankrolls) if final_bankrolls else 0.0,
        "probability_profit": profitable_sessions / sessions if sessions else 0.0,
        "probability_bust": busted_sessions / sessions if sessions else 0.0,
        "avg_max_drawdown": mean(max_drawdowns) if max_drawdowns else 0.0,
        "max_drawdown_seen": max(max_drawdowns) if max_drawdowns else 0.0,
        "biggest_hit_seen": biggest_hit_seen,
        "avg_hit_frequency": mean(hit_frequencies) if hit_frequencies else 0.0,
        "big_hit_frequency": mean(big_hit_frequencies) if big_hit_frequencies else 0.0,
    }
    return {"result": result, "paths": paths}
