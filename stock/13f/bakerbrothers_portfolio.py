"""
Baker Brothers Advisors portfolio analysis implementation.
"""
from base_portfolio import BasePortfolio

class BakerBrothersPortfolio(BasePortfolio):
    """
    Baker Brothers Advisors portfolio implementation.
    """
    FUND_NAME = "BakerBrothers"

    # Baker Brothers portfolio weights
    RAW_WEIGHTS = {
        "ONC": 0.217,
        "INCY": 0.188,
        "MDGL": 0.071,
        "INSM": 0.070,
        "ACAD": 0.066,
        "SMMT": 0.050,
        "RYTM": 0.041,
        "RVMD": 0.032,
        "CELC": 0.028,
        "KYMR": 0.027,
        "KOD": 0.021,
        "ALKS": 0.018,
        "ABCL": 0.010,
        "EWTX": 0.009,
        "KNSA": 0.008,
        "STOK": 0.008
    }

if __name__ == "__main__":
    # Example usage:
    # python bakerbrothers_portfolio.py
    # Or with custom date range: python bakerbrothers_portfolio.py 2025-01-01 2025-12-31 1
    import sys

    # Default date range: 2025-01-01 to 2025-12-31
    DEFAULT_START_DATE = "2025-01-01"
    DEFAULT_END_DATE = "2025-12-31"

    # Get date range from command line or use defaults
    start_date = sys.argv[1] if len(sys.argv) > 1 else DEFAULT_START_DATE
    end_date = sys.argv[2] if len(sys.argv) > 2 else DEFAULT_END_DATE
    mode = sys.argv[3] if len(sys.argv) > 3 else None

    # Run the analysis
    print(f"Running Baker Brothers portfolio analysis from {start_date} to {end_date}")
    BakerBrothersPortfolio.from_command_line(start_date, end_date, mode)