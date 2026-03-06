"""
Order placement for Binance Futures USDT-M (testnet).

Handles MARKET and LIMIT order types via the Binance Futures API.
"""

import time

from .client import BinanceFuturesClient, BinanceFuturesClientError
from .logging_config import get_logger
from .validators import MIN_NOTIONAL_USDT

logger = get_logger("orders")

# Seconds to wait before polling order status when MARKET returns NEW
_MARKET_POLL_DELAY = 2.0


def place_order(
    client: BinanceFuturesClient,
    symbol: str,
    side: str,
    order_type: str,
    quantity: float,
    price: float | None = None,
) -> dict:
    """
    Place a single order (MARKET or LIMIT) on Binance Futures Testnet.

    Args:
        client: Configured BinanceFuturesClient instance.
        symbol: Trading pair (e.g. BTCUSDT).
        side: BUY or SELL.
        order_type: MARKET or LIMIT.
        quantity: Order quantity (must be > 0).
        price: Limit price; required when order_type is LIMIT, ignored for MARKET.

    Returns:
        Order response dict from Binance containing at least:
        - orderId
        - status
        - executedQty
        - avgPrice (if available, e.g. for filled MARKET orders)

    Raises:
        BinanceFuturesClientError: On API or network errors.
        ValueError: If price is missing for LIMIT orders.
    """
    symbol = symbol.strip().upper()
    side = side.upper()
    order_type = order_type.upper()

    # For MARKET orders, check min notional using current price
    if order_type == "MARKET":
        try:
            current_price = client.get_ticker_price(symbol)
        except Exception as e:
            raise BinanceFuturesClientError(
                f"Cannot validate MARKET order size (failed to get price): {e}"
            ) from e
        notional = quantity * current_price
        if notional < MIN_NOTIONAL_USDT:
            raise BinanceFuturesClientError(
                f"Order notional must be at least {MIN_NOTIONAL_USDT} USDT. "
                f"At current price {current_price}, quantity {quantity} gives {notional:.2f} USDT. "
                f"Use quantity >= {MIN_NOTIONAL_USDT / current_price:.6f} (e.g. 0.002 for BTC)."
            )

    logger.info(
        "Placing order: symbol=%s side=%s type=%s quantity=%s price=%s",
        symbol,
        side,
        order_type,
        quantity,
        price,
    )

    response = client.post_order(
        symbol=symbol,
        side=side,
        order_type=order_type,
        quantity=quantity,
        price=price,
    )

    # For MARKET orders, if still NEW with no fill, poll once for updated status (testnet can be delayed)
    if order_type == "MARKET":
        status = response.get("status", "")
        executed = float(response.get("executedQty") or 0)
        if status == "NEW" and executed == 0:
            time.sleep(_MARKET_POLL_DELAY)
            try:
                response = client.get_order(symbol, response["orderId"])
                logger.info("Order status after poll: %s", response)
            except Exception as e:
                logger.warning("Could not poll order status: %s", e)

    logger.info("Order response: %s", response)
    return response
