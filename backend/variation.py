def get_variation(info: dict):
    price_before = info.get('previousClose')
    actual_price = info.get('regularMarketPrice')

    if price_before and actual_price:
        variation = ((actual_price - price_before) / price_before) * 100
        return variation
    return None
