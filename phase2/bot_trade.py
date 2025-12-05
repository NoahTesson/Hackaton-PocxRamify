import math
from collections import deque

class BotState:
    def __init__(self):
        self.last_epoch = -1
        self.ema_fast = None
        self.ema_slow = None
        self.prev_price_rsi = None
        self.avg_gain = 0.0
        self.avg_loss = 0.0
        self.rsi_initialized = False
        self.rsi_warmup_count = 0
        self.returns_buffer = deque(maxlen=20)
        self.prices_buffer = deque(maxlen=15)

state = BotState()

def update_ema(current_ema, price, span):
    if current_ema is None:
        return price
    alpha = 2 / (span + 1)
    return alpha * price + (1 - alpha) * current_ema

def update_rsi(price):
    if state.prev_price_rsi is None:
        state.prev_price_rsi = price
        return 50.0
    change = price - state.prev_price_rsi
    state.prev_price_rsi = price
    gain = change if change > 0 else 0.0
    loss = -change if change < 0 else 0.0
    period = 14
    if not state.rsi_initialized:
        state.rsi_warmup_count += 1
        state.avg_gain += gain
        state.avg_loss += loss
        if state.rsi_warmup_count >= period:
            state.avg_gain /= period
            state.avg_loss /= period
            state.rsi_initialized = True
        return 50.0
    else:
        state.avg_gain = (state.avg_gain * (period - 1) + gain) / period
        state.avg_loss = (state.avg_loss * (period - 1) + loss) / period
    if state.avg_loss == 0:
        return 100.0
    rs = state.avg_gain / state.avg_loss
    return 100.0 - (100.0 / (1.0 + rs))

def get_volatility():
    if len(state.returns_buffer) < 2:
        return 0.0
    data = list(state.returns_buffer)
    mean_ret = sum(data) / len(data)
    variance = sum((r - mean_ret) ** 2 for r in data) / len(data)
    return math.sqrt(variance)

def make_decision(epoch: int, price: float):
    global state
    if epoch == 0 or epoch < state.last_epoch:
        state = BotState()
    state.last_epoch = epoch
    if state.prices_buffer:
        prev_p = state.prices_buffer[-1]
        if prev_p > 0:
            ret = (price - prev_p) / prev_p
            state.returns_buffer.append(ret)
    state.prices_buffer.append(price)
    state.ema_fast = update_ema(state.ema_fast, price, 10)
    state.ema_slow = update_ema(state.ema_slow, price, 40)
    rsi_val = update_rsi(price)
    vol_val = get_volatility()
    if epoch < 50:
        return {'Asset B': 0.0, 'Cash': 1.0}
    allocation = 0.0
    is_bull = price > state.ema_slow
    if is_bull:
        if price > state.ema_fast:
            allocation = 1.0
        else:
            if rsi_val < 45:
                allocation = 1.0
            else:
                allocation = 0.5
        if rsi_val > 85:
            allocation = 0.5
        if rsi_val > 92:
            allocation = 0.0
    else:
        allocation = 0.0
    recent_max = max(state.prices_buffer)
    if recent_max > 0:
        dd = (price - recent_max) / recent_max
        if dd < -0.03:
            allocation = 0.0
    target_vol = 0.025
    if vol_val > 0:
        scalar = target_vol / vol_val
        if scalar < 1.0:
            scalar = max(0.5, scalar)
            allocation = allocation * scalar
    allocation = max(0.0, min(1.0, allocation))
    if allocation < 0.05:
        allocation = 0.0
    return {
        'Asset B': allocation,
        'Cash': 1.0 - allocation
    }