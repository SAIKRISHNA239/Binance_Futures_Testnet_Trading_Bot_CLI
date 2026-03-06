"""
Binance Futures (USDT-M) API client for testnet.

Uses environment variables or a .env file for API key and secret. All requests
are signed with HMAC SHA256.
"""

import hashlib
import hmac
import os
import time
from pathlib import Path
from urllib.parse import urlencode

import requests

from .logging_config import get_logger

# Environment variable names for credentials (used by _load_dotenv and __init__)
ENV_API_KEY = "BINANCE_FUTURES_API_KEY"
ENV_API_SECRET = "BINANCE_FUTURES_API_SECRET"


def _load_dotenv() -> None:
    """Load BINANCE_FUTURES_* from .env in project root or cwd (no extra deps)."""
    for base in (Path(__file__).resolve().parent.parent.parent, Path.cwd()):
        env_file = base / ".env"
        if env_file.exists():
            try:
                with open(env_file, encoding="utf-8") as f:
                    for line in f:
                        line = line.strip()
                        if line and not line.startswith("#") and "=" in line:
                            k, _, v = line.partition("=")
                            k, v = k.strip(), v.strip().strip("'\"")
                            if k in (ENV_API_KEY, ENV_API_SECRET) and k not in os.environ:
                                os.environ[k] = v
            except OSError:
                pass
            break


_load_dotenv()

logger = get_logger("client")

# Binance Futures Testnet base URL (USDT-M)
DEFAULT_BASE_URL = "https://testnet.binancefuture.com"


class BinanceFuturesClientError(Exception):
    """Raised when the Binance Futures API returns an error or request fails."""

    pass


class BinanceFuturesClient:
    """
    Lightweight client for Binance Futures Testnet (USDT-M) REST API.

    Reads BINANCE_FUTURES_API_KEY and BINANCE_FUTURES_API_SECRET from
    environment. All private endpoints are signed with HMAC SHA256.
    """

    def __init__(
        self,
        api_key: str | None = None,
        api_secret: str | None = None,
        base_url: str = DEFAULT_BASE_URL,
    ):
        """
        Initialize the client.

        Args:
            api_key: API key (default: from BINANCE_FUTURES_API_KEY).
            api_secret: API secret (default: from BINANCE_FUTURES_API_SECRET).
            base_url: Base URL for the API (default: testnet).
        """
        self.api_key = api_key or os.environ.get(ENV_API_KEY)
        self.api_secret = api_secret or os.environ.get(ENV_API_SECRET)
        self.base_url = base_url.rstrip("/")

        if not self.api_key or not self.api_secret:
            raise BinanceFuturesClientError(
                f"Missing credentials. Set {ENV_API_KEY} and {ENV_API_SECRET} "
                "in environment or in a .env file in the project root."
            )

        self._session = requests.Session()
        self._session.headers.update(
            {
                "X-MBX-APIKEY": self.api_key,
                "Content-Type": "application/x-www-form-urlencoded",
            }
        )

    def _sign(self, params: dict) -> str:
        """Create HMAC SHA256 signature for the given query string."""
        query = urlencode(params)
        signature = hmac.new(
            self.api_secret.encode("utf-8"),
            query.encode("utf-8"),
            hashlib.sha256,
        ).hexdigest()
        return signature

    def _request(
        self,
        method: str,
        path: str,
        params: dict | None = None,
        signed: bool = True,
    ) -> dict:
        """
        Send an HTTP request to the API.

        Args:
            method: HTTP method (GET, POST, etc.).
            path: API path (e.g. /fapi/v1/order).
            params: Query or form parameters.
            signed: If True, add timestamp and signature (for private endpoints).

        Returns:
            JSON response as dict.

        Raises:
            BinanceFuturesClientError: On HTTP or API error.
        """
        params = dict(params) if params else {}
        url = f"{self.base_url}{path}"

        if signed:
            params["timestamp"] = int(time.time() * 1000)
            params["signature"] = self._sign(params)

        logger.info("API request: %s %s params=%s", method, path, params)

        try:
            if method.upper() == "GET":
                resp = self._session.request(method, url, params=params, timeout=30)
            else:
                resp = self._session.request(
                    method, url, data=params, timeout=30
                )
        except requests.RequestException as e:
            logger.exception("Network error: %s", e)
            raise BinanceFuturesClientError(f"Network error: {e}") from e

        logger.info("API response: status=%s body=%s", resp.status_code, resp.text)

        try:
            data = resp.json()
        except ValueError:
            raise BinanceFuturesClientError(
                f"Invalid JSON response: {resp.text[:500]}"
            )

        if not resp.ok:
            code = data.get("code", resp.status_code)
            msg = data.get("msg", resp.text)
            logger.error("API error: code=%s msg=%s", code, msg)
            raise BinanceFuturesClientError(f"API error [{code}]: {msg}")

        return data

    def get_order(self, symbol: str, order_id: int) -> dict:
        """Fetch order status by orderId (for polling fill status)."""
        path = "/fapi/v1/order"
        params = {"symbol": symbol.strip().upper(), "orderId": order_id}
        return self._request("GET", path, params=params)

    def get_ticker_price(self, symbol: str) -> float:
        """
        Get current mark/price for a symbol (public endpoint).
        Used to validate MARKET order notional before placing.
        """
        path = "/fapi/v1/ticker/price"
        params = {"symbol": symbol.strip().upper()}
        data = self._request("GET", path, params=params, signed=False)
        return float(data["price"])

    def post_order(
        self,
        symbol: str,
        side: str,
        order_type: str,
        quantity: float,
        price: float | None = None,
    ) -> dict:
        """
        Place a new order (MARKET or LIMIT) on USDT-M futures.

        Args:
            symbol: Trading pair (e.g. BTCUSDT).
            side: BUY or SELL.
            order_type: MARKET or LIMIT.
            quantity: Order quantity.
            price: Limit price (required for LIMIT, ignored for MARKET).

        Returns:
            Order response from Binance (orderId, status, executedQty, etc.).
        """
        symbol = symbol.upper().strip()
        side = side.upper()
        order_type = order_type.upper()

        params = {
            "symbol": symbol,
            "side": side,
            "type": order_type,
            "quantity": quantity,
            # RESULT returns final order state (e.g. FILLED for MARKET) with executedQty/avgPrice
            "newOrderRespType": "RESULT",
        }

        if order_type == "LIMIT":
            if price is None:
                raise ValueError("Price is required for LIMIT orders.")
            params["timeInForce"] = "GTC"
            params["price"] = price

        return self._request("POST", "/fapi/v1/order", params=params)
