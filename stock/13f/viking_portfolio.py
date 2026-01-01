"""
Viking portfolio analysis implementation.
"""
from base_portfolio import BasePortfolio


class VikingPortfolio(BasePortfolio):
    """
    Viking portfolio implementation.
    """

    FUND_NAME = "Viking"

    # Viking portfolio weights
    RAW_WEIGHTS = {
        "PNC": 4.1,
        "JPM": 4.1,
        "SCHW": 4.1,
        "COF": 4.1,
        "MSFT": 3.3,
        "DIS": 3.1,
        "TSM": 2.9,
        "BBIO": 2.7,
        "MCD": 2.7,
        "FTV": 2.6,
        "APD": 2.6,
        "SHW": 2.6,
        "V": 2.6,
        "GM": 2.1,
        "CVNA": 2.1,
        "TMUS": 2.0,
    }


if __name__ == "__main__":
    # Example usage:
    # python viking_portfolio.py
    # Or with custom date range: python viking_portfolio.py 2025-01-01 2025-12-31
    import sys

    # Default date range: 2025-01-01 to 2025-12-31
    DEFAULT_START_DATE = "2025-01-01"
    DEFAULT_END_DATE = "2025-12-31"

    # Get date range from command line or use defaults
    start_date = sys.argv[1] if len(sys.argv) > 1 else DEFAULT_START_DATE
    end_date = sys.argv[2] if len(sys.argv) > 2 else DEFAULT_END_DATE

    # Run the analysis
    print(f"Running Viking portfolio analysis from {start_date} to {end_date}")
    VikingPortfolio.from_command_line(start_date, end_date)