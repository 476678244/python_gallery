"""
ARK Invest portfolio analysis implementation.
"""
from base_portfolio import BasePortfolio

class ArkPortfolio(BasePortfolio):
    """
    ARK Invest portfolio implementation.
    """
    FUND_NAME = "ARK"

    # ARK portfolio weights
    RAW_WEIGHTS = {
        "TSLA": 0.095,
        "COIN": 0.048,
        "ROKU": 0.044,
        "PLTR": 0.044,
        "RBLX": 0.044,
        "HOOD": 0.043,
        "SHOP": 0.043,
        "CRSP": 0.038,
        "TEM": 0.035,
        "AMD": 0.029,
        "CRCL": 0.023,
        "BMNRD": 0.023,
        "TER": 0.022,
        "KTOS": 0.020,
        "ACHR": 0.018,
        "BEAM": 0.016
    }

if __name__ == "__main__":
    # Example usage:
    # python ark_portfolio.py
    # Or with custom date range: python ark_portfolio.py 2025-01-01 2025-12-31 1
    import sys

    # Default date range: 2025-01-01 to 2025-12-31
    DEFAULT_START_DATE = "2025-01-01"
    DEFAULT_END_DATE = "2025-12-31"

    # Get date range from command line or use defaults
    start_date = sys.argv[1] if len(sys.argv) > 1 else DEFAULT_START_DATE
    end_date = sys.argv[2] if len(sys.argv) > 2 else DEFAULT_END_DATE
    mode = sys.argv[3] if len(sys.argv) > 3 else None

    # Run the analysis
    print(f"Running ARK portfolio analysis from {start_date} to {end_date}")
    ArkPortfolio.from_command_line(start_date, end_date, mode)