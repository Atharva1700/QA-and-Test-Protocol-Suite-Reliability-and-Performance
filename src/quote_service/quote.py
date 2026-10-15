"""Price quote logic for a small order service.

Money is handled as Decimal and returned as exact two-decimal strings, so no
float residue reaches a customer (BUG-102).
"""

from decimal import ROUND_HALF_UP, Decimal, InvalidOperation

CENT = Decimal("0.01")
MAX_ITEMS = 100
MAX_QTY = 1000
MAX_DISCOUNT_PCT = Decimal("100")  # BUG-101: discounts above 100 produced negative totals


class QuoteError(ValueError):
    """Raised for any request the service should reject with a 400."""


def _to_cents(value):
    return value.quantize(CENT, rounding=ROUND_HALF_UP)


def _parse_price(value):
    # Decimal(str(...)) keeps 0.1 as 0.1, not its binary approximation.
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise QuoteError("unit_price must be a non-negative number")
    try:
        d = Decimal(str(value))
    except InvalidOperation:
        raise QuoteError("unit_price must be a non-negative number")
    if not d.is_finite() or d < 0:
        raise QuoteError("unit_price must be a non-negative number")
    return d


def quote(items, discount_pct=0):
    if not isinstance(items, list) or not items:
        raise QuoteError("items must be a non-empty list")
    if len(items) > MAX_ITEMS:
        raise QuoteError(f"at most {MAX_ITEMS} items")

    discount = _parse_price(discount_pct)
    if discount > MAX_DISCOUNT_PCT:
        raise QuoteError("discount_pct must be between 0 and 100")

    lines = []
    subtotal = Decimal("0")
    for item in items:
        if not isinstance(item, dict):
            raise QuoteError("each item must be an object")
        sku = item.get("sku")
        if not isinstance(sku, str) or not sku:
            raise QuoteError("sku must be a non-empty string")
        qty = item.get("qty", 1)
        if not isinstance(qty, int) or isinstance(qty, bool) or not (1 <= qty <= MAX_QTY):
            raise QuoteError(f"qty must be an integer from 1 to {MAX_QTY}")
        line_total = _to_cents(_parse_price(item.get("unit_price")) * qty)
        lines.append({"sku": sku, "qty": qty, "line_total": str(line_total)})
        subtotal += line_total

    discount_amt = _to_cents(subtotal * discount / 100)
    total = subtotal - discount_amt
    return {
        "lines": lines,
        "subtotal": str(_to_cents(subtotal)),
        "discount": str(discount_amt),
        "total": str(_to_cents(total)),
    }
