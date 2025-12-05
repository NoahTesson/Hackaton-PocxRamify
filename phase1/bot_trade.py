# bot_trade.py
# Stratégie: crossover de moyennes mobiles + allocation smooth

history = []

def make_decision(epoch: int, price: float):
    history.append(price)
    
    if len(history) < 30:
        return {"Asset A": 0.5, "Cash": 0.5}
    
    # Momentum (10-period)
    momentum = (history[-1] - history[-10]) / history[-10]
    
    # Mean reversion (deviation from 30-MA)
    ma_30 = sum(history[-30:]) / 30
    deviation = (price - ma_30) / ma_30
    
    # Combined signal (60% momentum, 40% mean reversion)
    combined_signal = momentum * 0.6 - deviation * 0.4
    
    allocation_asset = 0.5 + max(min(combined_signal * 3, 0.4), -0.4)
    allocation_asset = max(0.1, min(0.9, allocation_asset))
    
    return {
        "Asset A": allocation_asset,
        "Cash": 1 - allocation_asset
    }