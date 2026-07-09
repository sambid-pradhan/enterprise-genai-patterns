from decimal import Decimal


def add(left: Decimal, right: Decimal) -> Decimal:
    return left + right


def subtract(left: Decimal, right: Decimal) -> Decimal:
    return left - right


def multiply(left: Decimal, right: Decimal) -> Decimal:
    return left * right


def divide(numerator: Decimal, denominator: Decimal) -> Decimal:
    if denominator == 0:
        raise ValueError("denominator must not be zero")
    return numerator / denominator


def apply_discount(amount: Decimal, percent: Decimal) -> Decimal:
    if amount < 0:
        raise ValueError("amount must not be negative")
    if percent < 0 or percent > 100:
        raise ValueError("percent must be between 0 and 100")
    return amount * (Decimal("1") - percent / Decimal("100"))
