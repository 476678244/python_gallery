import yfinance as yf

aapl = yf.Ticker("aapl")
aapl
aapl.info['forwardPE']
aapl.earnings
aapl.quarterly_earnings
aapl_historical = aapl.history(start="2020-02-02", end="2020-06-07", interval="1wk")
aapl_historical
