"""
Madison Asset Management portfolio implementation.
"""
from base_portfolio import BasePortfolio


class MadisonPortfolio(BasePortfolio):
    """
    Madison Asset Management portfolio implementation.
    """
    FUND_NAME = "Madison Asset Management"

    # Madison portfolio weights (converted from percentages to decimals)
    RAW_WEIGHTS = {
        "ACGL": 0.047,
        "APH": 0.033,
        "ROST": 0.027,
        "PCAR": 0.027,
        "CDW": 0.023,
        "GOOG": 0.023,
        "CPRT": 0.022,
        "BRO": 0.021,
        "IT": 0.021,
        "CSL": 0.019,
        "AMZN": 0.018,
        "LH": 0.018,
        "MEDP": 0.017,
        "WRB": 0.016,
        "TXN": 0.015,
        "TDY": 0.014
    }


if __name__ == "__main__":
    # Example usage:
    # python madison_portfolio.py
    # Or with custom date range: python madison_portfolio.py 2025-01-01 2025-12-31 1
    import sys

    # Default date range: 2025-01-01 to 2025-12-31
    DEFAULT_START_DATE = "2025-01-01"
    DEFAULT_END_DATE = "2025-12-31"

    # Get date range from command line or use defaults
    start_date = sys.argv[1] if len(sys.argv) > 1 else DEFAULT_START_DATE
    end_date = sys.argv[2] if len(sys.argv) > 2 else DEFAULT_END_DATE
    mode = sys.argv[3] if len(sys.argv) > 3 else None

    # Run the analysis
    print(f"Running Madison Asset Management portfolio analysis from {start_date} to {end_date}")
    MadisonPortfolio.from_command_line(start_date, end_date, mode)