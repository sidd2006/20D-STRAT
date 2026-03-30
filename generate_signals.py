"""
generate_signals.py - Run this at 3:35 PM after market close
Reads today's closed candles, generates breakout signals, saves to signals.json
"""

import json
import logging
from datetime import datetime

# ---- Your credentials ----
API_KEY      = ""
CLIENT_ID    = ""
PASSWORD     = ""
TOTP_SECRET  = ""

SIGNALS_FILE = "signals.json"

from broker.angel_broker import AngelBroker
from src.data_loader import fetch_price_data
from src.strategy import breakout_strat

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler("bot.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


def main():
    logger.info("=" * 50)
    logger.info("PHASE 1: Generating signals after market close")

    broker = AngelBroker(API_KEY, CLIENT_ID, PASSWORD, TOTP_SECRET)

    if not broker.login():
        logger.error("Login failed.")
        return

    price_data, ohlc = fetch_price_data(broker, days_back=300, interval="ONE_DAY")

    if price_data is None or price_data.empty:
        logger.error("No price data.")
        return

    entry_signal, exit_signal = breakout_strat(
        price_data=price_data,
        ohlc=ohlc,
        entry_lookback=15,
        exit_lookback=30,
        momentum_threshold=0.05
    )

    today = price_data.index[-1]
    today_entries = {k: bool(v) for k, v in entry_signal.loc[today].to_dict().items()}
    today_exits   = {k: bool(v) for k, v in exit_signal.loc[today].to_dict().items()}

    entry_stocks = [s for s, v in today_entries.items() if v]
    exit_stocks  = [s for s, v in today_exits.items() if v]

    logger.info(f"Entry signals: {entry_stocks if entry_stocks else 'None'}")
    logger.info(f"Exit signals:  {exit_stocks if exit_stocks else 'None'}")

    signals = {
        "date": str(today.date()),
        "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "entries": today_entries,
        "exits": today_exits
    }

    with open(SIGNALS_FILE, "w") as f:
        json.dump(signals, f, indent=2)

    logger.info(f"Signals saved to {SIGNALS_FILE}. Orders will be placed tomorrow at 9:15 AM.")
    logger.info("=" * 50)


if __name__ == "__main__":
    main()