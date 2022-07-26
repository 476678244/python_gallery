from stock.buy import Buy

from stock.computer import compute_avg_cost, compute_buys_income, compute_sells, compute_stock_value
from stock.stockinfo import get_latest_price
from stock.utils import strptime

b0406 = Buy('NVDA', 252, 3, strptime("04-06-2022 22"))

all_buys = [b0406]

compute_avg_cost(all_buys, 'all_buys NVDA')

close_price = get_latest_price('NVDA')
print('NVDA latest_price is : {}'.format(close_price))

total_income = compute_buys_income(all_buys, close_price)
print('total_income NVDA: {}'.format(total_income))


def stock_value_nvda():
    return compute_stock_value(all_buys, close_price, 'NVDA')
