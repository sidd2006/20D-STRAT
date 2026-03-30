import pandas as pd
from datetime import datetime, timedelta
import logging
import time 

logger = logging.getLogger(__name__)

# -------------------------------------------------------
# WATCHLIST: Add your stocks here
# Format: { "SYMBOL": "TOKEN" }
# Token is the AngelOne instrument token for each stock
# Get full token list from:
# https://margincalculator.angelbroking.com/OpenAPI_File/files/OpenAPIScripMaster.json
# -------------------------------------------------------
WATCHLIST = {
    "RELIANCE": "2885",
    "TCS": "11536",
    "INFY": "1594",
    "HDFCBANK": "1333",
    "ICICIBANK": "4963",
    "SBIN": "3045",
    "WIPRO": "3787",
    "AXISBANK": "5900",
    "BAJFINANCE": "317",
    "TITAN": "3506",
    "MARUTI": "10999",
    "LTIM": "17818",
    "SUNPHARMA": "3351",
    "ASIANPAINT": "236",
    "HCLTECH": "7229",
    "NESTLEIND": "17963",
    "ULTRACEMCO": "11532",
    "TATAMOTORS": "3456",
    "TATASTEEL": "3499",
    "KOTAKBANK": "1922",
}


def fetch_price_data(broker, days_back=60, interval="ONE_DAY"):
    """
    Fetch close price data for all stocks in WATCHLIST.
    Returns a DataFrame with dates as index, symbols as columns.
    """
    to_date = datetime.now()
    from_date = to_date - timedelta(days=days_back)

    from_str = from_date.strftime("%Y-%m-%d 09:15")
    to_str = to_date.strftime("%Y-%m-%d 15:30")

    all_close = {}

    for symbol, token in WATCHLIST.items():
        try:
            raw = broker.get_candle_data(
                token=token,
                interval=interval,
                from_date=from_str,
                to_date=to_str
            )

            if not raw or "data" not in raw:
                logger.warning(f"No data for {symbol}")
                continue

            # AngelOne candle format: [timestamp, open, high, low, close, volume]
            df = pd.DataFrame(raw["data"], columns=["datetime", "open", "high", "low", "close", "volume"])
            df["datetime"] = pd.to_datetime(df["datetime"])
            df.set_index("datetime", inplace=True)

            all_close[symbol] = df["close"]
            logger.info(f"Fetched {len(df)} candles for {symbol}")

        except Exception as e:
            logger.error(f"Error fetching {symbol}: {e}")

        time.sleep(0.5)

    if not all_close:
        logger.error("No data fetched for any stock!")
        return None, None

    price_data = pd.DataFrame(all_close)
    price_data = price_data.sort_index()

    # Also build OHLC dict for indicators if needed
    ohlc = {}  # Can extend later if strategy needs OHLC

    return price_data, ohlc


def get_latest_prices(broker):
    """Get current LTP for all watchlist stocks."""
    prices = {}
    for symbol, token in WATCHLIST.items():
        ltp = broker.get_ltp("NSE", symbol, token)
        if ltp:
            prices[symbol] = ltp
    return prices