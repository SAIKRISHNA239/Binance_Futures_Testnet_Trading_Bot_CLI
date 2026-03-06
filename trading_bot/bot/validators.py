"""
Input validation for order parameters.

Validates symbol, quantity, and ensures price is provided for LIMIT orders.
"""

from trading_bot.bot.logging_config import get_logger

logger = get_logger("validators")

# Supported order types
ORDER_TYPES = ("MARKET", "LIMIT")
SIDES = ("BUY", "SELL")

# Binance Futures minimum notional (USDT) per order
MIN_NOTIONAL_USDT = 100.0


class ValidationError(Exception):
    """Raised when order parameters fail validation."""

    pass


def validate_order_params(
    symbol: str,
    side: str,
    order_type: str,
    quantity: float,
    price: float | None,
) -> None:
    """
    Validate order parameters before sending to the API.

    Args:
        symbol: Trading pair (e.g. BTCUSDT).
        side: BUY or SELL.
        order_type: MARKET or LIMIT.
        quantity: Order quantity (must be > 0).
        price: Order price (required for LIMIT orders).

    Raises:
        ValidationError: If any parameter is invalid.
    """
    if not symbol or not symbol.strip():
        raise ValidationError("Symbol is required and cannot be empty.")

    symbol = symbol.strip().upper()

    if not symbol.endswith("USDT"):
        raise ValidationError(
            "Symbol must be a USDT-M pair (e.g. BTCUSDT)."
        )

    if side.upper() not in SIDES:
        raise ValidationError(
            f"Side must be one of: {', '.join(SIDES)}. Got: {side}"
        )

    if order_type.upper() not in ORDER_TYPES:
        raise ValidationError(
            f"Order type must be one of: {', '.join(ORDER_TYPES)}. Got: {order_type}"
        )

    try:
        qty = float(quantity)
    except (TypeError, ValueError):
        raise ValidationError(
            f"Quantity must be a positive number. Got: {quantity}"
        )

    if qty <= 0:
        raise ValidationError("Quantity must be greater than 0.")

    if order_type.upper() == "LIMIT":
        if price is None:
            raise ValidationError("Price is required for LIMIT orders.")
        try:
            p = float(price)
        except (TypeError, ValueError):
            raise ValidationError(
                f"Price must be a valid number for LIMIT orders. Got: {price}"
            )
        if p <= 0:
            raise ValidationError("Price must be greater than 0 for LIMIT orders.")
        notional = qty * p
        if notional < MIN_NOTIONAL_USDT:
            raise ValidationError(
                f"Order notional (quantity × price) must be at least {MIN_NOTIONAL_USDT} USDT. "
                f"Got {notional:.2f} USDT."
            )

    logger.debug(
        "Validation passed: symbol=%s side=%s type=%s qty=%s",
        symbol,
        side,
        order_type,
        quantity,
    )
