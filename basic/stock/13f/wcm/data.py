import datetime
from weights import weights
import yfinance as yf
import pandas as pd
import numpy as np
import mplfinance as mpf
from datetime import datetime

tickers = list(weights.keys())

start = f"{datetime.now().year}-01-01"
end = datetime.now().strftime("%Y-%m-%d")

data = yf.download(
    tickers,
    start=start,
    end=end,
    group_by="ticker",
    auto_adjust=True,
    progress=False
)
