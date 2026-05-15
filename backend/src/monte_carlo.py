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
