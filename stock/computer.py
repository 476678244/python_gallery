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


def compute_stock_value(left_buys, close_price, hint=''):
    stock_value = 0
    for left_buy in left_buys:
        stock_value += close_price * left_buy.num
    print('{} stock_value: {},   price: {}'.format(hint, "%.2f" % stock_value, close_price))
    return stock_value


def compute_buys_income(buys, close_price, hint=''):
    avg_cost, num, cost = compute_avg_cost(buys)
    current_value = close_price * num
    current_income = current_value - cost
    if len(hint) > 0:
        print('{} current income: {}'.format(hint, "%.2f" % current_income))
    return current_income


def compute_sells(sells, hint=''):
    sell_gain = 0
    sell_got_cash = 0
    for sell in sells:
        sell_gain += (sell.price - sell.cost_price) * sell.num - sell.fee
        sell_got_cash += sell.price * sell.num - sell.fee
    if len(hint) > 0:
        print('{} sell_gain: {}'.format(hint, "%.2f" % sell_gain))
        print('{} sell_got_cash: {}'.format(hint, "%.2f" % sell_got_cash))
    return sell_gain, sell_got_cash


# 104 * 9, if buy 3 * 94, (104 * 9 + 3 * 94)/(9+3) = 100
# (buy_num * target_close_price + (num * avg_cost ))/(buy_num + num) <= target_avg_cost
# buy_num * target_close_price + (num * avg_cost ) <= target_avg_cost * (buy_num + num)
# buy_num * target_close_price <= (target_avg_cost * (buy_num + num) - (num * avg_cost))
# target_close_price = (target_avg_cost * (buy_num + num) - (num * avg_cost)) / buy_num
def target_avg_cost_need_price(target_avg_cost, min_buy_num, max_buy_num, buys):
    for buy_num in range(min_buy_num, max_buy_num + 1):
        avg_cost, num, cost = compute_avg_cost(buys)
        target_close_price = (target_avg_cost * (buy_num + num) - num * avg_cost) / buy_num
        print('If buy {}, To cost at {}, need buy at {}'.format(buy_num, target_avg_cost, target_close_price))