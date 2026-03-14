from src.data_loader import load_data
from src.strategy import generate_signals
from src.backtest import backtest

# Step 1: Load data
price_data = load_data("data/price_data.csv")

# Step 2: Generate strategy signals
entry_signal, exit_signal, stop_loss, target, trailing = generate_signals(price_data)

# Step 3: Run backtest
results = backtest(
    price_data,
    entry_signal,
    exit_signal,
    stop_loss,
    target,
    trailing
)

# Step 4: Print results
print("Backtest Results")
print(results)