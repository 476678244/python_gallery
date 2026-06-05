
import mplfinance as mpf
from portfolio import *
benchmarks = {
    "SP500": "^GSPC",     # S&P 500
}

benchmark_data = yf.download(
    list(benchmarks.values()),
    start=start,
    end=end,
    auto_adjust=True,
    progress=False
)

# ===== 组合收盘价 =====
portfolio_close = portfolio_ohlc["Close"]

# 归一化（起点 = 1）
portfolio_close = portfolio_close / portfolio_close.iloc[0]

# ===== 基准收盘价 =====
sp500_close = benchmark_data["Close"][benchmarks["SP500"]]

sp500_close = sp500_close / sp500_close.iloc[0]

rs_vs_sp500 = portfolio_close / sp500_close

import matplotlib.pyplot as plt

plt.figure(figsize=(14, 6))
plt.plot(rs_vs_sp500.index, rs_vs_sp500, label="Portfolio / S&P 500")
plt.yscale("log")
plt.title("Relative Strength (Log) | Portfolio vs S&P 500")
plt.ylabel("Relative Strength (log)")
plt.grid(True, which="both", linestyle="--", alpha=0.4)
plt.legend()
# plt.show()


sp500 = yf.download("^GSPC", start=start, end=end, auto_adjust=True, progress=False)

if isinstance(sp500.columns, pd.MultiIndex):
    sp500 = sp500.xs("^GSPC", axis=1, level="Ticker")

# 转为周线 OHLC
sp500_weekly = sp500.resample("W").agg({
    "Open": "first",
    "High": "max",
    "Low": "min",
    "Close": "last"
})

portfolio_weekly = portfolio_ohlc.resample("W").agg({
    "Open": "first",
    "High": "max",
    "Low": "min",
    "Close": "last"
})

portfolio_norm = portfolio_weekly / portfolio_weekly["Close"].iloc[0]
sp500_norm = sp500_weekly / sp500_weekly["Close"].iloc[0]

ap_sp500 = mpf.make_addplot(
    sp500_norm["Close"],
    panel=0,
    color="black",
    linestyle="--",
    width=1.2
)

mpf.plot(
    portfolio_norm,
    type="candle",
    style="charles",
    title="Weekly Log Chart | Portfolio vs S&P 500",
    ylabel="Normalized Value (log)",
    yscale="log",
    volume=False,
    addplot=[ap_sp500],
    figsize=(15, 8)
)



