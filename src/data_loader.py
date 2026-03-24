
import pandas as pd
import yfinance as yf
import requests

def load_data():

    # GET NIFTY 50 TICKERS
    url = "https://en.wikipedia.org/wiki/NIFTY_50"

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
    }

    response = requests.get(url, headers=headers)

    tables = pd.read_html(response.text)

    nifty_table = tables[1]

    tickers = nifty_table["Symbol"].tolist()
    tickers = [ticker + ".NS" for ticker in tickers]

    # DOWNLOAD DATA
    data = yf.download(tickers, start="2023-01-01", end="2025-12-21",auto_adjust=True)#auto-ajust works for splits

    data["Close"].round(2).to_csv("data/close_prices.csv")
    data["High"].round(2).to_csv("data/high_prices.csv")
    data["Low"].round(2).to_csv("data/low_prices.csv")
    data["Open"].round(2).to_csv("data/open_prices.csv")

    close_prices = data["Close"].round(2)
    return {
        "close":close_prices,
        "ohlc":data
    }