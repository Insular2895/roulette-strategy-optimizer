"""Roulette bet type definitions."""

from __future__ import annotations

from dataclasses import dataclass

from .roulette_board import BLACK_NUMBERS, RED_NUMBERS

PAYOUTS = {
    "straight": 35,
    "split": 17,
    "street": 11,
    "corner": 8,
    "sixline": 5,
    "dozen": 2,
    "column": 2,
    "even_money": 1,
}


@dataclass(frozen=True)
class Bet:
    """A roulette bet with its covered numbers, stake and payout."""

    bet_id: str
    type: str
    numbers: tuple[int, ...]
    stake: int
    payout: int

    def to_dict(self) -> dict:
        """Serialize the bet to the public JSON shape."""
        return {
            "bet_id": self.bet_id,
            "type": self.type,
            "numbers": list(self.numbers),
            "stake": self.stake,
            "payout": self.payout,
        }


def get_payout(bet_type: str) -> int:
    """Return the roulette payout for a supported bet type."""
    return PAYOUTS[bet_type]


def make_bet(bet_type: str, numbers: tuple[int, ...] | list[int], stake: int = 1, bet_id: str | None = None) -> Bet:
    """Create and validate a roulette bet."""
    normalized_numbers = tuple(sorted(numbers))
    validate_bet(bet_type, normalized_numbers, stake)
    return Bet(
        bet_id=bet_id or build_bet_id(bet_type, normalized_numbers),
        type=bet_type,
        numbers=normalized_numbers,
        stake=stake,
        payout=get_payout(bet_type),
    )


def validate_bet(bet_type: str, numbers: tuple[int, ...], stake: int) -> None:
    """Validate a supported bet type, covered numbers and stake."""
    if bet_type not in PAYOUTS:
        raise ValueError(f"unsupported bet type: {bet_type}")
    if stake <= 0:
        raise ValueError("stake must be positive")
    if any(number < 0 or number > 36 for number in numbers):
        raise ValueError(f"invalid numbers for {bet_type}: {numbers}")

    expected_coverage = {
        "straight": 1,
        "split": 2,
        "street": 3,
        "corner": 4,
        "sixline": 6,
        "dozen": 12,
        "column": 12,
        "even_money": 18,
    }[bet_type]
    if len(set(numbers)) != expected_coverage:
        raise ValueError(f"{bet_type} must cover {expected_coverage} unique numbers")


def build_bet_id(bet_type: str, numbers: tuple[int, ...]) -> str:
    """Build a stable bet identifier from type and numbers."""
    return f"{bet_type}_{'_'.join(str(number) for number in numbers)}"


def generate_straights(stake: int = 1) -> list[Bet]:
    """Generate all straight-up bets."""
    return [make_bet("straight", (number,), stake) for number in range(37)]


def generate_splits(stake: int = 1) -> list[Bet]:
    """Generate all legal split bets on the European table layout."""
    pairs: set[tuple[int, int]] = set()
    for number in range(1, 34):
        pairs.add((number, number + 3))
    for row_start in range(1, 37, 3):
        pairs.add((row_start, row_start + 1))
        pairs.add((row_start + 1, row_start + 2))
    pairs.update({(0, 1), (0, 2), (0, 3)})
    return [make_bet("split", pair, stake) for pair in sorted(pairs)]


def generate_streets(stake: int = 1) -> list[Bet]:
    """Generate all street bets."""
    return [make_bet("street", (row_start, row_start + 1, row_start + 2), stake) for row_start in range(1, 37, 3)]


def generate_corners(stake: int = 1) -> list[Bet]:
    """Generate all legal corner bets."""
    corners: list[Bet] = []
    for row_start in range(1, 34, 3):
        corners.append(make_bet("corner", (row_start, row_start + 1, row_start + 3, row_start + 4), stake))
        corners.append(make_bet("corner", (row_start + 1, row_start + 2, row_start + 4, row_start + 5), stake))
    return corners


def generate_sixlines(stake: int = 1) -> list[Bet]:
    """Generate all sixline bets."""
    return [make_bet("sixline", tuple(range(row_start, row_start + 6)), stake) for row_start in range(1, 34, 3)]


def generate_dozens(stake: int = 1) -> list[Bet]:
    """Generate the three dozen bets."""
    return [
        make_bet("dozen", tuple(range(1, 13)), stake, "dozen_1"),
        make_bet("dozen", tuple(range(13, 25)), stake, "dozen_2"),
        make_bet("dozen", tuple(range(25, 37)), stake, "dozen_3"),
    ]


def generate_columns(stake: int = 1) -> list[Bet]:
    """Generate the three column bets."""
    return [
        make_bet("column", tuple(range(1, 35, 3)), stake, "column_1"),
        make_bet("column", tuple(range(2, 36, 3)), stake, "column_2"),
        make_bet("column", tuple(range(3, 37, 3)), stake, "column_3"),
    ]


def generate_even_money(stake: int = 1) -> list[Bet]:
    """Generate even-money bets."""
    return [
        make_bet("even_money", tuple(range(1, 19)), stake, "even_money_low"),
        make_bet("even_money", tuple(range(19, 37)), stake, "even_money_high"),
        make_bet("even_money", tuple(number for number in range(1, 37) if number % 2 == 0), stake, "even_money_even"),
        make_bet("even_money", tuple(number for number in range(1, 37) if number % 2 == 1), stake, "even_money_odd"),
        make_bet("even_money", tuple(sorted(RED_NUMBERS)), stake, "even_money_red"),
        make_bet("even_money", tuple(sorted(BLACK_NUMBERS)), stake, "even_money_black"),
    ]


def generate_all_bets(stake: int = 1) -> list[Bet]:
    """Generate all supported legal bets."""
    return [
        *generate_straights(stake),
        *generate_splits(stake),
        *generate_streets(stake),
        *generate_corners(stake),
        *generate_sixlines(stake),
        *generate_dozens(stake),
        *generate_columns(stake),
        *generate_even_money(stake),
    ]
