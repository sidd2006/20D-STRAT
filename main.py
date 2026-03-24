from src.data_loader import load_data
from src.data_cleaning import run_all
from src.strategy import breakout_strat
from src.backtest import backtest
from src.visualization import plot_results

# Step 1: Load data
data_bundle = load_data()  #STONGEST 10 STOCKS, SHARPE RATIO, 1% risk

price_data = data_bundle["close"]
ohlc = data_bundle["ohlc"]

price_data = run_all(price_data)
# Step 2: Generate strategy signals
entry_signal, exit_signal = breakout_strat(price_data,ohlc)

# Step 3: Run backtest
results = backtest(
    price_data,
    entry_signal,
    exit_signal
)

# Step 4: Print results
print("BACKTEST RESULTS")
print("Total Return:", results["total_return"])
print("Final Capital:", results["final_capital"])
print("Total Trades:", results["total_trades"])
print("Win Rate:", results["win_rate"])
print("Max Drawdown:", results["max_drawdown"])

plot_results(results)