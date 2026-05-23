"""
Akre Capital Management portfolio analysis implementation.
"""
from base_portfolio import BasePortfolio


class AkrePortfolio(BasePortfolio):
    """
    Akre Capital Management portfolio implementation.
    """
    FUND_NAME = "Akre"

    # Akre portfolio weights (converted from percentages to decimals)
    RAW_WEIGHTS = {
        "MA": 0.179,
        "BN": 0.131,
        "KKR": 0.113,
        "V": 0.101,
        "MCO": 0.101,
        "ORLY": 0.093,
        "CSGP": 0.078,
        "ROP": 0.058,
        "ABNB": 0.042,
        "FICO": 0.039,
        "CPRT": 0.019,
        "DHR": 0.017,
        "CCC": 0.015,
        "AMT": 0.009,
        "GSHD": 0.003,
        "SOPH": 0.002
    }


if __name__ == "__main__":
    # Example usage:
    # python akre_portfolio.py
    # Or with custom date range: python akre_portfolio.py 2025-01-01 2025-12-31 1
    import sys

    # Default date range: 2025-01-01 to 2025-12-31
    DEFAULT_START_DATE = "2025-01-01"
    DEFAULT_END_DATE = "2025-12-31"

    # Get date range from command line or use defaults
    start_date = sys.argv[1] if len(sys.argv) > 1 else DEFAULT_START_DATE
    end_date = sys.argv[2] if len(sys.argv) > 2 else DEFAULT_END_DATE
    mode = sys.argv[3] if len(sys.argv) > 3 else None

    # Run the analysis
    print(f"Running Akre portfolio analysis from {start_date} to {end_date}")
    AkrePortfolio.from_command_line(start_date, end_date, mode)
