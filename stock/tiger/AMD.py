from stock.buy import Buy

from stock.computer import compute_avg_cost, compute_buys_income
from stock.stockinfo import get_latest_price
from stock.utils import strptime

b0404 = Buy('AMD', 107.96, 4, strptime("04-04-2022 22"))
b0406 = Buy('AMD', 105.09, 4, strptime("04-06-2022 18"))
b0408 = Buy('AMD', 100.50, 7, strptime("04-08-2022 22"))
b0617 = Buy('AMD', 81.709, 4, strptime("06-17-2022 12"))
b0630 = Buy('AMD', 78.11, 6, strptime("06-30-2022 12"))

all_buys = [b0404, b0406, b0408, b0617, b0630]
april_buys = [b0404, b0406, b0408]
june_buys = [b0617, b0630]

compute_avg_cost(all_buys, 'all_buys AMD')
april_avg, april_num, cost = compute_avg_cost(april_buys, 'april_buys AMD')
compute_avg_cost(june_buys, 'june_buys AMD')

close_price = get_latest_price('AMD')
print('latest_price is : ')
print(close_price)


def find_price(rescue_num, latest_price, low_buys, threshold):
    # num * (april_avg - close_price) <= compute_buys_income(june_buys, close_price, 'june_buys AMD') - 1.99
    # (compute_buys_income(june_buys, close_price, 'june_buys AMD')- 1.99)/ num + close_price >= april_avg
    tmp_price = latest_price
    while (compute_buys_income(low_buys, tmp_price) - 1.99) / rescue_num + tmp_price < threshold:
        tmp_price = tmp_price + 0.1
    return tmp_price


for n in range(1, april_num + 1):
    print('if want to rescue : {} , price should be : '.format(n))
    print(find_price(n, close_price, june_buys, april_avg))

compute_buys_income(all_buys, close_price, 'all_buys AMD')
compute_buys_income(june_buys, close_price, 'june_buys AMD')
