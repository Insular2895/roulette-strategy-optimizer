"""CSV, JSON and HTML export helpers."""

from __future__ import annotations

import csv
import json
from pathlib import Path
from statistics import mean, median
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


def export_monte_carlo_html(
    simulation: dict[str, list[dict[str, Any]]],
    output_dir: str | Path = "outputs",
    max_paths: int = 1000,
) -> dict[str, Path]:
    """Export Plotly HTML views for Monte Carlo paths, summary and comparison."""
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    paths = {
        "monte_carlo_paths_html": output_path / "monte_carlo_paths.html",
        "monte_carlo_summary_html": output_path / "monte_carlo_summary.html",
        "monte_carlo_comparison_html": output_path / "monte_carlo_comparison.html",
    }

    paths["monte_carlo_paths_html"].write_text(build_paths_html(simulation["paths"], max_paths), encoding="utf-8")
    paths["monte_carlo_summary_html"].write_text(build_summary_html(simulation["results"], simulation["paths"]), encoding="utf-8")
    paths["monte_carlo_comparison_html"].write_text(build_comparison_html(simulation["results"]), encoding="utf-8")
    return paths


def build_paths_html(paths: list[dict[str, Any]], max_paths: int) -> str:
    """Build Monte Carlo path HTML with individual and average curves."""
    grouped = group_paths(paths)
    traces: list[dict[str, Any]] = []

    for index, ((combo_id, session_id), points) in enumerate(grouped.items()):
        if index >= max_paths:
            break
        traces.append(
            {
                "x": [point["spin_index"] for point in points],
                "y": [point["bankroll"] for point in points],
                "type": "scatter",
                "mode": "lines",
                "name": f"{combo_id} / session {session_id}",
                "line": {"width": 1, "color": "rgba(80, 160, 220, 0.18)"},
                "hoverinfo": "skip",
                "showlegend": False,
            }
        )

    for combo_id, points_by_spin in group_by_combo_and_spin(paths).items():
        spins = sorted(points_by_spin)
        traces.append(
            {
                "x": spins,
                "y": [mean(points_by_spin[spin]) for spin in spins],
                "type": "scatter",
                "mode": "lines",
                "name": f"{combo_id} average",
                "line": {"width": 4},
            }
        )
        traces.append(
            {
                "x": spins,
                "y": [median(points_by_spin[spin]) for spin in spins],
                "type": "scatter",
                "mode": "lines",
                "name": f"{combo_id} median",
                "line": {"width": 2, "dash": "dash"},
            }
        )

    return plotly_html(
        "Monte Carlo Paths",
        traces,
        {"xaxis": {"title": "Spin"}, "yaxis": {"title": "Bankroll"}, "hovermode": "x unified"},
    )


def build_summary_html(results: list[dict[str, Any]], paths: list[dict[str, Any]]) -> str:
    """Build summary HTML with final bankroll distribution and drawdowns."""
    final_bankrolls = final_bankroll_by_session(paths)
    traces = [
        {
            "x": list(final_bankrolls.values()),
            "type": "histogram",
            "name": "Final bankroll distribution",
            "marker": {"color": "#2dd4bf"},
        },
        {
            "x": [result["combo_id"] for result in results],
            "y": [result["avg_max_drawdown"] for result in results],
            "type": "bar",
            "name": "Average max drawdown",
            "marker": {"color": "#f2c94c"},
            "xaxis": "x2",
            "yaxis": "y2",
        },
    ]
    layout = {
        "grid": {"rows": 1, "columns": 2, "pattern": "independent"},
        "xaxis": {"title": "Final bankroll"},
        "yaxis": {"title": "Sessions"},
        "xaxis2": {"title": "Strategy"},
        "yaxis2": {"title": "Drawdown"},
    }
    return plotly_html("Monte Carlo Summary", traces, layout)


def build_comparison_html(results: list[dict[str, Any]]) -> str:
    """Build strategy comparison HTML."""
    combo_ids = [result["combo_id"] for result in results]
    traces = [
        {"x": combo_ids, "y": [result["final_bankroll_avg"] for result in results], "type": "bar", "name": "Final bankroll avg"},
        {"x": combo_ids, "y": [result["probability_profit"] for result in results], "type": "bar", "name": "Probability profit"},
        {"x": combo_ids, "y": [result["probability_bust"] for result in results], "type": "bar", "name": "Probability bust"},
        {"x": combo_ids, "y": [result["biggest_hit_seen"] for result in results], "type": "bar", "name": "Biggest hit seen"},
        {"x": combo_ids, "y": [result["big_hit_frequency"] for result in results], "type": "bar", "name": "Big hit frequency"},
    ]
    return plotly_html("Monte Carlo Comparison", traces, {"barmode": "group", "xaxis": {"title": "Strategy"}})


def plotly_html(title: str, traces: list[dict[str, Any]], layout: dict[str, Any]) -> str:
    """Build a standalone HTML document using Plotly from CDN."""
    full_layout = {"title": title, "template": "plotly_dark", **layout}
    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{title}</title>
  <script src="https://cdn.plot.ly/plotly-2.32.0.min.js"></script>
  <style>
    body {{ margin: 0; background: #111111; color: #f4f4f4; font-family: Arial, sans-serif; }}
    #chart {{ width: 100vw; height: 100vh; }}
  </style>
</head>
<body>
  <div id="chart"></div>
  <script>
    const traces = {json.dumps(traces)};
    const layout = {json.dumps(full_layout)};
    Plotly.newPlot('chart', traces, layout, {{responsive: true}});
  </script>
</body>
</html>
"""


def group_paths(paths: list[dict[str, Any]]) -> dict[tuple[str, int], list[dict[str, Any]]]:
    """Group path rows by combo and session."""
    grouped: dict[tuple[str, int], list[dict[str, Any]]] = {}
    for point in paths:
        grouped.setdefault((point["combo_id"], int(point["session_id"])), []).append(point)
    return grouped


def group_by_combo_and_spin(paths: list[dict[str, Any]]) -> dict[str, dict[int, list[float]]]:
    """Group bankroll values by combo and spin."""
    grouped: dict[str, dict[int, list[float]]] = {}
    for point in paths:
        combo = grouped.setdefault(point["combo_id"], {})
        combo.setdefault(int(point["spin_index"]), []).append(float(point["bankroll"]))
    return grouped


def final_bankroll_by_session(paths: list[dict[str, Any]]) -> dict[tuple[str, int], float]:
    """Return final bankroll for each combo/session path."""
    finals: dict[tuple[str, int], tuple[int, float]] = {}
    for point in paths:
        key = (point["combo_id"], int(point["session_id"]))
        spin_index = int(point["spin_index"])
        if key not in finals or spin_index >= finals[key][0]:
            finals[key] = (spin_index, float(point["bankroll"]))
    return {key: value for key, (_, value) in finals.items()}
