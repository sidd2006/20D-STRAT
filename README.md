# 20D-STRAT — Momentum Breakout Trading Bot

Automated momentum breakout strategy connected to AngelOne SmartAPI for live/paper trading on NSE stocks.

---

## What it does

- Scans 20 NSE stocks daily for breakout signals using a 15-day rolling high
- Filters by EMA200 trend, 20-day momentum ranking, and a momentum threshold
- Places buy orders at market open with automatic stop-loss and position sizing
- Handles exits when price breaks below 30-day rolling low or hits stop-loss
- Skips bad data automatically (outlier removal, missing value handling)
- Flask dashboard to monitor live positions *(Azure deployed)*

---

## How it works

The bot runs in two phases every trading day:

**3:35 PM — Signal Generation**
```
python generate_signals.py
```
Fetches the last 300 days of OHLC data from AngelOne, runs the breakout strategy, and saves entry/exit signals to `signals.json`.

**9:15 AM next morning — Order Placement**
```
python place_orders.py
```
Reads `signals.json` and places orders at market open. Cleans up the file after execution.

Both scripts are automated via Windows Task Scheduler.

---

## Strategy Logic

| Component | Detail |
|---|---|
| Entry | Price breaks above 15-day rolling high |
| Trend filter | Price above EMA200 |
| Momentum filter | Top 20 stocks by 20-day momentum, threshold > 5% |
| Exit | Price drops below 30-day rolling low |
| Stop-loss | 5% below entry price |
| Position sizing | 2% risk per trade on initial capital |
| Max positions | 7 at a time |

---

## Project Structure

```
├── generate_signals.py      # Phase 1: run at 3:35 PM
├── place_orders.py          # Phase 2: run at 9:15 AM
├── src/
│   ├── strategy.py          # Breakout signal logic
│   ├── data_loader.py       # AngelOne data fetching + watchlist
│   ├── data_cleaning_main.py# Outlier removal, missing value handling
│   ├── backtest.py          # Backtesting engine
│   └── visualization.py     # Equity curve, drawdown, return plots
├── broker/
│   └── angel_broker.py      # AngelOne SmartAPI wrapper
├── signals.json             # Generated at 3:35 PM, consumed at 9:15 AM
└── bot.log                  # Auto-generated logs
```

---

## Setup

### 1. Install dependencies

```bash
pip install -r requirements.txt
```

Key libraries: `smartapi-python`, `nsepython`, `pandas`, `ta`, `flask`

### 2. Configure environment variables

Create a `.env` file in the root directory:

```
API_KEY=your_angelone_api_key
CLIENT_ID=your_client_id
PASSWORD=your_password
TOTP_SECRET=your_totp_secret
```

> Get your API key from [AngelOne SmartAPI](https://smartapi.angelbroking.com/). TOTP secret is from when you set up 2FA.

### 3. Paper trade mode (default)

In `place_orders.py`, `PAPER_TRADE = True` by default — the bot will log orders but **not place real ones**. Set to `False` only when you're ready to go live.

### 4. Customize the watchlist

Edit `WATCHLIST` in `src/data_loader.py`. Format is "SYMBOL": "TOKEN" where token is the AngelOne instrument token.

> Full token list: [OpenAPIScripMaster.json](https://margincalculator.angelbroking.com/OpenAPI_File/files/OpenAPIScripMaster.json)

---

## Backtesting

```python
from src.data_loader import fetch_price_data
from src.strategy import breakout_strat
from src.backtest import backtest
from src.visualization import plot_results

price_data, ohlc = fetch_price_data(broker, days_back=300)
entry_signal, exit_signal = breakout_strat(price_data, ohlc)
results = backtest(price_data, entry_signal, exit_signal)
plot_results(results)
```

Outputs: total return, win rate, max drawdown, equity curve, drawdown curve, return distribution.

---

## Notes

- Currently in paper trade mode, observing live signals before going live
- `something.py` is a standalone yfinance-based data loader for backtesting with Nifty 50 data (not used in live bot)
- Logs are written to `bot.log` on every run

---

## VM Access

To connect to the Azure VM used for deployment (example):

```bash
ssh -i C:\Users\siddh\Downloads\TradingBot_key.pem azureuser@20.189.76.226
cd 20D-STRAT
source venv/bin/activate
```

Adjust the key path and username as needed.

