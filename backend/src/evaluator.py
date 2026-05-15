"""Theoretical strategy evaluation."""

from __future__ import annotations

from statistics import mean, median
from typing import Any

from .bet_types import Bet, make_bet
from .roulette_board import get_numbers


def evaluate_combo(combo: dict[str, Any], big_hit_threshold: float = 100.0) -> dict[str, Any]:
    """Evaluate one combo on all European roulette outcomes."""
    bets = normalize_bets(combo.get("bets", []))
    total_staked = sum(bet.stake for bet in bets)
    outcomes = [evaluate_number(number, bets, total_staked, big_hit_threshold) for number in get_numbers()]
    metrics = calculate_metrics(outcomes, total_staked)

    return {
        "combo_id": combo.get("combo_id", "combo"),
        "bets": [bet.to_dict() for bet in bets],
        "metrics": metrics,
        "outcomes": outcomes,
    }


def normalize_bets(raw_bets: list[Any]) -> list[Bet]:
    """Normalize dict or Bet inputs into Bet instances."""
    normalized: list[Bet] = []
    for raw_bet in raw_bets:
        if isinstance(raw_bet, Bet):
            normalized.append(raw_bet)
            continue

        normalized.append(
            make_bet(
                bet_type=raw_bet["type"],
                numbers=tuple(raw_bet["numbers"]),
                stake=int(raw_bet["stake"]),
                bet_id=raw_bet.get("bet_id"),
            )
        )
    return normalized


def evaluate_number(number: int, bets: list[Bet], total_staked: int, big_hit_threshold: float) -> dict[str, Any]:
    """Evaluate a combo for one roulette number."""
    winning_bets = [bet for bet in bets if number in bet.numbers]
    gross_return = sum(bet.stake * (bet.payout + 1) for bet in winning_bets)
    net_profit = gross_return - total_staked

    return {
        "number": number,
        "gross_return": gross_return,
        "net_profit": net_profit,
        "is_covered": bool(winning_bets),
        "is_profitable": net_profit > 0,
        "is_big_hit": net_profit >= big_hit_threshold,
        "winning_bets": [bet.to_dict() for bet in winning_bets],
        "explanation": explain_outcome(number, winning_bets, net_profit),
    }


def calculate_metrics(outcomes: list[dict[str, Any]], total_staked: int) -> dict[str, Any]:
    """Calculate theoretical metrics from all roulette outcomes."""
    net_profits = [float(outcome["net_profit"]) for outcome in outcomes]
    covered = [outcome for outcome in outcomes if outcome["is_covered"]]
    profitable = [outcome for outcome in outcomes if outcome["is_profitable"]]
    big_hits = [outcome for outcome in outcomes if outcome["is_big_hit"]]
    avg_profit_if_win = mean(outcome["net_profit"] for outcome in profitable) if profitable else 0.0
    expected_value = mean(net_profits)
    variance = mean((profit - expected_value) ** 2 for profit in net_profits)

    return {
        "total_staked": total_staked,
        "coverage_probability": len(covered) / len(outcomes),
        "hit_probability": len(covered) / len(outcomes),
        "profit_probability": len(profitable) / len(outcomes),
        "avg_profit_if_win": avg_profit_if_win,
        "max_profit": max(net_profits) if net_profits else 0.0,
        "min_profit": min(net_profits) if net_profits else 0.0,
        "expected_value": expected_value,
        "big_hit_probability": len(big_hits) / len(outcomes),
        "variance": variance,
        "volatility": variance**0.5,
        "median_profit": median(net_profits) if net_profits else 0.0,
        "theoretical_drawdown": abs(min(net_profits)) if net_profits else 0.0,
    }


def explain_outcome(number: int, winning_bets: list[Bet], net_profit: float) -> str:
    """Explain where the profit or loss comes from for one outcome."""
    if not winning_bets:
        return f"Number {number}: no covered bet wins, full stake is lost."

    parts = [f"{bet.stake} on {bet.type} ({'-'.join(str(value) for value in bet.numbers)}) pays {bet.payout}:1" for bet in winning_bets]
    if len(winning_bets) == 1:
        source = "single winning bet"
    else:
        source = "stacked winning bets"
    return f"Number {number}: {source}; " + "; ".join(parts) + f"; net profit {net_profit}."
