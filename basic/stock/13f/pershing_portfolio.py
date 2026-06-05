"""
Pershing portfolio analysis implementation.
"""
from base_portfolio import BasePortfolio

class PershingPortfolio(BasePortfolio):
    """
    Pershing portfolio implementation.
    """
    FUND_NAME = "Pershing"

    # Pershing portfolio weights
    RAW_WEIGHTS = {
        "UBER": 0.203,
        "BN":   0.192,
        "GOOG": 0.186,
        "HHH":  0.106,
        "QSR":  0.100,
        "AMZN": 0.087,
        "CMG":  0.058,
        "HLT":  0.054,
        "SEG":  0.008,
        "HTZ":  0.006
    }

if __name__ == "__main__":
    # Example usage:
    # python pershing_portfolio.py
    # Or with custom date range: python pershing_portfolio.py 2025-01-01 2025-12-31 1
    import sys

    # Default date range: 2025-01-01 to 2025-12-31
    DEFAULT_START_DATE = "2025-01-01"
    DEFAULT_END_DATE = "2025-12-31"

    # Get date range from command line or use defaults
    start_date = sys.argv[1] if len(sys.argv) > 1 else DEFAULT_START_DATE
    end_date = sys.argv[2] if len(sys.argv) > 2 else DEFAULT_END_DATE
    mode = sys.argv[3] if len(sys.argv) > 3 else None

    # Run the analysis
    print(f"Running Pershing portfolio analysis from {start_date} to {end_date}")
    PershingPortfolio.from_command_line(start_date, end_date, mode)
