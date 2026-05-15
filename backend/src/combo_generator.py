"""Strategy generation entry points."""

from __future__ import annotations

import random
from typing import Any

from .bet_types import Bet, generate_all_bets, make_bet
from .evaluator import evaluate_combo


DEFAULT_CONFIG = {
    "bankroll": {"total": 100, "allowed_units": [1, 2, 3, 5, 10], "exact_spend": True},
    "objective": {"min_coverage": 0.0, "max_coverage": 1.0},
    "search": {"method": "hybrid", "combos_to_generate": 100, "keep_top_n": 10},
    "stake_strategy": {"max_stake_per_bet": 10, "allow_repeated_bets": True, "merge_same_bets": True},
}


def generate_combos(config: dict[str, Any] | None = None, seed: int | None = None) -> list[dict[str, Any]]:
    """Return generated strategy combos for grid, random or hybrid search."""
    cfg = merge_config(DEFAULT_CONFIG, config or {})
    method = cfg["search"].get("method", "hybrid")
    count = int(cfg["search"].get("combos_to_generate", 100))

    if method == "grid":
        return generate_grid_combos(cfg, count)
    if method == "random":
        return generate_random_combos(cfg, count, seed)
    if method == "hybrid":
        grid_count = count // 2
        random_count = count - grid_count
        return [
            *generate_grid_combos(cfg, grid_count),
            *generate_random_combos(cfg, random_count, seed, combo_id_offset=grid_count),
        ]
    raise ValueError(f"unsupported search method: {method}")


def generate_grid_combos(config: dict[str, Any], count: int) -> list[dict[str, Any]]:
    """Generate deterministic combos by walking legal bets and stake patterns."""
    combos: list[dict[str, Any]] = []
    legal_bets = generate_all_bets(stake=1)
    units = sorted(config["bankroll"]["allowed_units"])
    bankroll = int(config["bankroll"]["total"])
    max_stake = int(config["stake_strategy"].get("max_stake_per_bet", max(units)))

    index = 0
    attempts = 0
    max_attempts = max(count * 20, 100)
    while len(combos) < count and attempts < max_attempts:
        attempts += 1
        remaining = bankroll
        bets: list[Bet] = []
        cursor = index
        unit_cursor = index

        while remaining >= min(units):
            unit = min(units[unit_cursor % len(units)], max_stake, remaining)
            while unit not in units and unit > 0:
                unit -= 1
            if unit <= 0:
                break
            template = legal_bets[cursor % len(legal_bets)]
            bets.append(make_bet(template.type, template.numbers, stake=unit, bet_id=template.bet_id))
            remaining -= unit
            cursor += 7
            unit_cursor += 1

        combo = build_combo(f"grid_{index}", bets, config)
        if combo_is_allowed(combo, config):
            combos.append(combo)
        index += 1

    return combos


def generate_random_combos(
    config: dict[str, Any],
    count: int,
    seed: int | None = None,
    combo_id_offset: int = 0,
) -> list[dict[str, Any]]:
    """Generate random controlled combos respecting bankroll constraints."""
    rng = random.Random(seed)
    combos: list[dict[str, Any]] = []
    legal_bets = generate_all_bets(stake=1)
    units = sorted(config["bankroll"]["allowed_units"])
    bankroll = int(config["bankroll"]["total"])
    max_stake = int(config["stake_strategy"].get("max_stake_per_bet", max(units)))

    attempts = 0
    max_attempts = max(count * 50, 250)
    while len(combos) < count and attempts < max_attempts:
        attempts += 1
        remaining = bankroll
        bets: list[Bet] = []

        while remaining >= min(units):
            possible_units = [unit for unit in units if unit <= remaining and unit <= max_stake]
            if not possible_units:
                break
            unit = rng.choice(possible_units)
            template = rng.choice(legal_bets)
            bets.append(make_bet(template.type, template.numbers, stake=unit, bet_id=template.bet_id))
            remaining -= unit

        combo = build_combo(f"random_{combo_id_offset + len(combos)}", bets, config)
        if combo_is_allowed(combo, config):
            combos.append(combo)

    return combos


def build_combo(combo_id: str, bets: list[Bet], config: dict[str, Any]) -> dict[str, Any]:
    """Build a public combo payload."""
    if config["stake_strategy"].get("merge_same_bets", True):
        bets = merge_same_bets(bets)
    return {
        "combo_id": combo_id,
        "bets": [bet.to_dict() for bet in bets],
        "total_staked": sum(bet.stake for bet in bets),
    }


def merge_same_bets(bets: list[Bet]) -> list[Bet]:
    """Merge repeated bets by summing their stakes."""
    merged: dict[str, Bet] = {}
    for bet in bets:
        if bet.bet_id not in merged:
            merged[bet.bet_id] = bet
            continue
        previous = merged[bet.bet_id]
        merged[bet.bet_id] = make_bet(previous.type, previous.numbers, previous.stake + bet.stake, previous.bet_id)
    return list(merged.values())


def combo_is_allowed(combo: dict[str, Any], config: dict[str, Any]) -> bool:
    """Check bankroll and coverage constraints."""
    bankroll = int(config["bankroll"]["total"])
    exact_spend = bool(config["bankroll"].get("exact_spend", True))
    total_staked = int(combo["total_staked"])
    if total_staked > bankroll:
        return False
    if exact_spend and total_staked != bankroll:
        return False

    metrics = evaluate_combo(combo)["metrics"]
    min_coverage = float(config["objective"].get("min_coverage", 0.0))
    max_coverage = float(config["objective"].get("max_coverage", 1.0))
    return min_coverage <= metrics["coverage_probability"] <= max_coverage


def merge_config(base: dict[str, Any], overrides: dict[str, Any]) -> dict[str, Any]:
    """Recursively merge config dictionaries."""
    merged = {key: value.copy() if isinstance(value, dict) else value for key, value in base.items()}
    for key, value in overrides.items():
        if isinstance(value, dict) and isinstance(merged.get(key), dict):
            merged[key] = merge_config(merged[key], value)
        else:
            merged[key] = value
    return merged
