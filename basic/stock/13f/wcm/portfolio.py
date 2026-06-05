from weights import *
from data import *

portfolio_ohlc = None

for ticker, w in weights.items():
    df = data[ticker][["Open", "High", "Low", "Close"]].copy()
    df = df / df.iloc[0]["Close"]   # 归一化
    df *= w                         # 权重加权

    if portfolio_ohlc is None:
        portfolio_ohlc = df
    else:
        portfolio_ohlc += df
