from flask import Flask, jsonify, send_from_directory
import json
import os
import re
from datetime import datetime
from SmartApi import SmartConnect
import pyotp
from dotenv import load_dotenv

load_dotenv()

ORDERS_FILE = "orders.log"
BOT_LOG     = "bot.log"
app = Flask(__name__, static_folder="dashboard")

API_KEY     = os.getenv("API_KEY")
CLIENT_ID   = os.getenv("CLIENT_ID")
PASSWORD    = os.getenv("PASSWORD")
TOTP_SECRET = os.getenv("TOTP_SECRET")

# Full Nifty 50 token map (same as data_loader WATCHLIST)
TOKEN_MAP = {
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

cached_broker = None

def get_broker():
    global cached_broker
    if cached_broker is not None:
        try:
            # Simple test to verify the session is active and valid
            res = cached_broker.position()
            if isinstance(res, dict) and res.get("status") is True:
                return cached_broker
        except Exception:
            pass
        cached_broker = None

    try:
        totp = pyotp.TOTP(TOTP_SECRET).now()
        broker = SmartConnect(api_key=API_KEY)
        data = broker.generateSession(CLIENT_ID, PASSWORD, totp)
        if data and data.get("status") is True:
            cached_broker = broker
            return cached_broker
        else:
            print("Login failed during generateSession:", data)
    except Exception as e:
        print("Broker login error:", e)
    return None


def get_ltp_bulk(broker, symbols):
    """Fetch LTP for a list of symbols in bulk."""
    prices = {}
    tokens = [TOKEN_MAP[sym] for sym in symbols if sym in TOKEN_MAP]
    if not tokens:
        return prices
    try:
        # Construct exchange tokens map
        payload = {"NSE": tokens}
        res = broker.getMarketData(mode="LTP", exchangeTokens=payload)
        if res and res.get("status") is True and "data" in res:
            fetched = res["data"].get("fetched", [])
            # Create a reverse mapping of token to symbol
            token_to_symbol = {v: k for k, v in TOKEN_MAP.items()}
            for item in fetched:
                token = item.get("symbolToken")
                sym = token_to_symbol.get(token)
                if sym:
                    prices[sym] = float(item.get("ltp", 0))
    except Exception as e:
        print(f"Bulk LTP fetch error: {e}")
    return prices


def parse_bot_log():
    """
    Parse old-format [PAPER] BUY / SELL lines from bot.log.
    Returns list of order dicts (same schema as orders.log).
    """
    orders = []
    if not os.path.exists(BOT_LOG):
        return orders

    buy_re  = re.compile(
        r'(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}).*\[(?:PAPER|LIVE)\] BUY (\d+) x ([\w\-&]+) @ ([\d.]+) \| SL: ([\d.]+)'
    )
    sell_re = re.compile(
        r'(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}).*\[(?:PAPER|LIVE)\] SELL (\d+) x ([\w\-&]+) @ ([\d.]+) \| PnL: ([-\d.]+) \| Reason: (.+)'
    )

    with open(BOT_LOG, "r", errors="replace") as f:
        for line in f:
            m = buy_re.search(line)
            if m:
                orders.append({
                    "time":      m.group(1),
                    "side":      "BUY",
                    "qty":       int(m.group(2)),
                    "symbol":    m.group(3),
                    "price":     float(m.group(4)),
                    "stop_loss": float(m.group(5)),
                    "_src":      "botlog",
                })
                continue
            m = sell_re.search(line)
            if m:
                orders.append({
                    "time":   m.group(1),
                    "side":   "SELL",
                    "qty":    int(m.group(2)),
                    "symbol": m.group(3),
                    "price":  float(m.group(4)),
                    "reason": m.group(5).strip(),
                    "_src":   "botlog",
                })

    return orders


def parse_orders_log():
    """Read orders.log (new JSON-line format)."""
    orders = []
    if not os.path.exists(ORDERS_FILE):
        return orders
    with open(ORDERS_FILE, "r") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                o = json.loads(line)
                o["_src"] = "orderslog"
                orders.append(o)
            except Exception:
                continue
    return orders


def merge_all_orders():
    """
    Return all orders from orders.log.
    """
    orders_log = parse_orders_log()
    orders_log.sort(key=lambda x: x.get("time", ""))
    return orders_log



def compute_capital_from_orders_log():
    """
    Compute remaining capital using ONLY orders.log (the new, properly
    state-tracked system). bot.log trades are excluded from capital calc
    because the old executor started fresh each day with no state —
    treating them as real capital depletions gives a -24L nonsense figure.
    Returns: remaining_capital
    """
    INITIAL_CAPITAL = 100000.0
    orders = parse_orders_log()   # Only new-format orders
    capital = INITIAL_CAPITAL
    for o in sorted(orders, key=lambda x: x.get("time", "")):
        try:
            qty = max(int(o.get("qty", 0)), 0)
            price = max(float(o.get("price", 0)), 0.0)
            side = o.get("side", "")
        except Exception:
            continue

        if qty == 0 or price == 0:
            continue

        value = qty * price

        if side == "BUY":
            # Ignore corrupted legacy buys that could not have been funded.
            if value > capital:
                continue
            capital -= value
        elif side == "SELL":
            capital += value

    return round(max(capital, 0.0), 2)


def compute_positions_and_trades(orders):
    """
    Walk through all orders in chronological order.
    Returns:
      - open_positions: dict { symbol: { entry_price, qty, time, stop_loss } }
      - closed_trades: list of completed round-trips with realized PnL
      - realized_pnl: total realized PnL
      - wins / losses count
    """
    # Track positions as a list of lots per symbol (FIFO)
    lots = {}           # { symbol: [ {qty, entry_price, time, stop_loss}, ... ] }
    closed_trades = []

    for o in orders:
        symbol = o["symbol"]
        qty    = int(o["qty"])
        price  = float(o["price"])
        side   = o["side"]
        time   = o.get("time", "")
        sl     = float(o.get("stop_loss", price * 0.95))

        if side == "BUY":
            if symbol not in lots:
                lots[symbol] = []
            lots[symbol].append({"qty": qty, "entry_price": price, "time": time, "stop_loss": sl})

        elif side == "SELL":
            remaining = qty
            if symbol not in lots:
                continue
            while remaining > 0 and lots[symbol]:
                lot = lots[symbol][0]
                fill = min(remaining, lot["qty"])
                pnl = (price - lot["entry_price"]) * fill
                closed_trades.append({
                    "symbol":      symbol,
                    "qty":         fill,
                    "entry_price": lot["entry_price"],
                    "exit_price":  price,
                    "pnl":         round(pnl, 2),
                    "entry_time":  lot["time"],
                    "exit_time":   time,
                    "reason":      o.get("reason", "EXIT SIGNAL"),
                })
                lot["qty"] -= fill
                remaining  -= fill
                if lot["qty"] == 0:
                    lots[symbol].pop(0)
            if not lots[symbol]:
                del lots[symbol]

    # Build open_positions list (aggregate by symbol)
    open_positions = {}
    for symbol, lot_list in lots.items():
        total_qty   = sum(l["qty"] for l in lot_list)
        avg_price   = sum(l["qty"] * l["entry_price"] for l in lot_list) / total_qty
        avg_sl      = sum(l["qty"] * l["stop_loss"] for l in lot_list) / total_qty
        earliest    = min(l["time"] for l in lot_list)
        open_positions[symbol] = {
            "symbol":      symbol,
            "qty":         total_qty,
            "entry_price": round(avg_price, 2),
            "stop_loss":   round(avg_sl, 2),
            "time":        earliest,
        }

    realized_pnl = sum(t["pnl"] for t in closed_trades)
    wins   = len([t for t in closed_trades if t["pnl"] > 0])
    losses = len([t for t in closed_trades if t["pnl"] <= 0])

    return open_positions, closed_trades, realized_pnl, wins, losses


@app.route("/api/data")
def get_data():
    all_orders = merge_all_orders()
    open_positions, closed_trades, realized_pnl, wins, losses = compute_positions_and_trades(all_orders)

    # Capital from new system only (orders.log) — avoids the -24L bug
    remaining_capital = compute_capital_from_orders_log()

    # Fetch live LTPs for open positions
    unrealized_pnl = 0.0
    open_list = list(open_positions.values())

    if open_list:
        broker = get_broker()
        if broker:
            ltps = get_ltp_bulk(broker, [p["symbol"] for p in open_list])
            for pos in open_list:
                sym = pos["symbol"]
                ltp = ltps.get(sym)
                if ltp:
                    unreal = (ltp - pos["entry_price"]) * pos["qty"]
                    pos["current_price"]   = round(ltp, 2)
                    pos["unrealized_pnl"]  = round(unreal, 2)
                    pos["pnl_pct"]         = round((ltp - pos["entry_price"]) / pos["entry_price"] * 100, 2)
                    unrealized_pnl        += unreal
                else:
                    pos["current_price"]  = pos["entry_price"]
                    pos["unrealized_pnl"] = 0.0
                    pos["pnl_pct"]        = 0.0
        else:
            for pos in open_list:
                pos["current_price"]  = pos["entry_price"]
                pos["unrealized_pnl"] = 0.0
                pos["pnl_pct"]        = 0.0

    win_rate = round(wins / (wins + losses) * 100, 1) if (wins + losses) > 0 else 0

    # Strip internal _src field before sending
    clean_orders = [{k: v for k, v in o.items() if k != "_src"} for o in reversed(all_orders)]

    return jsonify({
        "open_positions": open_list,
        "closed_trades":  list(reversed(closed_trades)),
        "all_trades":     clean_orders,
        "stats": {
            "realized_pnl":   round(realized_pnl, 2),
            "unrealized_pnl": round(unrealized_pnl, 2),
            "total_pnl":      round(realized_pnl + unrealized_pnl, 2),
            "total_trades":   len(closed_trades),
            "open_count":     len(open_list),
            "wins":           wins,
            "losses":         losses,
            "win_rate":       win_rate,
            "capital":        remaining_capital,
        }
    })


@app.route("/")
def index():
    return send_from_directory("dashboard", "index.html")


if __name__ == "__main__":
    os.makedirs("dashboard", exist_ok=True)
    print("Dashboard running at http://0.0.0.0:5000")
    app.run(debug=False, port=5000, host="0.0.0.0")