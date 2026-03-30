"""
place_orders.py - Run this at 9:15 AM at market open
Reads signals.json generated yesterday and places orders
"""

import json
import logging
import os

# ---- Your credentials ----
API_KEY      = "KMW3pBs4"
CLIENT_ID    = "AABZ520811"
PASSWORD     = "2826"
TOTP_SECRET  = "ZQFDIWN2563S4WJPG4JNQIUY4U"

# ---- Settings ----
INITIAL_CAPITAL  = 100000
PAPER_TRADE      = True      # ← SET TO False WHEN READY TO GO LIVE
SIGNALS_FILE     = "signals.json"

from broker.angel_broker import AngelBroker
from src.data_loader import get_latest_prices
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
    logger.info("PHASE 2: Placing orders at market open")
    logger.info(f"Mode: {'PAPER TRADE' if PAPER_TRADE else '🔴 LIVE TRADING'}")

    if not os.path.exists(SIGNALS_FILE):
        logger.warning("No signals.json found. Did generate_signals.py run yesterday?")
        return

    with open(SIGNALS_FILE, "r") as f:
        signals = json.load(f)

    logger.info(f"Signals generated at: {signals['generated_at']}")

    entries = signals["entries"]
    exits   = signals["exits"]

    entry_count = sum(1 for v in entries.values() if v)
    exit_count  = sum(1 for v in exits.values() if v)
    logger.info(f"Signals -> Entries: {entry_count} | Exits: {exit_count}")

    if entry_count == 0 and exit_count == 0:
        logger.info("No signals to act on today.")
        logger.info("=" * 50)
        return

    broker = AngelBroker(API_KEY, CLIENT_ID, PASSWORD, TOTP_SECRET)

    if not broker.login():
        logger.error("Login failed. Cannot place orders.")
        return

    engine = ExecutionEngine(
        broker=broker,
        capital=INITIAL_CAPITAL,
        risk_per_trade=0.02,
        stop_loss_pct=0.05,
        max_positions=7,
        paper_trade=PAPER_TRADE
    )

    latest_prices = get_latest_prices(broker)

    engine.execute_exits(exits, latest_prices)
    engine.execute_entries(entries, latest_prices)
    engine.get_status()

    os.remove(SIGNALS_FILE)
    logger.info("Orders placed. signals.json cleaned up.")
    logger.info("=" * 50)


if __name__ == "__main__":
    main()