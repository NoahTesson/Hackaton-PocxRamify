import pandas as pd
import numpy as np
from collections import deque

WINDOW_SHORT = 20
WINDOW_MED = 50
WINDOW_LONG = 100
RSI_PERIOD = 14
VOLATILITY_WINDOW = 20

class BotState:
    def __init__(self):
        self.prices = deque(maxlen=200)
        self.allocations = deque(maxlen=10)

state = BotState()

class AlphaEngine:
    @staticmethod
    def calculate_ema(series, span):
        return series.ewm(span=span, adjust=False).mean()

    @staticmethod
    def calculate_rsi(series, period=14):
        delta = series.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
        rs = gain / loss.replace(0, 1e-9)
        return 100 - (100 / (1 + rs))

    @staticmethod
    def calculate_volatility(series, window=20):
        return series.pct_change().rolling(window=window).std()

    @staticmethod
    def get_market_regime(df):
        curr = df.iloc[-1]
        ema_short_slope = (df['ema_short'].iloc[-1] - df['ema_short'].iloc[-3]) / df['ema_short'].iloc[-1]
        ema_long_slope = (df['ema_long'].iloc[-1] - df['ema_long'].iloc[-3]) / df['ema_long'].iloc[-1]
        
        price = curr['close']
        if price > curr['ema_long'] and ema_long_slope > -0.0005:
            if price > curr['ema_med']:
                return "STRONG_BULL"
            return "WEAK_BULL"

        if price < curr['ema_long']:
            return "BEAR"

        return "NEUTRAL"

def make_decision(epoch: int, price: float):
    global state
    state.prices.append(price)

    if len(state.prices) < WINDOW_LONG + 5:
        return {'Asset A': 0.0, 'Cash': 1.0}

    df = pd.DataFrame(list(state.prices), columns=['close'])

    df['ema_short'] = AlphaEngine.calculate_ema(df['close'], WINDOW_SHORT)
    df['ema_med'] = AlphaEngine.calculate_ema(df['close'], WINDOW_MED)
    df['ema_long'] = AlphaEngine.calculate_ema(df['close'], WINDOW_LONG)
    df['rsi'] = AlphaEngine.calculate_rsi(df['close'], RSI_PERIOD)
    df['volatility'] = AlphaEngine.calculate_volatility(df['close'], VOLATILITY_WINDOW)

    current = df.iloc[-1]
    regime = AlphaEngine.get_market_regime(df)
    raw_allocation = 0.0
    
    if regime == "STRONG_BULL":
        raw_allocation = 0.8
        if current['rsi'] < 70:
            raw_allocation = 1.0
        if current['rsi'] < 40: 
            raw_allocation = 1.0
            
    elif regime == "WEAK_BULL":
        raw_allocation = 0.5
        if current['close'] > current['ema_short']:
            raw_allocation += 0.2
        if current['rsi'] > 65:
            raw_allocation -= 0.3

    elif regime == "BEAR":
        raw_allocation = 0.0
        if current['rsi'] < 20:
            raw_allocation = 0.2
        else:
            raw_allocation = 0.0
            
    else:
        if current['rsi'] < 30:
            raw_allocation = 0.6
        elif current['rsi'] > 70:
            raw_allocation = 0.0
        else:
            raw_allocation = 0.2

    vol_scaling_factor = 1.0

    if not np.isnan(current['volatility']):
        if current['volatility'] > 0.025: 
            vol_scaling_factor = 0.5
        if current['volatility'] > 0.05:
            vol_scaling_factor = 0.0
            
    final_allocation_asset = raw_allocation * vol_scaling_factor
    final_allocation_asset = max(0.0, min(1.0, final_allocation_asset))
    
    return {
        'Asset A': final_allocation_asset,
        'Cash': 1.0 - final_allocation_asset
    }