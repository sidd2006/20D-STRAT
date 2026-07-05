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
    "RELIANCE":   "2885",
    "TCS":        "11536",
    "HDFCBANK":   "1333",
    "ICICIBANK":  "4963",
    "INFY":       "1594",
    "HINDUNILVR": "1394",
    "ITC":        "1660",
    "SBIN":       "3045",
    "BHARTIARTL": "10604",
    "KOTAKBANK":  "1922",
    "LT":         "11483",
    "AXISBANK":   "5900",
    "ASIANPAINT": "236",
    "MARUTI":     "10999",
    "SUNPHARMA":  "3351",
    "TITAN":      "3506",
    "ULTRACEMCO": "11532",
    "NESTLEIND":  "17963",
    "WIPRO":      "3787",
    "POWERGRID":  "14977",
    "NTPC":       "11630",
    "BAJFINANCE": "317",
    "BAJAJFINSV": "16675",
    "HCLTECH":    "7229",
    "TECHM":      "13538",
    "M&M":        "2031",
    "TATAMOTORS": "3456",
    "ADANIENT":   "25",
    "ADANIPORTS": "15083",
    "JSWSTEEL":   "11723",
    "TATASTEEL":  "3499",
    "COALINDIA":  "20374",
    "ONGC":       "2475",
    "INDUSINDBK": "5258",
    "GRASIM":     "1232",
    "DRREDDY":    "881",
    "EICHERMOT":  "910",
    "CIPLA":      "694",
    "BRITANNIA":  "547",
    "HEROMOTOCO": "1348",
    "DIVISLAB":   "10940",
    "APOLLOHOSP": "157",
    "BAJAJ-AUTO": "16669",
    "SBILIFE":    "21808",
    "HDFCLIFE":   "467",
    "UPL":        "11287",
    "SHREECEM":   "3103",
    "BPCL":       "526",
    "TATACONSUM": "3432",
    "ICICIPRULI": "18652",
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
        raw = None
        for attempt in range(3):
            try:
                raw = broker.get_candle_data(
                    token=token,
                    interval=interval,
                    from_date=from_str,
                    to_date=to_str
                )

                if raw and "data" in raw:
                    break

                # Handle potential rate limits/errors returned in message
                error_msg = ""
                if isinstance(raw, dict):
                    error_msg = raw.get("message", "")

                if "rate" in error_msg.lower() or "limit" in error_msg.lower() or "exceed" in error_msg.lower():
                    logger.warning(f"Rate limit hit for {symbol} on attempt {attempt+1}, retrying in 2s...")
                    time.sleep(2)
                else:
                    logger.warning(f"Attempt {attempt+1} failed for {symbol}: {raw}")
                    time.sleep(1)
            except Exception as e:
                logger.error(f"Error fetching {symbol} on attempt {attempt+1}: {e}")
                time.sleep(1)

        if not raw or "data" not in raw:
            logger.warning(f"No data for {symbol} after 3 attempts")
            continue

        try:
            # AngelOne candle format: [timestamp, open, high, low, close, volume]
            df = pd.DataFrame(raw["data"], columns=["datetime", "open", "high", "low", "close", "volume"])
            df["datetime"] = pd.to_datetime(df["datetime"])
            df.set_index("datetime", inplace=True)

            all_close[symbol] = df["close"]
            logger.info(f"Fetched {len(df)} candles for {symbol}")

        except Exception as e:
            logger.error(f"Error parsing data for {symbol}: {e}")

        time.sleep(1.0)

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