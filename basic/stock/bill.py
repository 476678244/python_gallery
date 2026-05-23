class Bill:

    def __init__(self, name, price, num, fee, time):
        self.name = name
        self.price = price
        self.num = num
        self.fee = fee
        self.time = time

    def __str__(self):
        return '{}: price {}, num {}, time {}'.format(self.name, self.price, self.num, self.time)
