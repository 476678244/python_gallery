"""
Fundsmith portfolio analysis implementation.
"""
from base_portfolio import BasePortfolio


class FundsmithPortfolio(BasePortfolio):
    """
    Fundsmith portfolio implementation.
    """
    FUND_NAME = "Fundsmith"

    # Fundsmith portfolio weights
    RAW_WEIGHTS = {
        "SYK": 0.086,   # Stryker
        "IDXX": 0.084,  # IDEXX Laboratories
        "GOOGL": 0.077, # Alphabet
        "MSFT": 0.068,  # Microsoft
        "V": 0.067,     # Visa
        "ADP": 0.064,   # Automatic Data Processing
        "WAT": 0.060,   # Waters Corporation
        "PM": 0.059,    # Philip Morris International
        "META": 0.058,  # Meta Platforms
        "MAR": 0.056,   # Marriott International
        "MTD": 0.037,   # Mettler-Toledo
        "FTNT": 0.036,  # Fortinet
        "PG": 0.036,    # Procter & Gamble
        "CHD": 0.030,   # Church & Dwight
        "OTIS": 0.027,  # Otis Worldwide
        "ZTS": 0.027    # Zoetis
    }


if __name__ == "__main__":
    # Example usage:
    # python fundsmith_portfolio.py
    # Or with custom date range: python fundsmith_portfolio.py 2025-01-01 2025-12-31
    import sys

    # Default date range: 2025-01-01 to 2025-12-31
    DEFAULT_START_DATE = "2025-01-01"
    DEFAULT_END_DATE = "2025-12-31"

    # Get date range from command line or use defaults
    start_date = sys.argv[1] if len(sys.argv) > 1 else DEFAULT_START_DATE
    end_date = sys.argv[2] if len(sys.argv) > 2 else DEFAULT_END_DATE
    mode = sys.argv[3] if len(sys.argv) > 3 else None

    # Run the analysis
    print(f"Running Fundsmith portfolio analysis from {start_date} to {end_date}")
    FundsmithPortfolio.from_command_line(start_date, end_date, mode)