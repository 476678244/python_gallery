from stock.tiger.AMD import cash_after_amd, stock_value_amd
from stock.tiger.NVDA import stock_value_nvda

realtime_cash = cash_after_amd()
print('--------------------')
print('realtime_cash: {}'.format(realtime_cash))
print('--------------------')

realtime_stock_value = stock_value_amd()
realtime_stock_value += stock_value_nvda()
print('--------------------')
print('realtime_stock_value: {}'.format(realtime_stock_value))
print('--------------------')

realtime_total_value = realtime_stock_value + realtime_cash
print('--------------------')
print('realtime_total_value: {}'.format(realtime_total_value))
print('--------------------')
