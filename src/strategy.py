import pandas as pd

def breakout_strat(price_data,entry_lookback = 20,exit_lookback = 15,stop_loss = 0.08,target = 0.5, trailing_SL = 0.06):

  rolling_max = price_data.rolling(window=entry_lookback).max() #20 day rolling window finds MAX, out of the last 20  days values MAX[1,2,...20]
  entry_signal = price_data > rolling_max.shift(1) # SHIFT HELPS to compare todays with previous 20D max
  
  rolling_min = price_data.rolling(window=exit_lookback).min()
  exit_signal = price_data < rolling_min.shift(1)

  stop_loss_level = price_data * (1 - stop_loss)

  target_level = price_data * (1 + target)

  trailing_SL_level = price_data * (1 - trailing_SL)

  return entry_signal,exit_signal,stop_loss_level,target_level,trailing_SL_level





