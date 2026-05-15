"""Command line entry point for the roulette optimizer."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Any

if __package__ in {None, ""}:
    sys.path.append(str(Path(__file__).resolve().parents[2]))
    from backend.src.monte_carlo import rerank_by_monte_carlo, run_monte_carlo
    from backend.src.optimizer import optimize
    from backend.src.visual_export import export_monte_carlo, export_monte_carlo_html, export_outputs, export_report_index
else:
    from .monte_carlo import rerank_by_monte_carlo, run_monte_carlo
    from .optimizer import optimize
    from .visual_export import export_monte_carlo, export_monte_carlo_html, export_outputs, export_report_index


DEFAULT_CONFIG_PATH = Path(__file__).resolve().parents[2] / "config.yaml"


def parse_units(value: str) -> list[int]:
    """Parse comma-separated chip units from the CLI."""
    try:
        units = [int(part.strip()) for part in value.split(",") if part.strip()]
    except ValueError as exc:
        raise argparse.ArgumentTypeError("units must be comma-separated integers") from exc

    if not units:
        raise argparse.ArgumentTypeError("at least one unit is required")
    if any(unit <= 0 for unit in units):
        raise argparse.ArgumentTypeError("units must be positive integers")
    return units


def load_config(path: Path) -> dict[str, Any]:
    """Load YAML configuration."""
    try:
        import yaml
    except ModuleNotFoundError:
        return load_simple_yaml(path)

    with path.open("r", encoding="utf-8") as handle:
        data = yaml.safe_load(handle) or {}
    if not isinstance(data, dict):
        raise ValueError("config file must contain a YAML mapping")
    return data


def parse_scalar(value: str) -> Any:
    """Parse the scalar subset used by the project config."""
    value = value.strip()
    if value in {"true", "false"}:
        return value == "true"
    if value.startswith("[") and value.endswith("]"):
        raw_items = value[1:-1].strip()
        if not raw_items:
            return []
        return [parse_scalar(item) for item in raw_items.split(",")]
    try:
        if "." in value:
            return float(value)
        return int(value)
    except ValueError:
        return value


def load_simple_yaml(path: Path) -> dict[str, Any]:
    """Load the small YAML subset used by config.yaml when PyYAML is absent."""
    root: dict[str, Any] = {}
    stack: list[tuple[int, dict[str, Any]]] = [(-1, root)]

    for raw_line in path.read_text(encoding="utf-8").splitlines():
        if not raw_line.strip() or raw_line.lstrip().startswith("#"):
            continue

        indent = len(raw_line) - len(raw_line.lstrip(" "))
        key, separator, value = raw_line.strip().partition(":")
        if not separator:
            raise ValueError(f"invalid config line: {raw_line}")

        while stack and indent <= stack[-1][0]:
            stack.pop()

        parent = stack[-1][1]
        if value.strip():
            parent[key] = parse_scalar(value)
        else:
            child: dict[str, Any] = {}
            parent[key] = child
            stack.append((indent, child))

    return root


def build_parser() -> argparse.ArgumentParser:
    """Build the optimizer CLI parser."""
    parser = argparse.ArgumentParser(description="Roulette Strategy Optimizer")
    parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG_PATH, help="Path to config.yaml")
    parser.add_argument("--profile", choices=("safe", "balanced", "aggressive"), help="Optimization profile")
    parser.add_argument("--bankroll", type=int, help="Total bankroll allocated to strategy generation")
    parser.add_argument("--units", type=parse_units, help="Comma-separated allowed stake units, for example 1,2,3,5,10")
    parser.add_argument("--combos-to-generate", type=int, help="Override search.combos_to_generate")
    parser.add_argument("--keep-top-n", type=int, help="Override search.keep_top_n")
    parser.add_argument("--monte-carlo-sessions", type=int, help="Override monte_carlo.sessions")
    parser.add_argument("--spins-per-session", type=int, help="Override monte_carlo.spins_per_session")
    parser.add_argument("--initial-bankroll", type=int, help="Override monte_carlo.initial_bankroll")
    parser.add_argument("--output-dir", type=Path, default=Path("outputs"), help="Output directory")
    parser.add_argument("--seed", type=int, default=42, help="Random seed for reproducible runs")
    parser.add_argument("--skip-monte-carlo", action="store_true", help="Only run theoretical optimization exports")
    parser.add_argument("--disable-refinement", action="store_true", help="Disable local stake refinement")
    parser.add_argument("--refinement-variants", type=int, help="Override refinement.variants_per_strategy")
    return parser


def apply_overrides(config: dict[str, Any], args: argparse.Namespace) -> dict[str, Any]:
    """Apply CLI overrides to the loaded config."""
    if args.profile:
        config.setdefault("objective", {})["profile"] = args.profile
    if args.bankroll is not None:
        config.setdefault("bankroll", {})["total"] = args.bankroll
    if args.units:
        config.setdefault("bankroll", {})["allowed_units"] = args.units
    if args.combos_to_generate is not None:
        config.setdefault("search", {})["combos_to_generate"] = args.combos_to_generate
    if args.keep_top_n is not None:
        config.setdefault("search", {})["keep_top_n"] = args.keep_top_n
    if args.monte_carlo_sessions is not None:
        config.setdefault("monte_carlo", {})["sessions"] = args.monte_carlo_sessions
    if args.spins_per_session is not None:
        config.setdefault("monte_carlo", {})["spins_per_session"] = args.spins_per_session
    if args.initial_bankroll is not None:
        config.setdefault("monte_carlo", {})["initial_bankroll"] = args.initial_bankroll
    if args.disable_refinement:
        config.setdefault("refinement", {})["enabled"] = False
    if args.refinement_variants is not None:
        config.setdefault("refinement", {})["variants_per_strategy"] = args.refinement_variants
    return config


def main() -> int:
    """Run the optimizer CLI."""
    parser = build_parser()
    args = parser.parse_args()
    config = apply_overrides(load_config(args.config), args)

    profile = config.get("objective", {}).get("profile", "balanced")
    bankroll = config.get("bankroll", {}).get("total")
    units = config.get("bankroll", {}).get("allowed_units", [])
    print(f"Roulette Strategy Optimizer: profile={profile}, bankroll={bankroll}, units={units}")

    strategies = optimize(config, seed=args.seed)
    data_paths = export_outputs(strategies, args.output_dir)
    print(f"Theoretical exports: {', '.join(str(path) for path in data_paths.values())}")

    monte_carlo_paths = {}
    html_paths = {}
    if not args.skip_monte_carlo:
        monte_carlo_config = config.get("monte_carlo", {})
        simulation = run_monte_carlo(
            strategies,
            sessions=int(monte_carlo_config.get("sessions", 10000)),
            spins_per_session=int(monte_carlo_config.get("spins_per_session", 100)),
            initial_bankroll=float(monte_carlo_config.get("initial_bankroll", 1000)),
            seed=args.seed,
        )
        strategies = rerank_by_monte_carlo(strategies, simulation, config.get("robust_filter", {}))
        data_paths = export_outputs(strategies, args.output_dir)
        monte_carlo_paths = export_monte_carlo(simulation, args.output_dir)
        html_paths = export_monte_carlo_html(simulation, args.output_dir)
        print("Final ranking: Monte Carlo robust score")
        print(f"Monte Carlo exports: {', '.join(str(path) for path in monte_carlo_paths.values())}")
        print(f"HTML exports: {', '.join(str(path) for path in html_paths.values())}")

    report_path = export_report_index(args.output_dir, data_paths, monte_carlo_paths, html_paths)
    print(f"Report index: {report_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
