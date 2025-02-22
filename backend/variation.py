def get_variation(info):
    if info:
        price_before = info.get('previousClose')
        actual_price = info.get('regularMarketPrice')
        if price_before and actual_price:
            variation = ((actual_price - price_before) / price_before) * 100
            return variation
    return None

if __name__ == "__main__":
    import yfinance as yf
    stock = yf.Ticker('AAPL')
    data = stock.info
    variation = get_variation(data)
    print(f"{variation:.2f}" if variation is not None else "No variation data available")