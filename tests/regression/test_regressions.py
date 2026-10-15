"""Regression tests: one per bug found during this project. Never delete these.

Each test pins the exact input that originally failed. If a test here fails
after a change, the change has reintroduced a bug.
"""

from decimal import Decimal

import pytest

from quote_service.quote import QuoteError, quote


def test_bug_101_discount_above_100_is_rejected():
    """BUG-101: discount_pct=150 was accepted, so the total could go negative.

    Found by: unit test test_discount_must_be_between_0_and_100, which failed
    with "DID NOT RAISE" on the v1 code.
    """
    with pytest.raises(QuoteError):
        quote([{"sku": "A", "unit_price": 100}], discount_pct=150)


def test_bug_101_discount_exactly_100_is_allowed():
    """Boundary guard for BUG-101: the fix must not over-reject 100%."""
    result = quote([{"sku": "A", "unit_price": 100}], discount_pct=100)
    assert Decimal(result["total"]) == Decimal("0.00")


def test_bug_102_subtotal_has_no_float_residue():
    """BUG-102: subtotal returned 0.30000000000000004 for 0.10 + 0.20.

    Found by: test_subtotal_has_no_float_residue_for_simple_prices.
    """
    result = quote([
        {"sku": "A", "unit_price": 0.10},
        {"sku": "B", "unit_price": 0.20},
    ])
    assert result["subtotal"] == "0.30"


def test_bug_102_money_fields_are_strings_with_two_decimals():
    """BUG-102 guard: money fields must always carry exactly two decimal places."""
    result = quote([{"sku": "A", "unit_price": 5}], discount_pct=10)
    for field in ("subtotal", "discount", "total"):
        assert len(result[field].split(".")[1]) == 2, field
