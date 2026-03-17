import pandas as pd
import yfinance as yf


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
    data = yf.download(tickers, start="2020-01-01", end="2025-12-21")

    close_prices = data["Close"]
    close_prices = close_prices.round(2)

    close_prices.to_csv("data/price_data.csv")

    return close_prices