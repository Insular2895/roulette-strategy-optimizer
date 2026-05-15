"""CSV, JSON and HTML export helpers."""

from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import Any


BEST_COMBOS_COLUMNS = [
    "combo_id",
    "rank",
    "profile",
    "score",
    "total_staked",
    "coverage_probability",
    "profit_probability",
    "avg_profit_if_win",
    "max_profit",
    "min_profit",
    "expected_value",
    "big_hit_probability",
    "variance",
]

NUMBER_OUTCOMES_COLUMNS = [
    "combo_id",
    "number",
    "gross_return",
    "net_profit",
    "is_covered",
    "is_profitable",
    "is_big_hit",
    "winning_bets",
    "explanation",
]

MONTE_CARLO_RESULTS_COLUMNS = [
    "combo_id",
    "sessions",
    "spins_per_session",
    "final_bankroll_avg",
    "final_bankroll_median",
    "probability_profit",
    "probability_bust",
    "avg_max_drawdown",
    "max_drawdown_seen",
    "biggest_hit_seen",
    "avg_hit_frequency",
    "big_hit_frequency",
]

MONTE_CARLO_PATHS_COLUMNS = [
    "combo_id",
    "session_id",
    "spin_index",
    "bankroll",
]


def export_outputs(results: list[dict[str, Any]], output_dir: str | Path = "outputs") -> dict[str, Path]:
    """Export best combos, best combo detail and number outcomes."""
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    paths = {
        "best_combos": output_path / "best_combos.csv",
        "best_combo_detail": output_path / "best_combo_detail.json",
        "number_outcomes": output_path / "number_outcomes.csv",
    }

    export_best_combos(results, paths["best_combos"])
    export_best_combo_detail(results[0] if results else None, paths["best_combo_detail"])
    export_number_outcomes(results, paths["number_outcomes"])
    return paths


def export_best_combos(results: list[dict[str, Any]], path: Path) -> None:
    """Export ranked strategy summary rows."""
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=BEST_COMBOS_COLUMNS)
        writer.writeheader()
        for result in results:
            metrics = result["metrics"]
            writer.writerow(
                {
                    "combo_id": result["combo_id"],
                    "rank": result["rank"],
                    "profile": result["profile"],
                    "score": result["score"],
                    "total_staked": metrics["total_staked"],
                    "coverage_probability": metrics["coverage_probability"],
                    "profit_probability": metrics["profit_probability"],
                    "avg_profit_if_win": metrics["avg_profit_if_win"],
                    "max_profit": metrics["max_profit"],
                    "min_profit": metrics["min_profit"],
                    "expected_value": metrics["expected_value"],
                    "big_hit_probability": metrics["big_hit_probability"],
                    "variance": metrics["variance"],
                }
            )


def export_best_combo_detail(result: dict[str, Any] | None, path: Path) -> None:
    """Export full JSON detail for the best combo."""
    payload = result or {}
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def export_number_outcomes(results: list[dict[str, Any]], path: Path) -> None:
    """Export one row per combo and roulette number."""
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=NUMBER_OUTCOMES_COLUMNS)
        writer.writeheader()
        for result in results:
            for outcome in result["outcomes"]:
                writer.writerow(
                    {
                        "combo_id": result["combo_id"],
                        "number": outcome["number"],
                        "gross_return": outcome["gross_return"],
                        "net_profit": outcome["net_profit"],
                        "is_covered": outcome["is_covered"],
                        "is_profitable": outcome["is_profitable"],
                        "is_big_hit": outcome["is_big_hit"],
                        "winning_bets": json.dumps(outcome["winning_bets"]),
                        "explanation": outcome["explanation"],
                    }
                )


def export_monte_carlo(simulation: dict[str, list[dict[str, Any]]], output_dir: str | Path = "outputs") -> dict[str, Path]:
    """Export Monte Carlo aggregate metrics and bankroll paths."""
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    paths = {
        "monte_carlo_results": output_path / "monte_carlo_results.csv",
        "monte_carlo_paths": output_path / "monte_carlo_paths.csv",
    }
    write_csv(paths["monte_carlo_results"], MONTE_CARLO_RESULTS_COLUMNS, simulation["results"])
    write_csv(paths["monte_carlo_paths"], MONTE_CARLO_PATHS_COLUMNS, simulation["paths"])
    return paths


def write_csv(path: Path, columns: list[str], rows: list[dict[str, Any]]) -> None:
    """Write selected columns to CSV."""
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=columns)
        writer.writeheader()
        for row in rows:
            writer.writerow({column: row.get(column) for column in columns})
