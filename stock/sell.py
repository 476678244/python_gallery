from stock.bill import Bill


class Sell(Bill):

    def __init__(self, name, price, num, time):
        super().__init__(name, price, num, 1.99, time)