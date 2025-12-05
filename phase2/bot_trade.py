import math
from collections import deque

history = deque(maxlen=300)

def calculate_ema(data, span):
    if not data:
        return 0.0
    alpha = 2 / (span + 1)
    ema = data[0]
    for price in data[1:]:
        ema = alpha * price + (1 - alpha) * ema
    return ema

def calculate_rsi(data, period=14):
    if len(data) < period + 1:
        return 50.0
    
    gains = 0.0
    losses = 0.0
    
    for i in range(1, period + 1):
        change = data[i] - data[i-1]
        if change > 0:
            gains += change
        else:
            losses -= change
            
    avg_gain = gains / period
    avg_loss = losses / period
    
    for i in range(period + 1, len(data)):
        change = data[i] - data[i-1]
        gain = change if change > 0 else 0.0
        loss = -change if change < 0 else 0.0
        
        avg_gain = (avg_gain * (period - 1) + gain) / period
        avg_loss = (avg_loss * (period - 1) + loss) / period
        
    if avg_loss == 0:
        return 100.0
    
    rs = avg_gain / avg_loss
    return 100.0 - (100.0 / (1.0 + rs))

def calculate_volatility(data, window=20):
    if len(data) < window + 1:
        return 0.0
    
    returns = []
    subset = list(data)[-window-1:]
    for i in range(1, len(subset)):
        if subset[i-1] == 0:
            ret = 0
        else:
            ret = (subset[i] - subset[i-1]) / subset[i-1]
        returns.append(ret)
        
    mean_ret = sum(returns) / len(returns)
    variance = sum((r - mean_ret) ** 2 for r in returns) / len(returns)
    return math.sqrt(variance)

def make_decision(epoch: int, price: float):
    global history
    history.append(price)

    if len(history) < 50:
        return {'Asset B': 0.0, 'Cash': 1.0}

    prices = list(history)
    current_price = prices[-1]
    
    ema_fast = calculate_ema(prices, 10)
    ema_slow = calculate_ema(prices, 40)
    
    rsi_val = calculate_rsi(prices, 14)
    vol_val = calculate_volatility(history, 20)

    allocation = 0.0
    
    is_bull_trend = current_price > ema_slow
    
    if is_bull_trend:
        if current_price > ema_fast:
            allocation = 1.0
        else:
            allocation = 0.6
            
        if rsi_val > 80:
            allocation = 0.5
        if rsi_val > 90:
            allocation = 0.0
            
    else:
        allocation = 0.0
        
    recent_high = 0
    recent_prices = prices[-15:]
    if recent_prices:
        recent_high = max(recent_prices)
    
    if recent_high > 0:
        drawdown_pct = (current_price - recent_high) / recent_high
        if drawdown_pct < -0.04:
            allocation = 0.0

    target_vol = 0.02
    
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
