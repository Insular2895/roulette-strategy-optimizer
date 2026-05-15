"""CSV, JSON and HTML export helpers."""

from __future__ import annotations

import csv
import html
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
    """Export best combos, best combo detail, number outcomes and board HTML."""
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    paths = {
        "best_combos": output_path / "best_combos.csv",
        "best_combo_detail": output_path / "best_combo_detail.json",
        "number_outcomes": output_path / "number_outcomes.csv",
        "roulette_board_html": output_path / "roulette_board.html",
    }

    export_best_combos(results, paths["best_combos"])
    export_best_combo_detail(results[0] if results else None, paths["best_combo_detail"])
    export_number_outcomes(results, paths["number_outcomes"])
    export_roulette_board_html(results[0] if results else None, paths["roulette_board_html"])
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


def export_report_index(
    output_dir: str | Path = "outputs",
    data_paths: dict[str, Path] | None = None,
    monte_carlo_paths: dict[str, Path] | None = None,
    html_paths: dict[str, Path] | None = None,
) -> Path:
    """Export a local file index linking every generated artifact."""
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    report_path = output_path / "report.html"
    sections = [
        ("Strategy data", data_paths or {}),
        ("Monte Carlo data", monte_carlo_paths or {}),
        ("Visualizations", html_paths or {}),
    ]
    cards = []
    for title, paths in sections:
        links = "\n".join(
            f'<li><a href="{html.escape(path.name)}">{html.escape(path.name)}</a><span>{html.escape(key)}</span></li>'
            for key, path in paths.items()
        )
        cards.append(f"<section><h2>{html.escape(title)}</h2><ul>{links}</ul></section>")

    report_path.write_text(
        f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Roulette Strategy Optimizer Report</title>
  <style>
    body {{ margin: 0; background: #101214; color: #f8fafc; font-family: Arial, sans-serif; }}
    main {{ width: min(1120px, calc(100% - 48px)); margin: 0 auto; padding: 40px 0; }}
    h1 {{ font-size: 42px; margin: 0 0 10px; }}
    p {{ color: #cbd5e1; margin: 0 0 28px; }}
    section {{ border: 1px solid #27313b; border-radius: 8px; padding: 18px; margin: 16px 0; background: #151a1f; }}
    h2 {{ margin: 0 0 14px; font-size: 20px; }}
    ul {{ list-style: none; padding: 0; margin: 0; display: grid; gap: 10px; }}
    li {{ display: flex; justify-content: space-between; gap: 12px; border-top: 1px solid #27313b; padding-top: 10px; }}
    a {{ color: #7dd3fc; font-weight: 700; text-decoration: none; }}
    span {{ color: #94a3b8; }}
  </style>
</head>
<body>
  <main>
    <h1>Roulette Strategy Optimizer Report</h1>
    <p>Open these generated files directly from this folder. No dev server is required.</p>
    {''.join(cards)}
  </main>
</body>
</html>
""",
        encoding="utf-8",
    )
    return report_path


def export_roulette_board_html(result: dict[str, Any] | None, path: Path) -> None:
    """Export an HTML roulette board heatmap for the best strategy."""
    if not result:
        path.write_text("<!doctype html><html><body>No strategy generated.</body></html>", encoding="utf-8")
        return

    outcome_by_number = {outcome["number"]: outcome for outcome in result["outcomes"]}
    rows = [[3 + index * 3, 2 + index * 3, 1 + index * 3] for index in range(12)]
    number_cells = "\n".join(
        render_number_cell(number, outcome_by_number[number])
        for row in rows
        for number in row
    )
    zero_cell = render_number_cell(0, outcome_by_number[0], extra_class="zero")
    chip_plan_svg = render_chip_plan_svg(result["bets"])
    bet_rows = "\n".join(
        f"<tr><td>{index}</td><td><strong>{bet['stake']}€</strong></td><td>{html.escape(bet_type_label(bet))}</td><td>{html.escape(placement_instruction(bet))}</td><td>{html.escape('-'.join(str(number) for number in bet['numbers']))}</td></tr>"
        for index, bet in enumerate(result["bets"], start=1)
    )
    metrics = result["metrics"]

    path.write_text(
        f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Roulette Board - {html.escape(result['combo_id'])}</title>
  <style>
    body {{ margin: 0; background: #101214; color: #f8fafc; font-family: Arial, sans-serif; }}
    main {{ width: min(1280px, calc(100% - 40px)); margin: 0 auto; padding: 30px 0; }}
    h1 {{ margin: 0 0 8px; font-size: 34px; }}
    h2 {{ margin: 28px 0 12px; font-size: 24px; }}
    .hint {{ color: #cbd5e1; margin: 0 0 18px; }}
    .summary {{ display: grid; grid-template-columns: repeat(5, minmax(120px, 1fr)); gap: 10px; margin: 20px 0; }}
    .metric {{ background: #151a1f; border: 1px solid #27313b; border-radius: 8px; padding: 14px; }}
    .metric span {{ color: #94a3b8; display: block; font-size: 12px; }}
    .metric strong {{ font-size: 22px; display: block; margin-top: 8px; }}
    .placement {{ border: 1px solid #27313b; border-radius: 8px; background: #151a1f; padding: 16px; }}
    .placement svg {{ width: 100%; height: auto; display: block; }}
    .chip-note {{ color: #94a3b8; margin: 12px 0 0; font-size: 14px; }}
    .board {{ display: grid; grid-template-columns: 80px 1fr; border: 1px solid #d1d5db; background: #0e402b; }}
    .grid {{ display: grid; grid-template-columns: repeat(12, 1fr); }}
    .cell {{ min-height: 92px; border: 1px solid rgba(255,255,255,0.5); display: grid; align-content: center; justify-items: center; gap: 8px; color: white; }}
    .zero {{ min-height: 276px; }}
    .red {{ background: #8f1d1d; }}
    .black {{ background: #111111; }}
    .green {{ background: #0f5132; }}
    .loss {{ box-shadow: inset 0 0 0 999px rgba(148, 163, 184, 0.09); }}
    .profit {{ box-shadow: inset 0 0 0 999px rgba(34, 197, 94, 0.30); }}
    .hit {{ box-shadow: inset 0 0 0 999px rgba(242, 201, 76, 0.34), 0 0 0 3px #f2c94c inset; }}
    .number {{ font-size: 24px; font-weight: 800; }}
    .net {{ color: #e5e7eb; font-size: 13px; }}
    table {{ width: 100%; border-collapse: collapse; margin-top: 22px; background: #151a1f; }}
    th, td {{ border: 1px solid #27313b; padding: 10px; text-align: left; }}
    th {{ color: #f2c94c; }}
  </style>
</head>
<body>
  <main>
    <h1>{html.escape(result['combo_id'])}</h1>
    <div class="summary">
      {metric_card('Rank', result['rank'])}
      {metric_card('Score', round(float(result['score']), 4))}
      {metric_card('Coverage', percent(metrics['coverage_probability']))}
      {metric_card('Profit probability', percent(metrics['profit_probability']))}
      {metric_card('Max profit', metrics['max_profit'])}
    </div>

    <h2>Plan de pose des jetons</h2>
    <p class="hint">Chaque jeton numerote correspond a une ligne du tableau. C'est uniquement la strategie gagnante du batch : {html.escape(result['combo_id'])}.</p>
    <section class="placement">
      {chip_plan_svg}
      <p class="chip-note">Les paris exterieurs comme impair ou passe sont places dans la zone basse dediee. Les chevaux, carres et transversales sont positionnes au milieu des numeros couverts.</p>
    </section>

    <table>
      <thead><tr><th>#</th><th>Montant</th><th>Type</th><th>Ou placer le jeton</th><th>Numeros couverts</th></tr></thead>
      <tbody>{bet_rows}</tbody>
    </table>

    <h2>Heatmap des resultats</h2>
    <p class="hint">Cette vue montre le gain net obtenu si chaque numero sort.</p>
    <section class="board">
      {zero_cell}
      <div class="grid">{number_cells}</div>
    </section>
  </main>
</body>
</html>
""",
        encoding="utf-8",
    )


def render_number_cell(number: int, outcome: dict[str, Any], extra_class: str = "") -> str:
    """Render one roulette board cell."""
    color = number_color(number)
    tone = "hit" if outcome["is_big_hit"] else "profit" if outcome["is_profitable"] else "loss"
    title = html.escape(outcome["explanation"])
    return (
        f'<div class="cell {extra_class} {color} {tone}" title="{title}">'
        f'<span class="number">{number}</span><span class="net">net {outcome["net_profit"]}</span></div>'
    )


def render_chip_plan_svg(bets: list[dict[str, Any]]) -> str:
    """Render a schematic roulette table with numbered chips for placement."""
    width = 1180
    height = 560
    cell_w = 76
    cell_h = 96
    zero_w = 84
    board_x = 36
    board_y = 36
    outside_y = board_y + cell_h * 3 + 34
    outside_boxes = [
        ("dozen_1", "1st 12", board_x + zero_w, outside_y, cell_w * 4, 54),
        ("dozen_2", "2nd 12", board_x + zero_w + cell_w * 4, outside_y, cell_w * 4, 54),
        ("dozen_3", "3rd 12", board_x + zero_w + cell_w * 8, outside_y, cell_w * 4, 54),
        ("even_money_low", "1-18", board_x + zero_w, outside_y + 66, cell_w * 2, 54),
        ("even_money_even", "PAIR", board_x + zero_w + cell_w * 2, outside_y + 66, cell_w * 2, 54),
        ("even_money_red", "ROUGE", board_x + zero_w + cell_w * 4, outside_y + 66, cell_w * 2, 54),
        ("even_money_black", "NOIR", board_x + zero_w + cell_w * 6, outside_y + 66, cell_w * 2, 54),
        ("even_money_odd", "IMPAIR", board_x + zero_w + cell_w * 8, outside_y + 66, cell_w * 2, 54),
        ("even_money_high", "19-36", board_x + zero_w + cell_w * 10, outside_y + 66, cell_w * 2, 54),
    ]
    outside_lookup = {key: (x + w / 2, y + h / 2) for key, _, x, y, w, h in outside_boxes}

    cells = [
        f'<rect x="{board_x}" y="{board_y}" width="{zero_w}" height="{cell_h * 3}" fill="#0f5132" stroke="#d1d5db" stroke-width="2"/>',
        f'<text x="{board_x + zero_w / 2}" y="{board_y + cell_h * 1.62}" text-anchor="middle" font-size="34" font-weight="800" fill="#ffffff">0</text>',
    ]
    for number in range(1, 37):
        x, y = number_cell_origin(number, board_x, board_y, zero_w, cell_w, cell_h)
        cells.append(f'<rect x="{x}" y="{y}" width="{cell_w}" height="{cell_h}" fill="{number_fill(number)}" stroke="#d1d5db" stroke-width="2"/>')
        cells.append(f'<text x="{x + cell_w / 2}" y="{y + cell_h / 2 + 8}" text-anchor="middle" font-size="24" font-weight="800" fill="#ffffff">{number}</text>')

    outside = [
        f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="4" fill="#123d2b" stroke="#d1d5db" stroke-width="2"/><text x="{x + w / 2}" y="{y + h / 2 + 6}" text-anchor="middle" font-size="20" font-weight="800" fill="#ffffff">{label}</text>'
        for _, label, x, y, w, h in outside_boxes
    ]
    chips = []
    for index, bet in enumerate(bets, start=1):
        x, y = chip_position(bet, board_x, board_y, zero_w, cell_w, cell_h, outside_lookup)
        chips.append(render_chip(index, bet["stake"], x, y))

    return f"""<svg viewBox="0 0 {width} {height}" role="img" aria-label="Plan de pose des jetons">
  <rect width="{width}" height="{height}" rx="10" fill="#0d281d"/>
  <g font-family="Arial, sans-serif">{''.join(cells)}{''.join(outside)}{''.join(chips)}</g>
</svg>"""


def render_chip(index: int, stake: int, x: float, y: float) -> str:
    """Render one numbered chip."""
    radius = 18 if stake < 10 else 21
    return (
        f'<g><circle cx="{x:.1f}" cy="{y:.1f}" r="{radius}" fill="#f8fafc" stroke="#f2c94c" stroke-width="5"/>'
        f'<circle cx="{x:.1f}" cy="{y:.1f}" r="{radius - 7}" fill="#111827"/>'
        f'<text x="{x:.1f}" y="{y - 2:.1f}" text-anchor="middle" font-size="11" font-weight="800" fill="#ffffff">{index}</text>'
        f'<text x="{x:.1f}" y="{y + 11:.1f}" text-anchor="middle" font-size="10" font-weight="800" fill="#f2c94c">{stake}€</text></g>'
    )


def chip_position(
    bet: dict[str, Any],
    board_x: int,
    board_y: int,
    zero_w: int,
    cell_w: int,
    cell_h: int,
    outside_lookup: dict[str, tuple[float, float]],
) -> tuple[float, float]:
    """Calculate a readable chip placement position."""
    bet_id = bet["bet_id"]
    if bet_id in outside_lookup:
        return outside_lookup[bet_id]
    if bet["type"] == "dozen":
        dozen_key = f"dozen_{((min(bet['numbers']) - 1) // 12) + 1}"
        if dozen_key in outside_lookup:
            return outside_lookup[dozen_key]

    centers = [number_center(number, board_x, board_y, zero_w, cell_w, cell_h) for number in bet["numbers"]]
    x = sum(point[0] for point in centers) / len(centers)
    y = sum(point[1] for point in centers) / len(centers)
    return x, y


def number_center(number: int, board_x: int, board_y: int, zero_w: int, cell_w: int, cell_h: int) -> tuple[float, float]:
    """Return center point for a roulette number on the schematic table."""
    if number == 0:
        return board_x + zero_w / 2, board_y + cell_h * 1.5
    x, y = number_cell_origin(number, board_x, board_y, zero_w, cell_w, cell_h)
    return x + cell_w / 2, y + cell_h / 2


def number_cell_origin(number: int, board_x: int, board_y: int, zero_w: int, cell_w: int, cell_h: int) -> tuple[int, int]:
    """Return top-left point for a roulette number cell."""
    column = (number - 1) // 3
    row = 2 - ((number - 1) % 3)
    return board_x + zero_w + column * cell_w, board_y + row * cell_h


def number_fill(number: int) -> str:
    """Return SVG fill for a roulette number."""
    if number == 0:
        return "#0f5132"
    return "#8f1d1d" if number_color(number) == "red" else "#111111"


def bet_type_label(bet: dict[str, Any]) -> str:
    """Return French display label for a bet."""
    labels = {
        "straight": "Plein",
        "split": "Cheval",
        "street": "Transversale",
        "corner": "Carre",
        "sixline": "Sixain",
        "dozen": "Douzaine",
        "column": "Colonne",
        "even_money": "Chance simple",
    }
    return labels.get(bet["type"], bet["type"])


def placement_instruction(bet: dict[str, Any]) -> str:
    """Return a human-readable placement instruction."""
    numbers = "-".join(str(number) for number in bet["numbers"])
    if bet["type"] == "straight":
        return f"Sur le numero {bet['numbers'][0]}"
    if bet["type"] == "split":
        return f"A cheval entre {numbers}"
    if bet["type"] == "street":
        return f"Sur la ligne {numbers}"
    if bet["type"] == "corner":
        return f"A l'intersection du carre {numbers}"
    if bet["type"] == "sixline":
        return f"Sur la double ligne {numbers}"
    if bet["type"] == "dozen":
        return f"Sur la douzaine couvrant {numbers}"
    if bet["type"] == "column":
        return f"Sur la colonne couvrant {numbers}"
    if bet["bet_id"] == "even_money_odd":
        return "Sur IMPAIR"
    if bet["bet_id"] == "even_money_even":
        return "Sur PAIR"
    if bet["bet_id"] == "even_money_low":
        return "Sur 1-18"
    if bet["bet_id"] == "even_money_high":
        return "Sur 19-36"
    if bet["bet_id"] == "even_money_red":
        return "Sur ROUGE"
    if bet["bet_id"] == "even_money_black":
        return "Sur NOIR"
    return f"Sur {numbers}"


def number_color(number: int) -> str:
    """Return display color class for a roulette number."""
    red = {1, 3, 5, 7, 9, 12, 14, 16, 18, 19, 21, 23, 25, 27, 30, 32, 34, 36}
    if number == 0:
        return "green"
    return "red" if number in red else "black"


def metric_card(label: str, value: Any) -> str:
    """Render one metric card."""
    return f'<div class="metric"><span>{html.escape(str(label))}</span><strong>{html.escape(str(value))}</strong></div>'


def percent(value: float) -> str:
    """Format a ratio as a percentage."""
    return f"{float(value) * 100:.1f}%"


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
