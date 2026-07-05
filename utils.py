from nsepython import nse_holidays
from datetime import datetime

def is_market_open():
    # Weekend check
    if datetime.today().weekday() >= 5:
        return False

    # Holiday check
    data = nse_holidays(type="trading")
    cm_holidays = data["CM"]

    holiday_dates = [h["tradingDate"] for h in cm_holidays]
    today = datetime.today().strftime("%d-%b-%Y")

    return today not in holiday_dates
