from stock.tiger.AMD import cash_after_amd, stock_value_amd
from stock.tiger.CPNG import stock_value_cpng
from stock.tiger.NVDA import stock_value_nvda
from stock.tiger.UVXY import stock_value_uvxy, cash_after_uvxy

realtime_cash = cash_after_amd()
realtime_cash = cash_after_uvxy(realtime_cash)
print('--------------------')
print('realtime_cash: {}'.format(realtime_cash))
print('--------------------')

realtime_stock_value = stock_value_amd()
realtime_stock_value += stock_value_nvda()
realtime_stock_value += stock_value_cpng()
realtime_stock_value += stock_value_uvxy()
print('--------------------')
print('realtime_stock_value: {}'.format(realtime_stock_value))
print('--------------------')

realtime_total_value = realtime_stock_value + realtime_cash
print('--------------------')
print('realtime_total_value: {}'.format(realtime_total_value))
print('--------------------')
