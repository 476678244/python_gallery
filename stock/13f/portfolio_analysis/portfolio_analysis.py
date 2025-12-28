import yfinance as yf
import pandas as pd
import mplfinance as mpf
import matplotlib.pyplot as plt
import re
from pathlib import Path

"""
Reusable portfolio analytics utilities.
No strategy- or year-specific assumptions.
"""

def normalize_weights(weights: dict[str, float]) -> dict[str, float]:
    total = float(sum(weights.values()))
    if total <= 0:
        raise ValueError("weights must sum to a positive number")
    return {k: float(v) / total for k, v in weights.items()}


def equal_weights(tickers: list[str]) -> dict[str, float]:
    if not tickers:
        raise ValueError("tickers must not be empty")
    w = 1.0 / len(tickers)
    return {t: w for t in tickers}


def download_close_prices(tickers: list[str], start: str, end: str) -> pd.DataFrame:
    prices = yf.download(
        tickers,
        start=start,
        end=end,
        auto_adjust=True,
        progress=False,
    )["Close"]

    if isinstance(prices, pd.Series):
        prices = prices.to_frame()

    return prices.dropna(how="any")


def download_index_close(symbol: str, start: str, end: str) -> pd.Series:
    idx = yf.download(
        symbol,
        start=start,
        end=end,
        auto_adjust=True,
        progress=False,
    )["Close"]

    return idx.dropna()


def build_portfolio_close(prices: pd.DataFrame, weights: dict[str, float]) -> pd.DataFrame:
    weights = normalize_weights(weights)
    tickers = list(weights.keys())

    missing = [t for t in tickers if t not in prices.columns]
    if missing:
        raise ValueError(f"prices missing columns for tickers: {missing}")

    normalized = prices[tickers] / prices[tickers].iloc[0]
    close = sum(weights[t] * normalized[t] for t in tickers)
    return pd.DataFrame({"Close": close})


def make_synthetic_ohlc(close_df: pd.DataFrame) -> pd.DataFrame:
    ohlc = pd.DataFrame(index=close_df.index)
    ohlc["Close"] = close_df["Close"]
    ohlc["Open"] = close_df["Close"].shift(1)
    ohlc["High"] = close_df["Close"].rolling(2).max()
    ohlc["Low"] = close_df["Close"].rolling(2).min()
    return ohlc.dropna()


def plot_three_way_trend(
    portfolio_a: pd.DataFrame,
    portfolio_b: pd.DataFrame,
    benchmark_close: pd.Series,
    year_label: str,
    label_a: str = "Portfolio A",
    label_b: str = "Portfolio B",
    benchmark_label: str = "Benchmark",
    fund_name: str | None = None,
    start_date: str | None = None,
    end_date: str | None = None,
) -> None:
    df = pd.concat([portfolio_a["Close"], portfolio_b["Close"], benchmark_close], axis=1).dropna()
    df.columns = [label_a, label_b, benchmark_label]
    df = df / df.iloc[0]

    plt.figure(figsize=(14, 7))
    plt.plot(df.index, df[label_a], label=label_a)
    plt.plot(df.index, df[label_b], label=label_b)
    plt.plot(df.index, df[benchmark_label], label=benchmark_label)

    plt.yscale("log")
    plt.title(f"{year_label} Trend | {label_a} vs {label_b} vs {benchmark_label}")
    plt.ylabel("Normalized Value (Log)")
    plt.grid(True, which="both", linestyle="--", alpha=0.4)
    plt.legend()

    if fund_name:
        out_dir = Path(".") / "three_lines"
        out_dir.mkdir(parents=True, exist_ok=True)

        if start_date and end_date:
            safe_fund = re.sub(r"[^A-Za-z0-9._-]+", "_", str(fund_name)).strip("_") or "fund"
            safe_start = re.sub(r"[^A-Za-z0-9._-]+", "_", str(start_date)).strip("_") or "start"
            safe_end = re.sub(r"[^A-Za-z0-9._-]+", "_", str(end_date)).strip("_") or "end"
            out_path = out_dir / f"{safe_fund}_{safe_start}_{safe_end}.png"
        else:
            safe_year = re.sub(r"[^A-Za-z0-9._-]+", "_", str(year_label)).strip("_") or "trend"
            safe_a = re.sub(r"[^A-Za-z0-9._-]+", "_", str(label_a)).strip("_") or "a"
            safe_b = re.sub(r"[^A-Za-z0-9._-]+", "_", str(label_b)).strip("_") or "b"
            safe_bm = re.sub(r"[^A-Za-z0-9._-]+", "_", str(benchmark_label)).strip("_") or "benchmark"
            out_path = out_dir / f"{safe_year}__{safe_a}__{safe_b}__{safe_bm}.png"

        plt.tight_layout()
        plt.gcf().savefig(out_path, dpi=150, bbox_inches="tight")
    plt.show()


def plot_ytd_candlestick(ohlc: pd.DataFrame, title: str) -> None:
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
