import pandas as pd

def breakout_strat(price_data, entry_lookback=20, exit_lookback=30):

    # Entry: 20-day breakout
    rolling_max = price_data.rolling(window=entry_lookback).max()
    entry_signal = price_data > rolling_max.shift(1)

    # Exit: 30-day low  
    rolling_min = price_data.rolling(window=exit_lookback).min()
    exit_signal = price_data < rolling_min.shift(1)

    return entry_signal, exit_signal