"""money utilities for precise decimal calculations."""

from decimal import Decimal, ROUND_HALF_UP


def to_decimal(amount):
    """convert amount to decimal with 2 decimal places."""
    return Decimal(str(amount)).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)


def round_money(amount):
    """round money to 2 decimal places."""
    return to_decimal(amount)


def is_positive(amount):
    """check if amount is positive."""
    return to_decimal(amount) > 0
