"""Roulette bet type definitions."""

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


def get_payout(bet_type: str) -> int:
    """Return the roulette payout for a supported bet type."""
    return PAYOUTS[bet_type]
