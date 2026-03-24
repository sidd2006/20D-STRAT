import numpy as np
import pandas as pd

def run_all(price_data):
    price_data = clean_missing_values(price_data)
    price_data = remove_outliers(price_data)
    return price_data

def clean_missing_values(price_data, max_gap_pct = 0.05):
  # remove the ones which have more than 5% Nan or like they have all rows Nan holiday or smtg
  missing_pct = price_data.isna().mean()  
  bad_stocks = missing_pct[missing_pct > max_gap_pct].index
  price_data = price_data.drop(columns=bad_stocks)

  price_data = price_data.dropna(how='all')
  price_data = price_data.ffill()
  
  return price_data

def remove_outliers(price_data, max_daily_move = 0.30):

  daily_returns = price_data.pct_change()
  outlier_mask = daily_returns.abs() > max_daily_move
  price_data = price_data.where(~outlier_mask,other=np.nan)
  price_data = price_data.ffill()

  n_outliers = outlier_mask.sum().sum()
  if n_outliers > 0:
    print(f"[Outliers] replaced {n_outliers} uspicoious prices")
  
  return price_data



