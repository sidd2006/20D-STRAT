import pandas as pd

def backtest(price_data, entry_signal, exit_signal,
             stop_loss_level=0.05,
             risk_per_trade=0.02,
             max_allocation=0.75,
             initial_capital=100000,
             transaction_cost=0.0015):

    capital = initial_capital
    positions = {}
    equity_curve = []
    equity_dates = []
    trades = []
    wins = losses = 0

    max_positions = 10

    # Momentum for rankings
    momentum = price_data.pct_change(20)

    for date in price_data.index:

        # =========================
        # 1. EXIT FIRST
        # =========================
        for stock in list(positions.keys()):

            price = price_data.loc[date, stock]
            if pd.isna(price):
                continue

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

        # =========================
        # 2. ENTRY AFTER EXIT
        # =========================
        daily_momentum = momentum.loc[date].dropna()
        sorted_stocks = daily_momentum.sort_values(ascending=False).index

        for stock in sorted_stocks:

            if stock not in price_data.columns:
                continue

            if (entry_signal.loc[date, stock]
                and stock not in positions
                and len(positions) < max_positions):

                price = price_data.loc[date, stock]

                if pd.isna(price):
                    continue

                # --- Stop loss ---
                stop_loss_price = price * (1 - stop_loss_level)

                # --- Risk calculation ---
                risk_amount = initial_capital* risk_per_trade
                risk_per_share = price - stop_loss_price

                if risk_per_share <= 0:
                    continue

                shares = risk_amount // risk_per_share

                # --- Max allocation cap ---
                max_shares = (capital * max_allocation) // price
                shares = min(shares, max_shares)

                if shares <= 0:
                    continue

                cost = shares * price * (1 + transaction_cost)

                if cost > capital:
                    continue

                # --- Enter trade ---
                capital -= cost

                positions[stock] = {
                    "entry_price": price,
                    "shares": shares,
                    "stop_loss": stop_loss_price
                }

        # =========================
        # 3. END-OF-DAY EQUITY
        # =========================
        equity = capital

        for stock in positions:
            shares = positions[stock]["shares"]
            price = price_data.loc[date, stock]

            if not pd.isna(price):
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