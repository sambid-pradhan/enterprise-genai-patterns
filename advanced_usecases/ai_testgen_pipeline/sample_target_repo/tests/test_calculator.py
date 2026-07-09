from decimal import Decimal
import pytest
import sys
from pathlib import Path

# Ensure the repository's `src` directory is importable during tests
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from sample_app import calculator


def test_add_basic():
    a = Decimal("1.1")
    b = Decimal("2.2")
    result = calculator.add(a, b)
    assert isinstance(result, Decimal)
    assert result == Decimal("3.3")


def test_add_with_zero():
    result = calculator.add(Decimal("4.25"), Decimal("0"))
    assert isinstance(result, Decimal)
    assert result == Decimal("4.25")


def test_subtract_basic():
    result = calculator.subtract(Decimal("5.5"), Decimal("2.25"))
    assert isinstance(result, Decimal)
    assert result == Decimal("3.25")


def test_multiply_basic():
    result = calculator.multiply(Decimal("3.5"), Decimal("2"))
    assert isinstance(result, Decimal)
    assert result == Decimal("7.0")


@pytest.mark.parametrize(
    "numerator,denominator,expected",
    [
        (Decimal("10"), Decimal("2"), Decimal("5")),
        (Decimal("1"), Decimal("2"), Decimal("0.5")),
        (Decimal("-6"), Decimal("3"), Decimal("-2")),
    ],
)
def test_divide_normal(numerator, denominator, expected):
    result = calculator.divide(numerator, denominator)
    assert isinstance(result, Decimal)
    assert result == expected


def test_divide_zero_denominator_raises():
    with pytest.raises(ValueError, match="denominator must not be zero"):
        calculator.divide(Decimal("1"), Decimal("0"))


@pytest.mark.parametrize(
    "amount,percent,expected",
    [
        (Decimal("100"), Decimal("0"), Decimal("100")),
        (Decimal("100"), Decimal("100"), Decimal("0")),
        (Decimal("200"), Decimal("50"), Decimal("100")),
        (Decimal("80"), Decimal("12.5"), Decimal("70")),
    ],
)
def test_apply_discount_normal(amount, percent, expected):
    result = calculator.apply_discount(amount, percent)
    assert isinstance(result, Decimal)
    assert result == expected


def test_apply_discount_negative_amount_raises():
    with pytest.raises(ValueError, match="amount must not be negative"):
        calculator.apply_discount(Decimal("-1"), Decimal("10"))


@pytest.mark.parametrize("bad_percent", [Decimal("-0.1"), Decimal("100.1")])
def test_apply_discount_percent_out_of_range_raises(bad_percent):
    with pytest.raises(ValueError, match="percent must be between 0 and 100"):
        calculator.apply_discount(Decimal("10"), bad_percent)
