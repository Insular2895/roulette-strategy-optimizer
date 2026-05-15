"""Command line entry point for the roulette optimizer."""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any


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
    return parser


def apply_overrides(config: dict[str, Any], args: argparse.Namespace) -> dict[str, Any]:
    """Apply CLI overrides to the loaded config."""
    if args.profile:
        config.setdefault("objective", {})["profile"] = args.profile
    if args.bankroll is not None:
        config.setdefault("bankroll", {})["total"] = args.bankroll
    if args.units:
        config.setdefault("bankroll", {})["allowed_units"] = args.units
    return config


def main() -> int:
    """Run the optimizer CLI."""
    parser = build_parser()
    args = parser.parse_args()
    config = apply_overrides(load_config(args.config), args)

    profile = config.get("objective", {}).get("profile", "balanced")
    bankroll = config.get("bankroll", {}).get("total")
    units = config.get("bankroll", {}).get("allowed_units", [])
    print(f"Roulette Strategy Optimizer ready: profile={profile}, bankroll={bankroll}, units={units}")
    print("Pipeline implementation starts in the next backend step.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
