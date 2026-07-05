import pyotp
from SmartApi import SmartConnect
import logging
from dotenv import load_dotenv
import os


load_dotenv()


api_key = os.getenv("API_KEY")
client_id = os.getenv("CLIENT_ID")
password = os.getenv("PASSWORD")
totp_secret = os.getenv("TOTP_SECRET")
logger = logging.getLogger(__name__)


class AngelBroker:
    def __init__(self, api_key, client_id, password, totp_secret):
        self.api_key = api_key
        self.client_id = client_id
        self.password = password
        self.totp_secret = totp_secret
        self.obj = None
        self.auth_token = None
        self.feed_token = None

    def login(self):
        try:
            self.obj = SmartConnect(api_key=self.api_key)
            totp = pyotp.TOTP(self.totp_secret).now()
            data = self.obj.generateSession(self.client_id, self.password, totp)

            if data["status"]:
                self.auth_token = data["data"]["jwtToken"]
                self.feed_token = self.obj.getfeedToken()
                logger.info("Login successful")
                return True
            else:
                logger.error(f"Login failed: {data['message']}")
                return False

        except Exception as e:
            logger.error(f"Login exception: {e}")
            return False

    def place_order(self, symbol, token, buy_sell, qty, order_type="MARKET", price=0):
        """
        buy_sell: "BUY" or "SELL"
        order_type: "MARKET" or "LIMIT"
        """
        try:
            order_params = {
                "variety": "NORMAL",
                "tradingsymbol": symbol,
                "symboltoken": token,
                "transactiontype": buy_sell,
                "exchange": "NSE",
                "ordertype": order_type,
                "producttype": "DELIVERY",
                "duration": "DAY",
                "price": str(price),
                "squareoff": "0",
                "stoploss": "0",
                "quantity": str(qty)
            }
            response = self.obj.placeOrder(order_params)
            logger.info(f"Order placed: {buy_sell} {qty} {symbol} -> {response}")
            return response

        except Exception as e:
            logger.error(f"Order placement error: {e}")
            return None

    def get_holdings(self):
        try:
            return self.obj.holding()
        except Exception as e:
            logger.error(f"Holdings fetch error: {e}")
            return None

    def get_positions(self):
        try:
            return self.obj.position()
        except Exception as e:
            logger.error(f"Positions fetch error: {e}")
            return None

    def get_ltp(self, exchange, symbol, token):
        """Get last traded price for a symbol"""
        try:
            data = self.obj.ltpData(exchange, symbol, token)
            return data["data"]["ltp"]
        except Exception as e:
            logger.error(f"LTP fetch error for {symbol}: {e}")
            return None

    def get_candle_data(self, token, interval, from_date, to_date, exchange="NSE"):
        """
        interval: ONE_MINUTE, FIVE_MINUTE, FIFTEEN_MINUTE, ONE_HOUR, ONE_DAY
        from_date/to_date: "YYYY-MM-DD HH:MM"
        """
        try:
            params = {
                "exchange": exchange,
                "symboltoken": token,
                "interval": interval,
                "fromdate": from_date,
                "todate": to_date
            }
            data = self.obj.getCandleData(params)
            return data
        except Exception as e:
            logger.error(f"Candle data error: {e}")
            return None
    @staticmethod
    def get_symbol_token(symbol):
        mapping = {
            "LT": "11483",
            "ADANIENT": "25",
            "ADANIPORTS": "15083",
            "TATASTEEL": "3499"
        }
        return mapping.get(symbol)
