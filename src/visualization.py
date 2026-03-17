import matplotlib.pyplot as plt
import seaborn as sns

sns.set_style("whitegrid")

def plot_results(results):

    equity = results["equity_curve"]
    drawdown = results["drawdown"]
    returns = results["returns"]

    # EQUITY CURVE
    plt.figure(figsize=(12,6))
    sns.lineplot(x=equity.index, y=equity.values)

    plt.title("Equity Curve")
    plt.xlabel("Time")
    plt.ylabel("Portfolio Value")
    plt.show()


    # DRAWDOWN CURVE
    plt.figure(figsize=(12,6))
    sns.lineplot(x=drawdown.index, y=drawdown.values)

    plt.title("Drawdown Curve")
    plt.xlabel("Time")
    plt.ylabel("Drawdown (%)")
    plt.show()


    # RETURN DISTRIBUTION
    plt.figure(figsize=(12,6))
    sns.histplot(returns, bins=50, kde=True)

    plt.title("Distribution of Strategy Returns")
    plt.xlabel("Daily Returns")
    plt.ylabel("Frequency")
    plt.show()