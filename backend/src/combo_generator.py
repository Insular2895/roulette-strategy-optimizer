"""Strategy generation entry points."""

from __future__ import annotations

import random
from typing import Any

from .bet_types import Bet, generate_all_bets, generate_corners, generate_splits, generate_straights, generate_streets, make_bet
from .evaluator import evaluate_combo
from .roulette_board import get_wheel_neighbors


DEFAULT_CONFIG = {
    "bankroll": {"total": 100, "allowed_units": [1, 2, 3, 5, 10], "exact_spend": True},
    "objective": {"min_coverage": 0.0, "max_coverage": 1.0},
    "search": {"method": "hybrid", "combos_to_generate": 100, "keep_top_n": 10},
    "stake_strategy": {"max_stake_per_bet": 10, "allow_repeated_bets": True, "merge_same_bets": True},
    "dense_coverage": {"base_unit": 1, "min_bet_count": 24, "wheel_neighbor_radius": 2, "announced_bundles_per_combo": 2},
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
    if method == "dense":
        return generate_dense_casino_combos(cfg, count, seed)
    if method == "hybrid":
        grid_count = count // 2
        random_count = count - grid_count
        return [
            *generate_grid_combos(cfg, grid_count),
            *generate_random_combos(cfg, random_count, seed, combo_id_offset=grid_count),
        ]
    if method == "dense_hybrid":
        grid_count = count // 5
        random_count = count // 5
        dense_count = count - grid_count - random_count
        return [
            *generate_grid_combos(cfg, grid_count),
            *generate_random_combos(cfg, random_count, seed, combo_id_offset=grid_count),
            *generate_dense_casino_combos(cfg, dense_count, seed, combo_id_offset=grid_count + random_count),
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


def generate_dense_casino_combos(
    config: dict[str, Any],
    count: int,
    seed: int | None = None,
    combo_id_offset: int = 0,
) -> list[dict[str, Any]]:
    """Generate casino-style dense table coverage with many small chips."""
    rng = random.Random(seed)
    combos: list[dict[str, Any]] = []
    dense_config = config.get("dense_coverage", {})
    units = sorted(config["bankroll"]["allowed_units"])
    bankroll = int(config["bankroll"]["total"])
    max_stake = int(config["stake_strategy"].get("max_stake_per_bet", max(units)))
    base_unit = min(int(dense_config.get("base_unit", min(units))), max_stake)
    base_unit = max(min(units), base_unit)
    min_bet_count = int(dense_config.get("min_bet_count", 24))
    wheel_neighbor_radius = int(dense_config.get("wheel_neighbor_radius", 2))
    announced_count = int(dense_config.get("announced_bundles_per_combo", 2))

    announced_bundles = build_announced_bundles(base_unit)
    dense_pool = build_dense_inside_pool(base_unit)

    attempts = 0
    max_attempts = max(count * 80, 500)
    while len(combos) < count and attempts < max_attempts:
        attempts += 1
        combo_index = combo_id_offset + len(combos)
        prefix = f"dense_{combo_index}_{attempts}"
        bets: list[Bet] = []
        remaining = bankroll
        sequence = 0

        bundle_names = list(announced_bundles)
        rng.shuffle(bundle_names)
        for bundle_name in bundle_names[: max(0, announced_count)]:
            remaining, sequence = add_dense_templates(
                bets,
                announced_bundles[bundle_name],
                remaining,
                prefix,
                sequence,
            )

        anchor_count = 1 + int(bankroll >= 60) + int(bankroll >= 120)
        anchors = rng.sample(range(37), k=min(anchor_count, 37))
        for anchor in anchors:
            hot_numbers = set(get_wheel_neighbors(anchor, wheel_neighbor_radius))
            neighbor_templates = [bet for bet in dense_pool if hot_numbers.intersection(bet.numbers)]
            rng.shuffle(neighbor_templates)
            max_neighbor_bets = min(len(neighbor_templates), max(6, bankroll // 8))
            remaining, sequence = add_dense_templates(
                bets,
                neighbor_templates[:max_neighbor_bets],
                remaining,
                prefix,
                sequence,
            )

        while remaining >= min(units):
            template = choose_dense_template(dense_pool, rng)
            possible_stakes = [unit for unit in units if unit <= remaining and unit <= max_stake]
            if not possible_stakes:
                break
            stake = choose_dense_stake(possible_stakes, rng)
            bets.append(clone_bet(template, stake, prefix, sequence))
            remaining -= stake
            sequence += 1

        combo = build_combo(f"dense_{combo_index}", bets, config)
        if len(combo["bets"]) < min_bet_count:
            continue
        if combo_is_allowed(combo, config):
            combos.append(combo)

    return combos


def build_announced_bundles(unit: int) -> dict[str, list[Bet]]:
    """Return French announced-bet bundles expressed as legal table bets."""
    return {
        "voisins_zero": [
            make_bet("street", (0, 2, 3), unit * 2, "voisins_zero_trio_0_2_3"),
            make_bet("split", (4, 7), unit, "voisins_zero_split_4_7"),
            make_bet("split", (12, 15), unit, "voisins_zero_split_12_15"),
            make_bet("split", (18, 21), unit, "voisins_zero_split_18_21"),
            make_bet("split", (19, 22), unit, "voisins_zero_split_19_22"),
            make_bet("corner", (25, 26, 28, 29), unit * 2, "voisins_zero_corner_25_26_28_29"),
            make_bet("split", (32, 35), unit, "voisins_zero_split_32_35"),
        ],
        "tiers_du_cylindre": [
            make_bet("split", (5, 8), unit, "tiers_split_5_8"),
            make_bet("split", (10, 11), unit, "tiers_split_10_11"),
            make_bet("split", (13, 16), unit, "tiers_split_13_16"),
            make_bet("split", (23, 24), unit, "tiers_split_23_24"),
            make_bet("split", (27, 30), unit, "tiers_split_27_30"),
            make_bet("split", (33, 36), unit, "tiers_split_33_36"),
        ],
        "orphelins": [
            make_bet("straight", (1,), unit, "orphelins_straight_1"),
            make_bet("split", (6, 9), unit, "orphelins_split_6_9"),
            make_bet("split", (14, 17), unit, "orphelins_split_14_17"),
            make_bet("split", (17, 20), unit, "orphelins_split_17_20"),
            make_bet("split", (31, 34), unit, "orphelins_split_31_34"),
        ],
        "jeu_zero": [
            make_bet("split", (0, 3), unit, "jeu_zero_split_0_3"),
            make_bet("split", (12, 15), unit, "jeu_zero_split_12_15"),
            make_bet("straight", (26,), unit, "jeu_zero_straight_26"),
            make_bet("split", (32, 35), unit, "jeu_zero_split_32_35"),
        ],
    }


def build_dense_inside_pool(unit: int) -> list[Bet]:
    """Return the inside-bet pool used to fill dense casino-style layouts."""
    return [
        *generate_straights(unit),
        *generate_splits(unit),
        *generate_streets(unit),
        *generate_corners(unit),
    ]


def add_dense_templates(
    bets: list[Bet],
    templates: list[Bet],
    remaining: int,
    prefix: str,
    sequence: int,
) -> tuple[int, int]:
    """Append templates while budget remains."""
    for template in templates:
        if remaining <= 0:
            break
        stake = min(template.stake, remaining)
        if stake <= 0:
            break
        bets.append(clone_bet(template, stake, prefix, sequence))
        remaining -= stake
        sequence += 1
    return remaining, sequence


def choose_dense_template(pool: list[Bet], rng: random.Random) -> Bet:
    """Choose dense fill bets while favoring visible chip spread."""
    by_type = {
        "straight": [bet for bet in pool if bet.type == "straight"],
        "split": [bet for bet in pool if bet.type == "split"],
        "street": [bet for bet in pool if bet.type == "street"],
        "corner": [bet for bet in pool if bet.type == "corner"],
    }
    bet_type = rng.choices(
        ("straight", "split", "corner", "street"),
        weights=(0.34, 0.32, 0.24, 0.10),
        k=1,
    )[0]
    return rng.choice(by_type[bet_type])


def choose_dense_stake(possible_stakes: list[int], rng: random.Random) -> int:
    """Choose mostly small chip amounts to mimic dense physical table placement."""
    weighted: list[int] = []
    for stake in possible_stakes:
        if stake == min(possible_stakes):
            weighted.extend([stake] * 6)
        elif stake <= 3:
            weighted.extend([stake] * 3)
        else:
            weighted.append(stake)
    return rng.choice(weighted)


def clone_bet(template: Bet, stake: int, prefix: str, sequence: int) -> Bet:
    """Clone a template with a unique physical-chip id."""
    return make_bet(template.type, template.numbers, stake, f"{prefix}_{sequence}_{template.bet_id}")


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
