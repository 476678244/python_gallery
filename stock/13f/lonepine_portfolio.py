"""
LonePine Capital portfolio implementation.
"""
from base_portfolio import BasePortfolio

class LonePinePortfolio(BasePortfolio):
    """
    LonePine Capital portfolio implementation.
    """
    FUND_NAME = "LonePine Capital"
    RAW_WEIGHTS = {
        "META": 0.070,
        "VST": 0.067,
        "TSM": 0.062,
        "APP": 0.058,
        "LPLA": 0.054,
        "PM": 0.054,
        "BN": 0.051,
        "CVNA": 0.048,
        "MSFT": 0.045,
        "AMZN": 0.045,
        "COF": 0.040,
        "KKR": 0.038,
        "AVGO": 0.037,
        "TLN": 0.037,
        "SBUX": 0.034,
        "EQT": 0.033
    }

if __name__ == "__main__":
    # Example usage:
    # python lonepine_portfolio.py
    # Or with custom date range: python lonepine_portfolio.py 2025-01-01 2025-12-31 1
    import sys

    # Default date range: 2025-01-01 to 2025-12-31
    DEFAULT_START_DATE = "2025-01-01"
    DEFAULT_END_DATE = "2025-12-31"

    # Get date range from command line or use defaults
    start_date = sys.argv[1] if len(sys.argv) > 1 else DEFAULT_START_DATE
    end_date = sys.argv[2] if len(sys.argv) > 2 else DEFAULT_END_DATE
    mode = sys.argv[3] if len(sys.argv) > 3 else None

    # Run the analysis
    print(f"Running LonePine Capital portfolio analysis from {start_date} to {end_date}")
    LonePinePortfolio.from_command_line(start_date, end_date, mode)