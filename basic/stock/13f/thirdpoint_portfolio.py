"""
ThirdPoint Capital portfolio definition.
"""

from base_portfolio import BasePortfolio


class ThirdPointPortfolio(BasePortfolio):
    """ThirdPoint Capital multi-stock portfolio."""

    FUND_NAME = "ThirdPoint"
    NORMALIZE_WEIGHTS = False

    RAW_WEIGHTS = {
        "PCG": 0.084,
        "AMZN": 0.069,
        "PUT_SPY": 0.065,
        "MSFT": 0.063,
        "NVDA": 0.059,
        "NSC": 0.055,
        "BN": 0.036,
        "TSM": 0.034,
        "COF": 0.033,
        "FLUT": 0.032,
        "CASY": 0.031,
        "TDS": 0.029,
        "CRH": 0.029,
        "CSGP": 0.028,
        "SGI": 0.028,
        "LYV": 0.025,
    }


if __name__ == "__main__":
    # Default date range: 2025-01-01 to 2025-12-31
    import sys

    DEFAULT_START_DATE = "2025-01-01"
    DEFAULT_END_DATE = "2025-12-31"

    start_date = sys.argv[1] if len(sys.argv) > 1 else DEFAULT_START_DATE
    end_date = sys.argv[2] if len(sys.argv) > 2 else DEFAULT_END_DATE
    mode = sys.argv[3] if len(sys.argv) > 3 else None

    print(f"Running ThirdPoint portfolio analysis from {start_date} to {end_date}")
    ThirdPointPortfolio.from_command_line(start_date, end_date, mode)
