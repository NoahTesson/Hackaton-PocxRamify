
history = []

def make_decision(epoch: int, price: float):
    history.append(price)

    if len(history) < 50: 
        return {"Asset A": 0.5, "Cash": 0.5}

    import math
    from math import tanh

    returns = [
        (history[i] - history[i-1]) / history[i-1]
        for i in range(len(history)-20, len(history))
    ]
    volatility = math.sqrt(sum(r*r for r in returns) / len(returns))
    volatility = max(volatility, 1e-6)

    alpha = 2 / (10 + 1)
    start_index = max(0, len(history) - 11) 
    ema = history[start_index]
    for p in history[start_index + 1:]:
        ema = ema + alpha * (p - ema)
    momentum = (history[-1] - ema) / ema

    ma30 = sum(history[-30:]) / 30
    deviation = (price - ma30) / ma30
    deviation /= volatility 

    vol_factor = min(volatility * 50, 1.0)
    w_mom = 0.5 + 0.3 * vol_factor
    w_mr = 0.5 - 0.3 * vol_factor

    signal = w_mom * momentum - w_mr * deviation

    allocation_asset = 0.5 + 0.5 * tanh(signal * 5)
    
    CRASH_WINDOW = 10 
    CRASH_THRESHOLD = 0.05 
    
    if len(history) >= CRASH_WINDOW:
        max_price_recent = max(history[-CRASH_WINDOW:])
        
        current_drawdown = (max_price_recent - price) / max_price_recent

        if current_drawdown > CRASH_THRESHOLD:
            allocation_asset = 0.1 
        
    allocation_asset = max(0.05, min(0.95, allocation_asset))

    return {
        "Asset A": allocation_asset,
        "Cash": 1 - allocation_asset
    }