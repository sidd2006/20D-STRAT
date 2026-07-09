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

Around 3:20 PM — Signal Generation + Order Placement
python run_trading_bot.py

The bot fetches the latest available OHLC data from AngelOne, runs the breakout strategy, and generates entry/exit signals.

Before placing any order, it checks:

Current market status
Available capital
Existing positions
Maximum position limit
Duplicate orders
Stop-loss and position-sizing rules

Approved entry and exit orders are then placed before market close through AngelOne SmartAPI.

Signals, orders, positions, and logs are saved for dashboard monitoring and later analysis.

The bot is automated through a scheduler and runs once per trading day near market close.
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
├── run_trading_bot.py     # Generates signals and places orders around 3:20 PM
├── src/
│   ├── strategy.py        # Breakout signal logic
│   ├── data_loader.py     # AngelOne data fetching + watchlist
│   ├── data_cleaning_main.py # Outlier removal, missing value handling
│   ├── backtest.py        # Backtesting engine
│   └── visualization.py   # Equity curve, drawdown, return plots
├── broker/
│   └── angel_broker.py    # AngelOne SmartAPI wrapper
├── logs/                  # Auto-generated logs
└── signals.json           # Latest generated signals and execution record
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



