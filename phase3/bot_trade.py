import math
from collections import deque

class BotState:
    def __init__(self):
        self.history_a = deque(maxlen=50)
        self.history_b = deque(maxlen=50)
        self.b_ema_fast = None
        self.b_ema_slow = None

state = BotState()

def get_stats(history):
    if len(history) < 20:
        return 0.0, 0.0
    
    data = list(history)[-20:]
    mean = sum(data) / len(data)
    variance = sum((x - mean) ** 2 for x in data) / len(data)
    std = math.sqrt(variance)
    
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
    state.b_ema_fast = update_ema(state.b_ema_fast, priceB, 10)
    state.b_ema_slow = update_ema(state.b_ema_slow, priceB, 40)

    if len(state.history_a) < 25:
        return {'Asset A': 0.0, 'Asset B': 0.0, 'Cash': 1.0}

    mean_a, std_a = get_stats(state.history_a)
    
    alloc_a = 0.0
    if std_a > 0:
        z_score_a = (priceA - mean_a) / std_a
        if z_score_a < -1.0:
            alloc_a = 0.8
        elif z_score_a < 0.0:
            alloc_a = 0.4
        elif z_score_a < 1.0:
            alloc_a = 0.1
        else:
            alloc_a = 0.0

    alloc_b = 0.0
    
    if state.b_ema_slow is not None:
        if priceB > state.b_ema_slow:
            if priceB > state.b_ema_fast:
                alloc_b = 1.0
            else:
                alloc_b = 0.8
        else:
            alloc_b = 0.0

    _, std_b = get_stats(state.history_b)
    vol_b_pct = std_b / priceB if priceB > 0 else 0

    if vol_b_pct > 0.03:
        alloc_b *= 0.5
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