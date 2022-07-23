from stock.computer import compute_buys_income


def find_price(rescue_num, latest_price, low_buys, threshold):
    # num * (april_avg - close_price) <= compute_buys_income(june_buys, close_price, 'june_buys AMD') - 1.99
    # (compute_buys_income(june_buys, close_price, 'june_buys AMD')- 1.99)/ num + close_price >= april_avg
    tmp_price = latest_price
    while (compute_buys_income(low_buys, tmp_price) - 1.99) / rescue_num + tmp_price < threshold:
        tmp_price = tmp_price + 0.1
    return tmp_price
