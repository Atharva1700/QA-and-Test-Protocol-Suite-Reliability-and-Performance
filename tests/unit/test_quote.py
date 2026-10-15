"""Unit tests for quote(). Written from the spec, not from the implementation.

Spec summary:
  - items: non-empty list of objects, at most 100
  - sku: non-empty string
  - qty: integer 1..1000, defaults to 1
  - unit_price: non-negative number
  - line_total = unit_price * qty, rounded to cents
  - discount = subtotal * discount_pct / 100, rounded to cents
  - discount_pct: 0..100
"""

from decimal import Decimal

import pytest

from quote_service.quote import QuoteError, quote


def money(value):
    # str() first so a float like 0.9 compares as the decimal 0.9, not its binary expansion.
    return Decimal(str(value))


def test_single_item_defaults_to_qty_one():
    result = quote([{"sku": "A", "unit_price": 5.00}])
    assert money(result["total"]) == Decimal("5.00")
    assert result["lines"][0]["qty"] == 1


def test_quantity_multiplies_unit_price():
    result = quote([{"sku": "A", "unit_price": 2.50, "qty": 4}])
    assert money(result["lines"][0]["line_total"]) == Decimal("10.00")


def test_subtotal_sums_all_lines():
    result = quote([
        {"sku": "A", "unit_price": 10.00, "qty": 2},
        {"sku": "B", "unit_price": 3.25, "qty": 1},
    ])
    assert money(result["subtotal"]) == Decimal("23.25")


def test_discount_is_applied_to_subtotal():
    result = quote([{"sku": "A", "unit_price": 100.00}], discount_pct=10)
    assert money(result["discount"]) == Decimal("10.00")
    assert money(result["total"]) == Decimal("90.00")


def test_zero_discount_leaves_total_equal_to_subtotal():
    result = quote([{"sku": "A", "unit_price": 19.99}])
    assert result["total"] == result["subtotal"]


def test_free_item_is_allowed():
    result = quote([{"sku": "A", "unit_price": 0}])
    assert money(result["total"]) == Decimal("0")


@pytest.mark.parametrize("items", [None, [], "not-a-list", {"sku": "A"}])
def test_rejects_bad_items_container(items):
    with pytest.raises(QuoteError):
        quote(items)


def test_rejects_more_than_100_items():
    with pytest.raises(QuoteError):
        quote([{"sku": "A", "unit_price": 1}] * 101)


@pytest.mark.parametrize("line", [
    "A",                                  # not an object
    {"unit_price": 1},                    # missing sku
    {"sku": "", "unit_price": 1},         # empty sku
    {"sku": 123, "unit_price": 1},        # sku not a string
    {"sku": "A", "unit_price": 1, "qty": 0},
    {"sku": "A", "unit_price": 1, "qty": 1001},
    {"sku": "A", "unit_price": 1, "qty": 1.5},
    {"sku": "A", "unit_price": 1, "qty": True},   # bool is not an int here
    {"sku": "A"},                         # missing price
    {"sku": "A", "unit_price": -0.01},
    {"sku": "A", "unit_price": "5"},      # string price
])
def test_rejects_invalid_line(line):
    with pytest.raises(QuoteError):
        quote([line])


@pytest.mark.parametrize("pct", [-1, 101])
def test_discount_must_be_between_0_and_100(pct):
    with pytest.raises(QuoteError):
        quote([{"sku": "A", "unit_price": 10}], discount_pct=pct)


def test_totals_are_exact_to_the_cent():
    # Every money field shown to a customer must be exact cents, not float residue.
    result = quote([
        {"sku": "A", "unit_price": 0.10, "qty": 3},
        {"sku": "B", "unit_price": 0.20, "qty": 3},
    ])
    assert money(result["subtotal"]) == Decimal("0.90")
    assert money(result["total"]) == Decimal("0.90")


def test_subtotal_has_no_float_residue_for_simple_prices():
    result = quote([
        {"sku": "A", "unit_price": 0.10, "qty": 1},
        {"sku": "B", "unit_price": 0.20, "qty": 1},
    ])
    assert money(result["subtotal"]) == Decimal("0.30")
