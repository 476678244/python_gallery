from stock.buy import Buy

from stock.computer import compute_avg_cost, compute_buys_income, get_close_price
from stock.utils import strptime

b0404 = Buy('AMD', 107.96, 4, strptime("04-04-2022 22"))
b0406 = Buy('AMD', 105.09, 4, strptime("04-06-2022 18"))
b0408 = Buy('AMD', 100.50, 7, strptime("04-08-2022 22"))
b0617 = Buy('AMD', 81.709, 4, strptime("06-17-2022 12"))

all_buys = [b0404, b0406, b0408, b0617]
april_buys = [b0404, b0406, b0408]
june_buys = [b0617]

compute_avg_cost(all_buys, 'all_buys AMD')
compute_avg_cost(april_buys, 'april_buys AMD')
compute_avg_cost(june_buys, 'june_buys AMD')

close_price = get_close_price('AMD')
compute_buys_income(all_buys, close_price, 'all_buys AMD')
compute_buys_income(june_buys, close_price, 'june_buys AMD')
print(close_price)