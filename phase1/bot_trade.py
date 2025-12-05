
history = []

def make_decision(epoch: int, price: float):
    history.append(price)

    if len(history) < 3:
        return {"Asset A": 0.5, "Cash": 0.5}

    short_window = 5
    long_window = 20

    short_ma = sum(history[-short_window:]) / min(len(history), short_window)
    long_ma = sum(history[-long_window:]) / min(len(history), long_window)

    signal = (short_ma - long_ma) / long_ma
    allocation_asset = 0.5 + max(min(signal * 5, 0.3), -0.3)  
    allocation_asset = max(0.2, min(0.8, allocation_asset))

    return {
        "Asset A": allocation_asset,
        "Cash": 1 - allocation_asset
    }
