import pandas as pd

def backtest(price_data,entry_signal,exit_signal,stop_loss_level,target_level,trailing_level,initial_capital=1000000,transaction_cost = 0.0015):
  capital = initial_capital
  positions = {}
  equity_curve = []
  trades = []
  wins = losses = 0
  
  for date in price_data.index:
    for stock in price_data.columns:
      price = price_data.loc[date,stock]

      #ENTRY
      position_size = initial_capital/len(price_data.columns)
      shares = position_size/price
      if entry_signal.loc[date,stock] and stock not in positions:
        positions[stock] = {
          "entry_price": price,
          "shares": shares
        }

      
      #EXIT
      if stock in positions:
        if(price <= stop_loss_level.loc[date,stock] 
           or price >= target_level.loc[date,stock] 
           or exit_signal.loc[date,stock]):
          
          entry_price = positions[stock]["entry_price"]
          shares = positions[stock]["shares"]


          pnl = (price - entry_price) * shares
          pnl = pnl*(1- transaction_cost)
           
          capital += pnl
          equity_curve.append(capital)
          trades.append(pnl)
          if (pnl > 0):
            wins += 1
          else:
            losses += 1
          
          del positions[stock]
          

          win_rate = wins/len(trades)

          #drawdown
          equity_series = pd.Series(equity_curve)
          running_max = equity_series.cummax()
          drawdown = equity_series - running_max
          max_drawdown = drawdown.min()
      
  total_return = (capital/initial_capital - 1) * 100
  return {
    "total_return": float(total_return),
    "final_capital": float(capital),
    "total_trades": int(len(trades)),
    "win_rate": float(win_rate),
    "max_drawdown": float(max_drawdown),
  }