import pandas as pd
import yfinance as yf


def load_data():

    # GET NIFTY 50 TICKERS
    url = "https://en.wikipedia.org/wiki/NIFTY_50"
    headers = {
        "User-Agent": "Mozilla/5.0"
    }

    tables = pd.read_html(url, flavor="html5lib", storage_options=headers)
    nifty_table = tables[1]

    tickers = nifty_table["Symbol"].tolist()
    tickers = [ticker + ".NS" for ticker in tickers]

    # DOWNLOAD DATA
    data = yf.download(tickers, start="2022-01-01", end="2024-12-31")

    close_prices = data["Close"]
    close_prices = close_prices.round(2)

    close_prices.to_csv("data/price_data.csv")

    return close_prices