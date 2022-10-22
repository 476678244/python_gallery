from stock.buy import Buy

from stock.computer import compute_avg_cost, compute_buys_income, compute_sells, compute_stock_value
from stock.sell import Sell
from stock.stockinfo import get_latest_price
from stock.utils import strptime

b0722 = Buy('UVXY', 12.01, 14, strptime("07-22-2022 22"))
b0727 = Buy('UVXY', 11.35, 20, strptime("07-27-2022 22"))
b0806 = Buy('UVXY', 9.95, 30, strptime("08-06-2022 22"))
b0812 = Buy('UVXY', 8.9, 25, strptime("08-12-2022 22"))

all_buys = [b0722, b0727, b0806, b0812]

avg_cost, num, cost = compute_avg_cost(all_buys, 'all_buys UVXY')

close_price = get_latest_price('UVXY')
print('UVXY latest_price is : {}'.format(close_price))

total_income = compute_buys_income(all_buys, close_price)
print('total_income UVXY: {}'.format(total_income))

sell0923 = Sell('UVXY', 11, 86, strptime("09-23-2022 12"), avg_cost, 2.01)
sell_gain, sell_got_cash = compute_sells([sell0923])

left_buy = Buy('UVXY', avg_cost, 3, strptime("09-23-2022 22"))
left_buys = [left_buy]


def stock_value_uvxy():
    return compute_stock_value(left_buys, close_price, 'UVXY')


def cash_after_uvxy(realtime_cash):
    return realtime_cash - cost + sell_got_cash