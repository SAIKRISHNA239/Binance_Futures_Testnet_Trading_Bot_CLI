"""
Binance Futures Testnet Trading Bot - Core package.

Provides client, order placement, validation, and logging for USDT-M futures
trading on Binance Testnet.
"""

from .client import BinanceFuturesClient
from .orders import place_order
from .validators import validate_order_params

__all__ = [
    "BinanceFuturesClient",
    "place_order",
    "validate_order_params",
]
