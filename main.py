from src.data_loader import load_data
from src.strategy import breakout_strat
from src.backtest import backtest
from src.visualization import plot_results

# Step 1: Load data
price_data = load_data()

# Step 2: Generate strategy signals
entry_signal, exit_signal= breakout_strat(price_data)

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