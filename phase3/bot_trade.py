import math
from collections import deque

class BotState:
    def __init__(self):
        self.history_a = deque(maxlen=30)
        self.history_b = deque(maxlen=30)
        self.b_highs = deque(maxlen=15)
        self.b_ema_fast = None
        self.b_ema_slow = None

state = BotState()

def get_stats(history):
    if len(history) < 20:
        return 0.0, 0.0

    data = list(history)[-20:]
    mean = sum(data) / len(data)
    
    if len(data) > 1:
        variance = sum((x - mean) ** 2 for x in data) / (len(data) - 1)
        std = math.sqrt(variance)
    else:
        std = 0.0
    
    return mean, std

def update_ema(current, price, span):
    if current is None:
        return price
    k = 2 / (span + 1)
    return k * price + (1 - k) * current

def make_decision(epoch: int, priceA: float, priceB: float):
    global state

    state.history_a.append(priceA)
    state.history_b.append(priceB)
    state.b_highs.append(priceB)
    state.b_ema_fast = update_ema(state.b_ema_fast, priceB, 10)
    state.b_ema_slow = update_ema(state.b_ema_slow, priceB, 30)

    if len(state.history_a) < 25:
        return {'Asset A': 0.0, 'Asset B': 0.0, 'Cash': 1.0}

    mean_a, std_a = get_stats(state.history_a)
    
    alloc_a = 0.0
    if std_a > 0:
        z_score_a = (priceA - mean_a) / std_a
        if z_score_a < -1.5:
            alloc_a = 1.0
        elif z_score_a < -0.5:
            alloc_a = 0.5
        else:
            alloc_a = 0.0

    alloc_b = 0.0
    if state.b_ema_slow is not None and priceB > state.b_ema_slow:
        if priceB > state.b_ema_fast:
            alloc_b = 1.0
        else:
            alloc_b = 0.8

    recent_high_b = max(state.b_highs)
    if recent_high_b > 0:
        drawdown_b = (priceB - recent_high_b) / recent_high_b
        if drawdown_b < -0.035:
            alloc_b = 0.0

    _, std_b = get_stats(state.history_b)
    vol_b_pct = std_b / priceB if priceB > 0 else 0.0
    
    target_vol = 0.03
    if vol_b_pct > 0:
        scalar = target_vol / vol_b_pct
        scalar = min(1.0, scalar)
        scalar = max(0.5, scalar) 
        alloc_b *= scalar
    total_req = alloc_a + alloc_b
    
    final_a = 0.0
    final_b = 0.0
    
    if total_req > 1.0:
        final_a = alloc_a / total_req
        final_b = alloc_b / total_req
    else:
        final_a = alloc_a
        final_b = alloc_b
        
    final_cash = 1.0 - (final_a + final_b)
    
    return {
        'Asset A': final_a,
        'Asset B': final_b,
        'Cash': max(0.0, final_cash)
    }