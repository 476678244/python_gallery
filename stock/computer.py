def compute_avg_cost(buys, hint=''):
    cost = 0
    num = 0
    for buy in buys:
        cost += buy.price * buy.num + buy.fee
        num += buy.num
    avg_cost = cost / num
    print('{} costs: {}'.format(hint, "%.2f" % avg_cost))
    return avg_cost

