import pandas as pd

def backtest(price_data, entry_signal, exit_signal, stop_loss_level=0.15,
             initial_capital=100000, transaction_cost=0.0015):

    capital = initial_capital
    positions = {}
    equity_curve = []
    equity_dates = []
    trades = []
    wins = losses = 0

    max_positions = 10

    for date in price_data.index:

        # =========================
        # 1. EXIT FIRST
        # =========================
        for stock in list(positions.keys()):   # IMPORTANT: use list()

            price = price_data.loc[date, stock]
            stop = positions[stock]["stop_loss"]

            if price <= stop or exit_signal.loc[date, stock]:

                entry_price = positions[stock]["entry_price"]
                shares = positions[stock]["shares"]

                entry_value = entry_price * shares
                exit_value = price * shares

                cost = (entry_value + exit_value) * transaction_cost
                pnl = exit_value - entry_value - cost

                capital += exit_value - cost
                trades.append(pnl)

                if pnl > 0:
                    wins += 1
                else:
                    losses += 1

                del positions[stock]


        start_capital = capital 
        position_size = start_capital / (max_positions - len(positions))

        # =========================
        # 2. ENTRY AFTER EXIT
        # =========================
        for stock in price_data.columns:

            if (entry_signal.loc[date, stock]
                and stock not in positions
                and len(positions) < max_positions):

                price = price_data.loc[date, stock]

                if capital >= position_size:   # safety check

                    shares = position_size / price
                    capital -= position_size

                    positions[stock] = {
                        "entry_price": price,
                        "shares": shares,
                        "stop_loss": price * (1 - stop_loss_level)
                    }

        # =========================
        # 3. END-OF-DAY EQUITY
        # =========================
        equity = capital

        for stock in positions:
            shares = positions[stock]["shares"]
            price = price_data.loc[date, stock]
            equity += shares * price

        equity_curve.append(equity)
        equity_dates.append(date)

    # =========================
    # PERFORMANCE METRICS
    # =========================
    equity_series = pd.Series(equity_curve, index=equity_dates)

    returns = equity_series.pct_change().dropna()

    win_rate = wins / len(trades) if len(trades) > 0 else 0

    running_max = equity_series.cummax()
    drawdown = (equity_series - running_max) / running_max * 100
    max_drawdown = drawdown.min()

    total_return = (equity_series.iloc[-1] / initial_capital - 1) * 100

    return {
        "total_return": float(total_return),
        "final_capital": float(equity_series.iloc[-1]),
        "total_trades": int(len(trades)),
        "win_rate": float(win_rate),
        "max_drawdown": float(max_drawdown),

        "equity_curve": equity_series,
        "drawdown": drawdown,
        "returns": returns
    }