from stock.buy import Buy

from stock.computer import compute_avg_cost, compute_buys_income, compute_sells, compute_stock_value
from stock.stockinfo import get_latest_price
from stock.utils import strptime

b0722 = Buy('UVXY', 12.01, 14, strptime("07-22-2022 22"))
b0727 = Buy('UVXY', 11.35, 20, strptime("07-27-2022 22"))
b0806 = Buy('UVXY', 9.95, 30, strptime("08-06-2022 22"))

all_buys = [b0722, b0727, b0806]

compute_avg_cost(all_buys, 'all_buys UVXY')

close_price = get_latest_price('UVXY')
print('UVXY latest_price is : {}'.format(close_price))

total_income = compute_buys_income(all_buys, close_price)
print('total_income UVXY: {}'.format(total_income))


def stock_value_uvxy():
    return compute_stock_value(all_buys, close_price, 'UVXY')