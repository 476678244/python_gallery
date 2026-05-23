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
        "PNC": 0.041,
        "JPM": 0.041,
        "SCHW": 0.041,
        "COF": 0.041,
        "MSFT": 0.033,
        "DIS": 0.031,
        "TSM": 0.029,
        "BBIO": 0.027,
        "MCD": 0.027,
        "FTV": 0.026,
        "APD": 0.026,
        "SHW": 0.026,
        "V": 0.026,
        "GM": 0.021,
        "CVNA": 0.021,
        "TMUS": 0.020,
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
    mode = sys.argv[3] if len(sys.argv) > 3 else None

    # Run the analysis
    print(f"Running Viking portfolio analysis from {start_date} to {end_date}")
    VikingPortfolio.from_command_line(start_date, end_date, mode)