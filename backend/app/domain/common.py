from decimal import ROUND_HALF_EVEN, Decimal

QUANTITY_QUANTUM = Decimal("0.0001")
PRICE_QUANTUM = Decimal("0.01")


def quantize_quantity(value: Decimal) -> Decimal:
    return value.quantize(QUANTITY_QUANTUM, rounding=ROUND_HALF_EVEN)


def quantize_price(value: Decimal) -> Decimal:
    return value.quantize(PRICE_QUANTUM, rounding=ROUND_HALF_EVEN)
