import yfinance as yf
import efinance as ef


def get_close_price(symbol):
    ticker = yf.Ticker(symbol)
    today_data = ticker.history(period='1d')
    return today_data['Close'][0]


def get_latest_price(symbol):
    hist = ef.stock.get_quote_history(symbol)
    if not hist.empty:
        return hist['收盘'].iloc[-1]
    else:
        return get_close_price(symbol)
