
import math
from math import tanh
import pandas as pd
import numpy as np

history = []

def make_decision(epoch: int, price: float):
    global history
    history.append(price)


    if len(history) < 50: 
        return {"Asset A": 0.5, "Cash": 0.5}


    prices_series = pd.Series(history)

    returns = prices_series.pct_change().iloc[-20:].dropna()
    
    volatility = returns.std() if not returns.empty else 1e-6
    volatility = max(volatility, 1e-6)

    ema_10 = prices_series.ewm(span=10, adjust=False).mean().iloc[-1]
    momentum = (price - ema_10) / ema_10

    ma30 = prices_series.rolling(window=30).mean().iloc[-1]
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
        max_price_recent = np.max(history[-CRASH_WINDOW:]) 
        current_drawdown = (max_price_recent - price) / max_price_recent

        if current_drawdown > CRASH_THRESHOLD:
            allocation_asset = 0.05 
        
    allocation_asset = np.clip(allocation_asset, 0.05, 0.95)

    return {
        "Asset A": allocation_asset,
        "Cash": 1 - allocation_asset
    }