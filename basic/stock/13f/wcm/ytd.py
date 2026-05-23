import mplfinance as mpf
from portfolio import *

mpf.plot(
    portfolio_ohlc,
    type="candle",
    style="charles",
    title="WCM-style Portfolio | YTD Candlestick",
    ylabel="Portfolio Value (Weighted)",
    volume=False,
    figsize=(14, 7),
    datetime_format="%Y-%m",
    yscale="log"
)


