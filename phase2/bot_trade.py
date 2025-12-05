import pandas as pd
import numpy as np
from collections import deque

history_prices = deque(maxlen=300)

def make_decision(epoch: int, price: float):
    global history_prices
    history_prices.append(price)

    # 1. WARMUP
    # On a besoin d'au moins 60 points pour l'EMA lente
    if len(history_prices) < 60:
        return {'Asset B': 0.0, 'Cash': 1.0}

    # 2. DATA PREPARATION
    # Conversion rapide : la liste ne fait JAMAIS plus de 300 éléments.
    # C'est très léger pour la RAM.
    df = pd.DataFrame(list(history_prices), columns=['close'])

    # 3. INDICATORS
    
    # A. Trend (EMA)
    # EMA 20 (Rapide) et EMA 60 (Lente)
    df['ema_fast'] = df['close'].ewm(span=20, adjust=False).mean()
    df['ema_slow'] = df['close'].ewm(span=60, adjust=False).mean()

    # B. RSI (14)
    delta = df['close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
    rs = gain / loss.replace(0, 1e-9)
    df['rsi'] = 100 - (100 / (1 + rs))

    # C. Volatility (20)
    df['returns'] = df['close'].pct_change()
    current_vol = df['returns'].rolling(window=20).std().iloc[-1]

    # Valeurs actuelles
    current_price = df['close'].iloc[-1]
    ema_fast = df['ema_fast'].iloc[-1]
    ema_slow = df['ema_slow'].iloc[-1]
    current_rsi = df['rsi'].iloc[-1]

    # 4. STRATEGY LOGIC (Asset B Focus)
    
    allocation = 0.0
    
    # Check Regime: Bull or Bear?
    is_bull_trend = current_price > ema_slow
    
    if is_bull_trend:
        # === BULL MARKET ===
        if current_price > ema_fast:
            # Full Momentum
            allocation = 1.0
        else:
            # Correction saine
            allocation = 0.8
            
        # Profit Taking sur excès (RSI > 80)
        if current_rsi > 80:
            allocation = 0.7
            
    else:
        # === BEAR MARKET ===
        # Défense absolue pour éviter les -43%
        allocation = 0.0
        
        # Sauf si Crash extrême (Rebond technique)
        if current_rsi < 25:
            allocation = 0.4
            
    # 5. VOLATILITY SCALING (Risk Management)
    target_vol = 0.015
    
    if current_vol > 0:
        vol_scalar = target_vol / current_vol
        vol_scalar = min(1.0, vol_scalar)
        allocation = allocation * vol_scalar

    # 6. FINAL CHECKS
    allocation = max(0.0, min(1.0, allocation))
    
    if allocation < 0.05:
        allocation = 0.0

    return {
        'Asset B': allocation,
        'Cash': 1.0 - allocation
    }
