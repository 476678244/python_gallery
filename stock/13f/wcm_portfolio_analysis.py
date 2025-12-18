import yfinance as yf
import pandas as pd
import numpy as np
import mplfinance as mpf
import matplotlib.pyplot as plt
from datetime import datetime

# =========================================================
# 1. 股票池 & 原始 WCM 权重（Conviction）
# =========================================================
RAW_WEIGHTS = {
    "SE": 0.098,
    "APP": 0.073,
    "TSM": 0.057,
    "SPOT": 0.051,
    "ASML": 0.039,
    "PM": 0.038,
    "IBN": 0.034,
    "LIN": 0.034,
    "CPNG": 0.033,
    "AMZN": 0.029,
    "MELI": 0.026,
}

TICKERS = list(RAW_WEIGHTS.keys())
N = len(TICKERS)

# =========================================================
# 2. 时间区间（避免非交易日偏差）
# =========================================================
START = pd.Timestamp(datetime.now().year, 1, 1) - pd.offsets.BDay(5)
END = datetime.now().strftime("%Y-%m-%d")

# =========================================================
# 3. 数据下载
# =========================================================
def download_prices(tickers, start, end):
    prices = yf.download(
        tickers,
        start=start,
        end=end,
        auto_adjust=True,
        progress=False,
    )["Close"]

    return prices.dropna(how="any")

# =========================================================
# 4. 权重生成器
# =========================================================
def get_weights(mode="wcm"):
    if mode == "wcm":
        total = sum(RAW_WEIGHTS.values())
        return {k: v / total for k, v in RAW_WEIGHTS.items()}
    elif mode == "equal":
        return {k: 1 / N for k in TICKERS}
    else:
        raise ValueError("weight mode must be 'wcm' or 'equal'")

# =========================================================
# 5. 构建组合净值（唯一金融上严格的做法）
# =========================================================
def build_portfolio(prices, weight_mode="wcm"):
    weights = get_weights(weight_mode)
    normalized = prices / prices.iloc[0]
    close = sum(weights[t] * normalized[t] for t in TICKERS)
    return pd.DataFrame({"Close": close})

# =========================================================
# 6. Synthetic OHLC（仅用于 K 线可视化）
# =========================================================
def make_synthetic_ohlc(close_df):
    ohlc = pd.DataFrame(index=close_df.index)
    ohlc["Close"] = close_df["Close"]
    ohlc["Open"] = close_df["Close"].shift(1)
    ohlc["High"] = close_df["Close"].rolling(2).max()
    ohlc["Low"] = close_df["Close"].rolling(2).min()
    return ohlc.dropna()

# =========================================================
# 7. S&P 500
# =========================================================
def get_sp500(start, end):
    sp = yf.download(
        "^GSPC",
        start=start,
        end=end,
        auto_adjust=True,
        progress=False,
    )["Close"]

    return sp.dropna()

# =========================================================
# 8. 可视化函数
# =========================================================
def plot_ytd_candlestick(ohlc, title):
    mpf.plot(
        ohlc,
        type="candle",
        style="charles",
        title=title,
        ylabel="Value (Log)",
        volume=False,
        figsize=(14, 7),
        yscale="log",
        datetime_format="%Y-%m",
    )

def plot_weekly_candlestick(ohlc, title):
    weekly = ohlc.resample("W-FRI").agg({
        "Open": "first",
        "High": "max",
        "Low": "min",
        "Close": "last",
    }).dropna()

    mpf.plot(
        weekly,
        type="candle",
        style="charles",
        title=title,
        ylabel="Value (Log)",
        volume=False,
        figsize=(14, 7),
        yscale="log",
        datetime_format="%Y-%m-%d",
    )

def plot_three_way_comparison(p_wcm, p_eq, sp500):
    df = pd.concat(
        [p_wcm["Close"], p_eq["Close"], sp500],
        axis=1
    ).dropna()

    df.columns = ["WCM", "Equal", "SP500"]
    df = df / df.iloc[0]

    plt.figure(figsize=(14, 7))
    plt.plot(df.index, df["WCM"], label="WCM-weighted")
    plt.plot(df.index, df["Equal"], label="Equal-weight")
    plt.plot(df.index, df["SP500"], label="S&P 500")

    plt.yscale("log")
    plt.title("WCM vs Equal vs S&P 500 (Log, Normalized)")
    plt.ylabel("Normalized Value")
    plt.grid(True, which="both", linestyle="--", alpha=0.4)
    plt.legend()
    plt.show()

def plot_rs(series_a, series_b, label_a, label_b):
    rs = series_a / series_b

    plt.figure(figsize=(14, 6))
    plt.plot(rs.index, rs, label=f"{label_a} / {label_b}")
    plt.yscale("log")
    plt.title(f"Relative Strength | {label_a} vs {label_b}")
    plt.ylabel("RS (Log)")
    plt.grid(True, which="both", linestyle="--", alpha=0.4)
    plt.legend()
    plt.show()

# =========================================================
# 9. CLI 主入口
# =========================================================
if __name__ == "__main__":
    print("WCM-style Portfolio Analysis Tool (Final)")
    print("1. WCM 权重组合（K线）")
    print("2. 等权组合（K线）")
    print("3. WCM vs 等权（RS）")
    print("4. 加入 S&P 500（三方对比 + RS）")
    print("5. 全部执行")

    choice = input("请选择要执行的操作 (1-5): ")

    prices = download_prices(TICKERS, START, END)
    p_wcm = build_portfolio(prices, "wcm")
    p_eq = build_portfolio(prices, "equal")
    sp500 = get_sp500(START, END)

    if choice in {"1", "5"}:
        ohlc = make_synthetic_ohlc(p_wcm)
        plot_ytd_candlestick(ohlc, "WCM-weighted Portfolio | YTD")
        plot_weekly_candlestick(ohlc, "WCM-weighted Portfolio | Weekly")

    if choice in {"2", "5"}:
        ohlc = make_synthetic_ohlc(p_eq)
        plot_ytd_candlestick(ohlc, "Equal-weight Portfolio | YTD")
        plot_weekly_candlestick(ohlc, "Equal-weight Portfolio | Weekly")

    if choice in {"3", "5"}:
        plot_rs(p_wcm["Close"], p_eq["Close"], "WCM", "Equal Weight")

    if choice in {"4", "5"}:
        plot_three_way_comparison(p_wcm, p_eq, sp500)
        plot_rs(p_wcm["Close"], sp500, "WCM", "S&P 500")
        plot_rs(p_eq["Close"], sp500, "Equal Weight", "S&P 500")
