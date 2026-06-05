import efinance as ef
# 股票代码
stock_code = 'AMD'
hist = ef.stock.get_quote_history(stock_code)
close_price = hist['收盘'].iloc[-1]
print(close_price)
print(hist)