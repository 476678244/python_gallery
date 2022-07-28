from stock.buy import Buy

from stock.computer import compute_avg_cost, compute_buys_income, compute_sells, compute_stock_value
from stock.stockinfo import get_latest_price
from stock.utils import strptime

b0517 = Buy('CPNG', 12, 3, strptime("05-17-2022 22"))

all_buys = [b0517]

compute_avg_cost(all_buys, 'all_buys CPNG')

close_price = get_latest_price('CPNG')
print('CPNG latest_price is : {}'.format(close_price))

total_income = compute_buys_income(all_buys, close_price)
print('total_income CPNG: {}'.format(total_income))


def stock_value_cpng():
    return compute_stock_value(all_buys, close_price, 'CPNG')