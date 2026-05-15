"""European roulette board primitives."""

EUROPEAN_NUMBERS = tuple(range(37))
RED_NUMBERS = frozenset({1, 3, 5, 7, 9, 12, 14, 16, 18, 19, 21, 23, 25, 27, 30, 32, 34, 36})
BLACK_NUMBERS = frozenset(number for number in range(1, 37) if number not in RED_NUMBERS)

FIRST_DOZEN = frozenset(range(1, 13))
SECOND_DOZEN = frozenset(range(13, 25))
THIRD_DOZEN = frozenset(range(25, 37))

FIRST_COLUMN = frozenset(range(1, 35, 3))
SECOND_COLUMN = frozenset(range(2, 36, 3))
THIRD_COLUMN = frozenset(range(3, 37, 3))


def get_numbers() -> tuple[int, ...]:
    """Return all European roulette outcomes, from 0 to 36."""
    return EUROPEAN_NUMBERS


def get_color(number: int) -> str:
    """Return green, red or black for a roulette number."""
    validate_number(number)
    if number == 0:
        return "green"
    if number in RED_NUMBERS:
        return "red"
    return "black"


def get_dozen(number: int) -> int | None:
    """Return the dozen index for a number, or None for zero."""
    validate_number(number)
    if number == 0:
        return None
    return ((number - 1) // 12) + 1


def get_column(number: int) -> int | None:
    """Return the column index for a number, or None for zero."""
    validate_number(number)
    if number == 0:
        return None
    return ((number - 1) % 3) + 1


def is_even(number: int) -> bool:
    """Return whether a non-zero roulette number is even."""
    validate_number(number)
    return number != 0 and number % 2 == 0


def is_odd(number: int) -> bool:
    """Return whether a non-zero roulette number is odd."""
    validate_number(number)
    return number != 0 and number % 2 == 1


def is_low(number: int) -> bool:
    """Return whether a number is in 1-18."""
    validate_number(number)
    return 1 <= number <= 18


def is_high(number: int) -> bool:
    """Return whether a number is in 19-36."""
    validate_number(number)
    return 19 <= number <= 36


def validate_number(number: int) -> None:
    """Raise ValueError if number is not a European roulette outcome."""
    if number not in EUROPEAN_NUMBERS:
        raise ValueError(f"invalid European roulette number: {number}")
