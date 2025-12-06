import math
from collections import deque

class AssetTracker:
    def __init__(self):
        self.ema_short = None
        self.ema_long = None
        self.prev_price = None
        self.avg_gain = 0.0
        self.avg_loss = 0.0
        self.rsi_initialized = False
        self.rsi_step = 0
        self.last_rsi = 50.0
        self.last_vol = 0.0
        self.returns = deque(maxlen=20)
        self.prices = deque(maxlen=15)

    def update(self, price):
        if self.prices:
            prev = self.prices[-1]
            if prev > 0:
                ret = (price - prev) / prev
                self.returns.append(ret)
        self.prices.append(price)
        self.ema_short = self._update_ema(self.ema_short, price, 12)
        self.ema_long = self._update_ema(self.ema_long, price, 50)
        self.last_rsi = self._update_rsi(price)
        self.last_vol = self._get_volatility()

    def _update_ema(self, current, price, span):
        if current is None:
            return price
        k = 2 / (span + 1)
        return k * price + (1 - k) * current

    def _update_rsi(self, price):
        if self.prev_price is None:
            self.prev_price = price
            return 50.0
        delta = price - self.prev_price
        self.prev_price = price
        gain = delta if delta > 0 else 0.0
        loss = -delta if delta < 0 else 0.0
        period = 14
        if not self.rsi_initialized:
            self.rsi_step += 1
            self.avg_gain += gain
            self.avg_loss += loss
            if self.rsi_step >= period:
                self.avg_gain /= period
                self.avg_loss /= period
                self.rsi_initialized = True
            return 50.0
        else:
            self.avg_gain = (self.avg_gain * (period - 1) + gain) / period
            self.avg_loss = (self.avg_loss * (period - 1) + loss) / period
        if self.avg_loss == 0:
            return 100.0
        rs = self.avg_gain / self.avg_loss
        return 100.0 - (100.0 / (1.0 + rs))

    def _get_volatility(self):
        if len(self.returns) < 2:
            return 0.0
        data = list(self.returns)
        mean = sum(data) / len(data)
        var = sum((x - mean) ** 2 for x in data) / len(data)
        return math.sqrt(var)

class BotState:
    def __init__(self):
        self.last_epoch = -1
        self.tracker_a = AssetTracker()
        self.tracker_b = AssetTracker()

state = BotState()

def get_asset_score(tracker, price):
    score = 0.0
    if tracker.ema_long is None:
        return 0.0
    is_bullish = price > tracker.ema_long
    if is_bullish:
        if price > tracker.ema_short:
            score = 1.0
        else:
            if tracker.last_rsi < 45:
                score = 1.0
            else:
                score = 0.6
        if tracker.last_rsi > 88:
            score = 0.7
        if tracker.last_rsi > 95:
            score = 0.0
    else:
        score = 0.0
    
    recent_max = 0.0
    if tracker.prices:
        recent_max = max(tracker.prices)
    if recent_max > 0:
        dd = (price - recent_max) / recent_max
        if dd < -0.035:
            score = 0.0
            
    return score

def make_decision(epoch: int, priceA: float, priceB: float):
    global state
    if epoch == 0 or epoch < state.last_epoch:
        state = BotState()
    state.last_epoch = epoch

    state.tracker_a.update(priceA)
    state.tracker_b.update(priceB)

    if epoch < 50:
        return {'Asset A': 0.0, 'Asset B': 0.0, 'Cash': 1.0}

    score_a = get_asset_score(state.tracker_a, priceA)
    score_b = get_asset_score(state.tracker_b, priceB)

    vol_a = max(0.002, state.tracker_a.last_vol)
    vol_b = max(0.002, state.tracker_b.last_vol)

    raw_weight_a = score_a / vol_a
    raw_weight_b = score_b / vol_b
    
    total_raw = raw_weight_a + raw_weight_b
    
    weight_a = 0.0
    weight_b = 0.0
    
    if total_raw > 0:
        exposure_factor = max(score_a, score_b)
        
        weight_a = (raw_weight_a / total_raw) * exposure_factor
        weight_b = (raw_weight_b / total_raw) * exposure_factor

    weight_a = max(0.0, min(1.0, weight_a))
    weight_b = max(0.0, min(1.0, weight_b))
    
    if (weight_a + weight_b) > 1.0:
        factor = 1.0 / (weight_a + weight_b)
        weight_a *= factor
        weight_b *= factor

    weight_cash = 1.0 - (weight_a + weight_b)
    weight_cash = max(0.0, weight_cash)

    return {
        'Asset A': weight_a,
        'Asset B': weight_b,
        'Cash': weight_cash
    }