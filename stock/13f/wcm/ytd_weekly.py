
import mplfinance as mpf
from portfolio import *


portfolio_weekly = portfolio_ohlc.resample("W").agg({
    "Open": "first",
    "High": "max",
    "Low": "min",
    "Close": "last"
})

mpf.plot(
    portfolio_weekly,
    type="candle",
    style="charles",
    title="WCM-style Portfolio | Weekly Candlestick (Log Scale)",
    yscale="log",
    volume=False,
    figsize=(14, 7),
)
