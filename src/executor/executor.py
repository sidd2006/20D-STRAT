import logging
from src.data_loader import WATCHLIST

logger = logging.getLogger(__name__)


class ExecutionEngine:
    def __init__(self, broker, capital, risk_per_trade=0.02, stop_loss_pct=0.05, max_positions=7, paper_trade=True):
        self.broker = broker
        self.capital = capital
        self.risk_per_trade = risk_per_trade
        self.stop_loss_pct = stop_loss_pct
        self.max_positions = max_positions
        self.paper_trade = paper_trade  # Set True to simulate without real orders
        self.open_positions = {}  # { symbol: { entry_price, shares, stop_loss } }

    def calculate_qty(self, price):
        """Calculate number of shares based on risk management."""
        risk_amount = self.capital * self.risk_per_trade
        stop_loss_price = price * (1 - self.stop_loss_pct)
        risk_per_share = price - stop_loss_price

        if risk_per_share <= 0:
            return 0

        qty = int(risk_amount // risk_per_share)

        # Cap at 75% of available capital
        max_qty = int((self.capital * 0.75) // price)
        qty = min(qty, max_qty)

        return qty

    def execute_entries(self, entry_signals, latest_prices):
        """
        entry_signals: dict { symbol: True/False }
        latest_prices: dict { symbol: price }
        """
        if len(self.open_positions) >= self.max_positions:
            logger.info("Max positions reached, skipping entries.")
            return

        for symbol, signal in entry_signals.items():
            if not signal:
                continue
            if symbol in self.open_positions:
                continue
            if len(self.open_positions) >= self.max_positions:
                break

            price = latest_prices.get(symbol)
            if not price:
                continue

            qty = self.calculate_qty(price)
            if qty <= 0:
                continue

            cost = qty * price
            if cost > self.capital:
                logger.warning(f"Not enough capital for {symbol}. Need {cost:.0f}, have {self.capital:.0f}")
                continue

            stop_loss = price * (1 - self.stop_loss_pct)

            if self.paper_trade:
                logger.info(f"[PAPER] BUY {qty} x {symbol} @ {price:.2f} | SL: {stop_loss:.2f}")
            else:
                token = WATCHLIST.get(symbol)
                response = self.broker.place_order(symbol, token, "BUY", qty)
                if not response:
                    logger.error(f"Order failed for {symbol}")
                    continue
                logger.info(f"[LIVE] BUY {qty} x {symbol} @ {price:.2f} | SL: {stop_loss:.2f}")

            self.capital -= cost
            self.open_positions[symbol] = {
                "entry_price": price,
                "shares": qty,
                "stop_loss": stop_loss
            }

    def execute_exits(self, exit_signals, latest_prices):
        """
        exit_signals: dict { symbol: True/False }
        latest_prices: dict { symbol: price }
        Also checks stop loss hits.
        """
        to_exit = []

        for symbol, pos in self.open_positions.items():
            price = latest_prices.get(symbol)
            if not price:
                continue

            stop_hit = price <= pos["stop_loss"]
            signal_exit = exit_signals.get(symbol, False)

            if stop_hit or signal_exit:
                reason = "STOP LOSS" if stop_hit else "EXIT SIGNAL"
                to_exit.append((symbol, price, reason))

        for symbol, price, reason in to_exit:
            pos = self.open_positions[symbol]
            qty = pos["shares"]
            pnl = (price - pos["entry_price"]) * qty

            if self.paper_trade:
                logger.info(f"[PAPER] SELL {qty} x {symbol} @ {price:.2f} | PnL: {pnl:.2f} | Reason: {reason}")
            else:
                token = WATCHLIST.get(symbol)
                response = self.broker.place_order(symbol, token, "SELL", qty)
                if not response:
                    logger.error(f"Exit order failed for {symbol}")
                    continue
                logger.info(f"[LIVE] SELL {qty} x {symbol} @ {price:.2f} | PnL: {pnl:.2f} | Reason: {reason}")

            self.capital += price * qty
            del self.open_positions[symbol]

    def get_status(self):
        logger.info(f"Capital: {self.capital:.2f} | Open Positions: {len(self.open_positions)}")
        for sym, pos in self.open_positions.items():
            logger.info(f"  {sym}: entry={pos['entry_price']:.2f}, shares={pos['shares']}, sl={pos['stop_loss']:.2f}")