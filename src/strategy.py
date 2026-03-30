import ta
import pandas as pd
from ta.trend import ADXIndicator

def breakout_strat(price_data, ohlc, entry_lookback=15, exit_lookback=30, momentum_threshold=0.05):


    # ---------- TREND ----------
    ema200 = price_data.ewm(span=200).mean()
    trend_filter = price_data > ema200

    # ---------- MOMENTUM ----------
    momentum = price_data.pct_change(20)
    ranked = momentum.rank(axis=1, ascending=False)
    top_10_mask = ranked <= 20

    # ---------- ENTRY ----------
    rolling_max = price_data.rolling(entry_lookback).max()

    entry_signal = (
        (price_data > rolling_max.shift(1)) &
        top_10_mask &
        (momentum > momentum_threshold) &
        trend_filter 
    )

    # ---------- EXIT ----------
    rolling_min = price_data.rolling(exit_lookback).min()
    exit_signal = price_data < rolling_min.shift(1)

    return entry_signal, exit_signal