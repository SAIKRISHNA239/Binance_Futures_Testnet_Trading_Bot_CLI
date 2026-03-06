"""
CLI entry point for the Binance Futures Testnet Trading Bot.

Parses arguments, validates input, places the order, and prints formatted results.
"""

import argparse
import sys
from pathlib import Path

# Ensure project root is on path when running as script
_project_root = Path(__file__).resolve().parent.parent
if str(_project_root) not in sys.path:
    sys.path.insert(0, str(_project_root))

from trading_bot.bot.client import BinanceFuturesClient, BinanceFuturesClientError
from trading_bot.bot.logging_config import setup_logging, get_logger
from trading_bot.bot.orders import place_order
from trading_bot.bot.validators import ValidationError, validate_order_params


def _parse_args() -> argparse.Namespace:
    """Parse and return CLI arguments."""
    parser = argparse.ArgumentParser(
        description="Place or verify orders on Binance Futures Testnet (USDT-M)."
    )
    parser.add_argument("--symbol", required=True, help="Trading pair (e.g. BTCUSDT)")
    parser.add_argument("--order_id", type=int, default=None, help="If set, check this order's status instead of placing (verify an order)")
    # Place-order args (required when not using --order_id)
    parser.add_argument("--side", help="Order side: BUY or SELL (required for place)")
    parser.add_argument("--order_type", help="Order type: MARKET or LIMIT (required for place)")
    parser.add_argument("--quantity", type=float, default=None, help="Order quantity (required for place)")
    parser.add_argument("--price", type=float, default=None, help="Limit price (required for LIMIT orders)")
    return parser.parse_args()


def _print_order_summary(
    symbol: str,
    side: str,
    order_type: str,
    quantity: float,
    price: float | None,
) -> None:
    """Print a summary of the order request."""
    print("\n" + "=" * 50)
    print("ORDER REQUEST SUMMARY")
    print("=" * 50)
    print(f"  Symbol:     {symbol}")
    print(f"  Side:       {side}")
    print(f"  Type:       {order_type}")
    print(f"  Quantity:   {quantity}")
    if price is not None:
        print(f"  Price:      {price}")
    print("=" * 50)


def _print_order_response(response: dict) -> None:
    """Print order response details (orderId, status, executedQty, avgPrice)."""
    print("\nORDER RESPONSE")
    print("-" * 50)
    print(f"  orderId:     {response.get('orderId', 'N/A')}")
    print(f"  status:      {response.get('status', 'N/A')}")
    print(f"  executedQty: {response.get('executedQty', '0')}")
    avg_price = response.get("avgPrice")
    if avg_price is not None and str(avg_price).strip() and float(avg_price) != 0:
        print(f"  avgPrice:    {avg_price}")
    else:
        print("  avgPrice:    N/A (not filled or not applicable)")
    print("-" * 50)


def main() -> int:
    """Run the CLI: place order or check order status. Returns 0 on success, 1 on failure."""
    args = _parse_args()

    setup_logging(console=False)
    logger = get_logger("cli")

    symbol = args.symbol.strip().upper()

    # --- Verify order: --order_id set → fetch status from exchange ---
    if args.order_id is not None:
        try:
            client = BinanceFuturesClient()
            response = client.get_order(symbol, args.order_id)
            print("\n" + "=" * 50)
            print("ORDER STATUS (from Binance)")
            print("=" * 50)
            _print_order_response(response)
            print("=" * 50)
            print("\nOrder found. Details above match what the exchange has for this order ID.")
            return 0
        except BinanceFuturesClientError as e:
            print(f"\nFailure: {e}", file=sys.stderr)
            logger.exception("Order status check failed")
            return 1
        except Exception as e:
            print(f"\nUnexpected error: {e}", file=sys.stderr)
            logger.exception("Unexpected error")
            return 1

    # --- Place order ---
    side = args.side
    order_type = args.order_type
    quantity = args.quantity
    price = args.price
    if not side or order_type is None or quantity is None:
        print("For placing an order, --side, --order_type and --quantity are required.", file=sys.stderr)
        return 1
    side = side.upper()
    order_type = order_type.upper()

    try:
        validate_order_params(symbol, side, order_type, quantity, price)
    except ValidationError as e:
        print(f"\nValidation error: {e}", file=sys.stderr)
        logger.warning("Validation failed: %s", e)
        return 1

    _print_order_summary(symbol, side, order_type, quantity, price)

    try:
        client = BinanceFuturesClient()
        response = place_order(
            client,
            symbol=symbol,
            side=side,
            order_type=order_type,
            quantity=quantity,
            price=price,
        )
        _print_order_response(response)
        print("\nSuccess: Order placed successfully.")
        print("\nTo verify this order on the exchange, run:")
        print(f"  python -m trading_bot.cli --symbol {symbol} --order_id {response.get('orderId')}")
        return 0
    except BinanceFuturesClientError as e:
        err_msg = str(e)
        print(f"\nFailure: {e}", file=sys.stderr)
        if "-4024" in err_msg or "limit price" in err_msg.lower():
            print(
                "\nHint: Binance restricts limit price vs current market. "
                "For a SELL use a price at or above the minimum shown; for a BUY use a price at or below the maximum. "
                "Check the current price on the testnet or retry with a price inside the allowed range.",
                file=sys.stderr,
            )
        logger.exception("Order placement failed")
        return 1
    except Exception as e:
        print(f"\nUnexpected error: {e}", file=sys.stderr)
        logger.exception("Unexpected error")
        return 1


if __name__ == "__main__":
    sys.exit(main())
