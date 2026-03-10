import sys
from pathlib import Path
from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from typing import Optional

# Ensure project root is on path
project_root = Path(__file__).resolve().parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from trading_bot.bot.client import BinanceFuturesClient, BinanceFuturesClientError
from trading_bot.bot.orders import place_order
from trading_bot.bot.validators import ValidationError, validate_order_params
from trading_bot.bot.logging_config import setup_logging, get_logger

setup_logging(console=True)
logger = get_logger("web")

app = FastAPI(title="Binance Futures Testnet Bot API")

class PlaceOrderRequest(BaseModel):
    symbol: str
    side: str
    order_type: str
    quantity: float
    price: Optional[float] = None

@app.post("/api/order")
def api_place_order(req: PlaceOrderRequest):
    symbol = req.symbol.strip().upper()
    side = req.side.strip().upper()
    order_type = req.order_type.strip().upper()
    try:
        validate_order_params(symbol, side, order_type, req.quantity, req.price)
    except ValidationError as e:
        raise HTTPException(status_code=400, detail=str(e))
    
    try:
        client = BinanceFuturesClient()
        response = place_order(
            client=client,
            symbol=symbol,
            side=side,
            order_type=order_type,
            quantity=req.quantity,
            price=req.price
        )
        return response
    except BinanceFuturesClientError as e:
        err_msg = str(e)
        if "-4024" in err_msg or "limit price" in err_msg.lower():
            err_msg += " Hint: Binance restricts limit price vs current market."
        raise HTTPException(status_code=400, detail=err_msg)
    except Exception as e:
        logger.exception("Unexpected error")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/order/{symbol}/{order_id}")
def api_get_order(symbol: str, order_id: int):
    symbol = symbol.strip().upper()
    try:
        client = BinanceFuturesClient()
        response = client.get_order(symbol, order_id)
        return response
    except BinanceFuturesClientError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.exception("Unexpected error")
        raise HTTPException(status_code=500, detail=str(e))

# Mount static files correctly
static_dir = project_root / "web" / "static"
app.mount("/", StaticFiles(directory=str(static_dir), html=True), name="static")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("web.server:app", host="0.0.0.0", port=8000, reload=True)
