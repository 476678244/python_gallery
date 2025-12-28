"""
Base portfolio class that provides common functionality for all portfolio types.
"""
from datetime import datetime
import pandas as pd
import yfinance as yf
import numpy as np
import matplotlib.pyplot as plt
import re
from pathlib import Path
from matplotlib.ticker import FuncFormatter
import mplfinance as mpf

class BasePortfolio:
    """
    Base class for portfolio analysis. Subclasses should define FUND_NAME and RAW_WEIGHTS.
    """
    FUND_NAME = None  # To be overridden by subclasses
    RAW_WEIGHTS = {}  # To be overridden by subclasses

    def __init__(self):
        if self.FUND_NAME is None or not self.RAW_WEIGHTS:
            raise NotImplementedError("Subclasses must define FUND_NAME and RAW_WEIGHTS")
        self.tickers = list(self.RAW_WEIGHTS.keys())
        self.n = len(self.tickers)

    def get_weights(self, mode=None):
        """
        Get portfolio weights for the specified mode.
        
        Args:
            mode (str, optional): Weighting mode ('fund_name' or 'equal'). 
                                Defaults to the fund's name.
                                
        Returns:
            dict: Dictionary of ticker to weight mappings
        """
        mode = mode or self.FUND_NAME.lower()
        if mode == self.FUND_NAME.lower():
            return self.normalize_weights(self.RAW_WEIGHTS)
        elif mode == "equal":
            return self.equal_weights()
        else:
            raise ValueError(f"weight mode must be '{self.FUND_NAME.lower()}' or 'equal'")

    @staticmethod
    def normalize_weights(weights):
        """Normalize weights to sum to 1."""
        total = sum(weights.values())
        return {k: v / total for k, v in weights.items()}

    def equal_weights(self):
        """Generate equal weights for all tickers."""
        return {ticker: 1.0 / self.n for ticker in self.tickers}

    def download_close_prices(self, tickers, start, end):
        """Download adjusted close prices for the given tickers."""
        data = yf.download(
            tickers,
            start=start,
            end=end,
            group_by="ticker",
            progress=False,
            auto_adjust=False,
        )
        
        # Handle single ticker case
        if len(tickers) == 1:
            ticker = tickers[0]
            if "Adj Close" in data.columns:
                df = data["Adj Close"].to_frame()
            else:
                df = data["Close"].to_frame()
            df.columns = [ticker]
            return df
            
        # Multiple tickers
        swapped = data.swaplevel(axis=1)
        if "Adj Close" in swapped.columns.get_level_values(0):
            return swapped["Adj Close"]
        return swapped["Close"]

    def download_index_close(self, index_ticker, start, end):
        """Download index data."""
        data = yf.download(
            index_ticker,
            start=start,
            end=end,
            progress=False,
            auto_adjust=False,
        )
        if "Adj Close" in data.columns:
            return data["Adj Close"]
        return data["Close"]

    def download_prices(self, start, end):
        """Download prices for all tickers in the portfolio."""
        return self.download_close_prices(self.tickers, start, end)

    def get_sp500(self, start, end):
        """Get S&P 500 index data."""
        return self.download_index_close("^GSPC", start, end)

    def build_portfolio_close(self, prices, weights):
        """Build portfolio returns from prices and weights."""
        returns = prices.pct_change().dropna()
        weighted_returns = returns.mul(weights, axis=1)
        return weighted_returns.sum(axis=1).add(1).cumprod()

    def build_portfolio(self, prices, weight_mode=None):
        """
        Build portfolio with the specified weighting scheme.
        
        Args:
            prices (DataFrame): DataFrame of price data
            weight_mode (str, optional): Weighting mode. Defaults to fund name.
            
        Returns:
            Series: Portfolio cumulative returns
        """
        weight_mode = weight_mode or self.FUND_NAME.lower()
        weights = self.get_weights(weight_mode)
        return self.build_portfolio_close(prices, weights)

    def make_synthetic_ohlc(self, close_series):
        """
        Create synthetic OHLC data from close prices.
        
        Args:
            close_series (Series): Series of close prices
            
        Returns:
            DataFrame: DataFrame with OHLC columns
        """
        df = close_series.to_frame("Close")
        df["Open"] = df["Close"].shift(1)
        df["High"] = df[["Open", "Close"]].max(axis=1)
        df["Low"] = df[["Open", "Close"]].min(axis=1)
        return df.dropna()

    def plot_ytd_candlestick(self, ohlc, title):
        """
        Plot YTD candlestick chart.
        
        Args:
            ohlc (DataFrame): OHLC data
            title (str): Chart title
        """
        # Set style
        mc = mpf.make_marketcolors(
            up='red',
            down='green',
            edge='inherit',
            wick='inherit',
            volume='in'
        )
        
        s = mpf.make_mpf_style(
            marketcolors=mc,
            gridstyle='',
            rc={'font.family': 'Arial'}
        )
        
        fig, axlist = mpf.plot(
            ohlc,
            type='candle',
            title=title,
            style=s,
            volume=False,
            returnfig=True,
            figsize=(12, 6),
            scale_padding=0.3,
            datetime_format='%Y-%m-%d',
            xrotation=0,
        )
        
        # Format y-axis as percentage
        ax = axlist[0]
        ax.yaxis.set_major_formatter(FuncFormatter(lambda y, _: f"{y:.1f}%"))
        
        plt.tight_layout()
        plt.show()

    def plot_three_way_trend(self, p_fund, p_eq, sp500, year_label, start_date=None, end_date=None, **kwargs):
        """
        Plot three-way comparison between fund, equal weight, and S&P 500.
        
        Args:
            p_fund (Series): Fund portfolio returns
            p_eq (Series): Equal weight portfolio returns
            sp500 (Series): S&P 500 returns
            year_label (str): Label for the current year
            **kwargs: Additional arguments to pass to the plot function
        """
        plt.figure(figsize=(12, 6))
        
        # Convert to percentage and rebase to 100
        def rebase(series):
            return (series / series.iloc[0]) * 100
            
        # Plot all series
        plt.plot(rebase(p_fund), label=f"{self.FUND_NAME}-weighted")
        plt.plot(rebase(p_eq), label="Equal-weight")
        plt.plot(rebase(sp500), label="S&P 500", linestyle="--")
        
        # Formatting
        plt.title(f"Portfolio Performance | {year_label}")
        plt.ylabel("Performance (Rebased to 100)")
        plt.legend()
        plt.grid(True, linestyle='--', alpha=0.7)
        
        # Format y-axis as percentage
        ax = plt.gca()
        ax.yaxis.set_major_formatter(FuncFormatter(lambda y, _: f"{y:.0f}%"))
        
        plt.tight_layout()

        if start_date and end_date:
            out_dir = Path(".") / str(self.FUND_NAME)
            out_dir.mkdir(parents=True, exist_ok=True)
            safe_fund = re.sub(r"[^A-Za-z0-9._-]+", "_", str(self.FUND_NAME)).strip("_") or "fund"
            safe_start = re.sub(r"[^A-Za-z0-9._-]+", "_", str(start_date)).strip("_") or "start"
            safe_end = re.sub(r"[^A-Za-z0-9._-]+", "_", str(end_date)).strip("_") or "end"
            out_path = out_dir / f"{safe_fund}_{safe_start}_{safe_end}.png"
            plt.gcf().savefig(out_path, dpi=150, bbox_inches="tight")
        plt.show()

    def run_analysis(self, start_date, end_date):
        """
        Run the portfolio analysis with the given date range.
        
        Args:
            start_date (str): Start date in 'YYYY-MM-DD' format
            end_date (str): End date in 'YYYY-MM-DD' format
        """
        print(f"{self.FUND_NAME} Portfolio Analysis Tool")
        print("1. Fund / Equal-weight / SP500 Trend")
        print("2. Fund Portfolio Candlestick")
        print("3. Equal-weight Portfolio Candlestick")
        print("4. Run All")

        choice = input("Select an option (1-4): ")

        # Download data
        print("Downloading data...")
        prices = self.download_prices(start_date, end_date)
        p_fund = self.build_portfolio(prices, self.FUND_NAME.lower())
        p_eq = self.build_portfolio(prices, "equal")
        sp500 = self.get_sp500(start_date, end_date)

        year_label = f"{start_date.split('-')[0]} YTD"

        # Execute selected analysis
        if choice in {"1", "4"}:
            self.plot_three_way_trend(p_fund, p_eq, sp500, year_label, start_date=start_date, end_date=end_date)

        if choice in {"2", "4"}:
            ohlc = self.make_synthetic_ohlc(p_fund)
            self.plot_ytd_candlestick(ohlc, f"{self.FUND_NAME}-weighted Portfolio | YTD")

        if choice in {"3", "4"}:
            ohlc = self.make_synthetic_ohlc(p_eq)
            self.plot_ytd_candlestick(ohlc, "Equal-weight Portfolio | YTD")

    @classmethod
    def from_command_line(cls, start_date=None, end_date=None):
        """
        Run the analysis from command line with optional date parameters.
        
        Args:
            start_date (str, optional): Start date in 'YYYY-MM-DD' format
            end_date (str, optional): End date in 'YYYY-MM-DD' format
        """
        if start_date is None:
            start_date = input("Enter start date (YYYY-MM-DD): ")
        if end_date is None:
            end_date = datetime.now().strftime("%Y-%m-%d")
            
        portfolio = cls()
        portfolio.run_analysis(start_date, end_date)
