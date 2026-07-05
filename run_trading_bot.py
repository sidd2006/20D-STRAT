"""
run_trading_bot.py - Run this at ~3:20 PM, before market close (3:30 PM)
Fetches near-final prices, generates signals, and places orders same day.
"""
import logging
import os
import pandas as pd
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()
api_key = os.getenv("API_KEY")
client_id = os.getenv("CLIENT_ID")
password = os.getenv("PASSWORD")
totp = os.getenv("TOTP_SECRET")

INITIAL_CAPITAL = 100000
PAPER_TRADE = True  # SET TO False WHEN READY TO GO LIVE

from broker.angel_broker import AngelBroker
from src.data_loader import fetch_price_data, get_latest_prices, WATCHLIST
from src.strategy import breakout_strat
from src.executor.executor import ExecutionEngine

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
    logger.info("Running near-close: fetching data, generating signals, placing orders")

    broker = AngelBroker(api_key, client_id, password, totp)
    if not broker.login():
        logger.error("Login failed.")
        return

    # Step 1: historical daily candles (up through yesterday's close)
    price_data, ohlc = fetch_price_data(broker, days_back=300, interval="ONE_DAY")
    if price_data is None or price_data.empty:
        logger.error("No price data.")
        return

    # Step 2: today's near-close LTP, treat as today's close
    logger.info("Fetching live LTP as proxy for today's close...")
    latest_prices = get_latest_prices(broker)

    today_ts = pd.Timestamp(datetime.now().date(), tz='Asia/Kolkata')
    today_row = pd.Series(latest_prices, name=today_ts)

    # Append today's row (only for symbols we have LTP for)
    price_data = pd.concat([price_data, today_row.to_frame().T])
    price_data = price_data[~price_data.index.duplicated(keep='last')]
    price_data = price_data.sort_index()

    # Step 3: run strategy including today's near-close price
    entry_signal, exit_signal = breakout_strat(
        price_data=price_data,
        ohlc=ohlc,
        entry_lookback=15,
        exit_lookback=30,
        momentum_threshold=0.05,
    )

    today = price_data.index[-1]

    momentum = price_data.pct_change(20)
    today_momentum = momentum.loc[today].to_dict()

    today_entries = {k: bool(v) for k, v in entry_signal.loc[today].to_dict().items()}
    today_exits   = {k: bool(v) for k, v in exit_signal.loc[today].to_dict().items()}

    entry_stocks = [s for s, v in today_entries.items() if v]
    exit_stocks  = [s for s, v in today_exits.items() if v]

    logger.info(f"Entry signals: {entry_stocks if entry_stocks else 'None'}")
    logger.info(f"Exit signals:  {exit_stocks if exit_stocks else 'None'}")

    if not entry_stocks and not exit_stocks:
        logger.info("No signals to act on today.")
        logger.info("=" * 50)
        return

    # Step 4: place orders immediately, same day
    engine = ExecutionEngine(
        broker=broker,
        capital=INITIAL_CAPITAL,
        risk_per_trade=0.02,
        stop_loss_pct=0.05,
        max_positions=7,
        paper_trade=PAPER_TRADE
    )
    engine.load_state_from_log()

    engine.execute_exits(today_exits, latest_prices)
    engine.execute_entries(today_entries, latest_prices, today_momentum)
    engine.get_status()

    logger.info("Orders placed for today, near close.")
    logger.info("=" * 50)


if __name__ == "__main__":
    main()
