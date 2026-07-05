import logging
import json
import os
from datetime import datetime
from src.data_loader import WATCHLIST

logger = logging.getLogger(__name__)


class ExecutionEngine:
    def __init__(self, broker, capital, risk_per_trade=0.02, stop_loss_pct=0.05, max_positions=7, paper_trade=True):
        self.broker = broker
        self.capital = capital
        self.risk_per_trade = risk_per_trade
        self.stop_loss_pct = stop_loss_pct
        self.max_positions = max_positions
        self.paper_trade = paper_trade
        self.open_positions = {}

    def _resolve_price(self, symbol, latest_prices):
        price = latest_prices.get(symbol)
        if price is not None and price > 0:
            return price
        token = WATCHLIST.get(symbol)
        if not token:
            return None
        for candidate in (symbol, f"{symbol}-EQ"):
            try:
                fetched = self.broker.get_ltp("NSE", candidate, token)
                if fetched is not None and fetched > 0:
                    latest_prices[symbol] = fetched
                    return fetched
            except Exception:
                continue
        return None

    def load_state_from_log(self, orders_file="orders.log"):
        if not os.path.exists(orders_file):
            logger.info("No orders.log found — starting with empty positions.")
            return

        lots = {}
        current_cap = self.capital

        with open(orders_file, "r") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    o = json.loads(line)
                except Exception:
                    continue

                symbol = o.get("symbol")
                qty = int(o.get("qty", 0))
                price = float(o.get("price", 0))
                side = o.get("side", "")
                sl = float(o.get("stop_loss", price * (1 - self.stop_loss_pct)))
                time = o.get("time", "")

                if side == "BUY":
                    current_cap -= qty * price
                    lots.setdefault(symbol, []).append(
                        {"qty": qty, "entry_price": price, "stop_loss": sl, "time": time}
                    )
                elif side == "SELL":
                    current_cap += qty * price
                    remaining = qty
                    if symbol not in lots:
                        continue
                    while remaining > 0 and lots[symbol]:
                        lot = lots[symbol][0]
                        fill = min(remaining, lot["qty"])
                        lot["qty"] -= fill
                        remaining -= fill
                        if lot["qty"] == 0:
                            lots[symbol].pop(0)
                    if not lots.get(symbol):
                        lots.pop(symbol, None)

        self.open_positions = {}
        for symbol, lot_list in lots.items():
            if not lot_list:
                continue
            total_qty = sum(l["qty"] for l in lot_list)
            avg_price = sum(l["qty"] * l["entry_price"] for l in lot_list) / total_qty
            avg_sl = sum(l["qty"] * l["stop_loss"] for l in lot_list) / total_qty
            self.open_positions[symbol] = {
                "entry_price": round(avg_price, 2),
                "shares": total_qty,
                "stop_loss": round(avg_sl, 2),
            }
            logger.info(f"Restored position: {symbol} x{total_qty} @ {avg_price:.2f} | SL: {avg_sl:.2f}")

        self.capital = round(current_cap, 2)
        logger.info(f"State loaded — Capital: {self.capital:.2f}, {len(self.open_positions)} position(s) restored.")

    def _log_order(self, symbol, qty, price, side, stop_loss=None, reason=None):
        order_data = {
            "symbol": symbol,
            "qty": qty,
            "price": price,
            "side": side,
            "time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        }
        if stop_loss is not None:
            order_data["stop_loss"] = round(stop_loss, 2)
        if reason is not None:
            order_data["reason"] = reason
        with open("orders.log", "a") as f:
            f.write(json.dumps(order_data) + "\n")

    def calculate_qty(self, price):
        risk_amount = self.capital * self.risk_per_trade
        stop_loss_price = price * (1 - self.stop_loss_pct)
        risk_per_share = price - stop_loss_price
        if risk_per_share <= 0:
            return 0
        qty = int(risk_amount // risk_per_share)
        max_qty = int((self.capital * 0.75) // price)
        qty = min(qty, max_qty)
        return qty

    def execute_entries(self, entry_signals, latest_prices, momentum=None):
        if len(self.open_positions) >= self.max_positions:
            logger.info("Max positions reached, skipping entries.")
            return

        momentum = momentum or {}
        candidates = [s for s, sig in entry_signals.items() if sig]
        candidates.sort(key=lambda s: momentum.get(s, float('-inf')), reverse=True)

        for symbol in candidates:
            if symbol in self.open_positions:
                continue
            if len(self.open_positions) >= self.max_positions:
                break

            price = self._resolve_price(symbol, latest_prices)
            if price is None or price <= 0:
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

            self._log_order(symbol, qty, price, "BUY", stop_loss=stop_loss)
            self.capital -= cost
            self.open_positions[symbol] = {
                "entry_price": price,
                "shares": qty,
                "stop_loss": stop_loss
            }

    def execute_exits(self, exit_signals, latest_prices):
        to_exit = []

        for symbol, pos in self.open_positions.items():
            signal_exit = exit_signals.get(symbol, False)
            price = self._resolve_price(symbol, latest_prices)

            if price is None or price <= 0:
                if signal_exit:
                    fallback_price = pos["entry_price"]
                    to_exit.append((symbol, fallback_price, "EXIT SIGNAL"))
                else:
                    logger.warning(f"Skipping exit check for {symbol}: no valid LTP available")
                continue

            stop_hit = price <= pos["stop_loss"]
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

            self._log_order(symbol, qty, price, "SELL", stop_loss=pos["stop_loss"], reason=reason)
            self.capital += price * qty
            del self.open_positions[symbol]

    def get_status(self):
        logger.info(f"Capital: {self.capital:.2f} | Open Positions: {len(self.open_positions)}")
        for sym, pos in self.open_positions.items():
            logger.info(f"  {sym}: entry={pos['entry_price']:.2f}, shares={pos['shares']}, sl={pos['stop_loss']:.2f}")
