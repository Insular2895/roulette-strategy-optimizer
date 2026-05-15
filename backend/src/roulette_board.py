"""European roulette board primitives."""

EUROPEAN_NUMBERS = tuple(range(37))


def get_numbers() -> tuple[int, ...]:
    """Return all European roulette outcomes, from 0 to 36."""
    return EUROPEAN_NUMBERS
