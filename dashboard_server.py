"""
dashboard_server.py - Serves bot trade data as JSON API
Run this alongside mainbot.py: python dashboard_server.py
Then open http://localhost:5000 in your browser
"""

from flask import Flask, jsonify, send_from_directory
import re
import os
from datetime import datetime

app = Flask(__name__, static_folder="dashboard")

LOG_FILE = "bot.log"


def parse_log():
    if not os.path.exists(LOG_FILE):
        return [], [], []

    trades = []
    runs = []
    current_run = None

    with open(LOG_FILE, "r") as f:
        lines = f.readlines()

    for line in lines:
        line = line.strip()

        # Detect run start
        if "Bot triggered at" in line:
            ts = re.search(r"\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}", line)
            if ts:
                current_run = {"time": ts.group(), "entries": 0, "exits": 0, "capital": None}

        if "Signals ->" in line and current_run:
            e = re.search(r"Entries: (\d+)", line)
            x = re.search(r"Exits: (\d+)", line)
            if e: current_run["entries"] = int(e.group(1))
            if x: current_run["exits"] = int(x.group(1))

        if "Capital:" in line and current_run:
            c = re.search(r"Capital: ([\d.]+)", line)
            if c:
                current_run["capital"] = float(c.group(1))
                runs.append(current_run)
                current_run = None

        # Parse BUY trades
        buy = re.search(r"\[(?:PAPER|LIVE)\] BUY (\d+) x (\w+) @ ([\d.]+) \| SL: ([\d.]+)", line)
        if buy:
            ts = re.search(r"(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})", line)
            trades.append({
                "type": "BUY",
                "qty": int(buy.group(1)),
                "symbol": buy.group(2),
                "price": float(buy.group(3)),
                "sl": float(buy.group(4)),
                "time": ts.group(1) if ts else "",
                "pnl": None
            })

        # Parse SELL trades
        sell = re.search(r"\[(?:PAPER|LIVE)\] SELL (\d+) x (\w+) @ ([\d.]+) \| PnL: ([-\d.]+)", line)
        if sell:
            ts = re.search(r"(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})", line)
            trades.append({
                "type": "SELL",
                "qty": int(sell.group(1)),
                "symbol": sell.group(2),
                "price": float(sell.group(3)),
                "sl": None,
                "time": ts.group(1) if ts else "",
                "pnl": float(sell.group(4))
            })

    return trades, runs


@app.route("/api/data")
def get_data():
    trades, runs = parse_log()

    # Calculate stats
    sell_trades = [t for t in trades if t["type"] == "SELL"]
    total_pnl = sum(t["pnl"] for t in sell_trades)
    wins = len([t for t in sell_trades if t["pnl"] > 0])
    losses = len([t for t in sell_trades if t["pnl"] <= 0])
    win_rate = round(wins / len(sell_trades) * 100, 1) if sell_trades else 0

    # Open positions = bought but not sold
    open_pos = {}
    for t in trades:
        if t["type"] == "BUY":
            open_pos[t["symbol"]] = t
        elif t["type"] == "SELL" and t["symbol"] in open_pos:
            del open_pos[t["symbol"]]

    capital = runs[-1]["capital"] if runs else 100000

    return jsonify({
        "trades": list(reversed(trades)),
        "runs": list(reversed(runs)),
        "open_positions": list(open_pos.values()),
        "stats": {
            "total_pnl": round(total_pnl, 2),
            "total_trades": len(sell_trades),
            "wins": wins,
            "losses": losses,
            "win_rate": win_rate,
            "capital": capital
        }
    })


@app.route("/")
def index():
    return send_from_directory("dashboard", "index.html")


if __name__ == "__main__":
    os.makedirs("dashboard", exist_ok=True)
    print("Dashboard running at http://localhost:5000")
    app.run(debug=False, port=5000)