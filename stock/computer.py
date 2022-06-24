import yfinance as yf
import efinance as ef

def compute_avg_cost(buys, hint=''):
    cost = 0
    num = 0
    for buy in buys:
        cost += buy.price * buy.num + buy.fee
        num += buy.num
    avg_cost = cost / num
    if len(hint) > 0:
        print('{} avg costs: {}'.format(hint, "%.2f" % avg_cost))
    return avg_cost, num, cost


def get_close_price(symbol):
    ticker = yf.Ticker(symbol)
    today_data = ticker.history(period='1d')
    return today_data['Close'][0]


def get_latest_price(symbol):
    hist = ef.stock.get_quote_history(symbol)
    return hist['收盘'].iloc[-1]


def compute_buys_income(buys, close_price, hint=''):
    avg_cost, num, cost = compute_avg_cost(buys)
    current_value = close_price * num
    current_income = current_value - cost
    if len(hint) > 0:
        print('{} current income: {}'.format(hint, "%.2f" % current_income))
    return current_income
