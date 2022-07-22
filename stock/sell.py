from stock.bill import Bill


class Sell(Bill):

    def __init__(self, name, price, num, time, cost_price, fee):
        super().__init__(name, price, num, fee, time)
        self.cost_price = cost_price