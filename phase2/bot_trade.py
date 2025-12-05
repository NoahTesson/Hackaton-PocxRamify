import pandas as pd
import numpy as np

history_prices = []

def make_decision(epoch: int, price: float):
    global history_prices
    history_prices.append(price)

    if len(history_prices) < 60:
        return {'Asset B': 0.0, 'Cash': 1.0}

    window_size = 200
    df = pd.DataFrame(history_prices[-window_size:], columns=['close'])
    df['ema_fast'] = df['close'].ewm(span=20, adjust=False).mean()
    df['ema_slow'] = df['close'].ewm(span=60, adjust=False).mean()

    period = 14
    delta = df['close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
    rs = gain / loss.replace(0, 1e-9)
    df['rsi'] = 100 - (100 / (1 + rs))

    df['returns'] = df['close'].pct_change()
    current_vol = df['returns'].rolling(window=20).std().iloc[-1]
    current_price = df['close'].iloc[-1]
    ema_fast = df['ema_fast'].iloc[-1]
    ema_slow = df['ema_slow'].iloc[-1]
    current_rsi = df['rsi'].iloc[-1]

    allocation = 0.0

    is_bull_trend = current_price > ema_slow
    
    if is_bull_trend:
        if current_price > ema_fast:
            allocation = 1.0
        else:
            allocation = 0.8
        if current_rsi > 80:
            allocation = 0.7
            
    else:
        allocation = 0.0
        if current_rsi < 25:
            allocation = 0.4

    target_vol = 0.015
    
    if current_vol > 0:
        vol_scalar = target_vol / current_vol
        vol_scalar = min(1.0, vol_scalar)
        allocation = allocation * vol_scalar

    allocation = max(0.0, min(1.0, allocation))

    if allocation < 0.05:
        allocation = 0.0

    return {
        'Asset B': allocation,
        'Cash': 1.0 - allocation
    }