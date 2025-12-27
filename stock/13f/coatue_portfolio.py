"""
COATUE portfolio analysis implementation.
"""
from base_portfolio import BasePortfolio

class CoatuePortfolio(BasePortfolio):
    """
    COATUE portfolio implementation.
    """
    FUND_NAME = "COATUE"
    
    # COATUE portfolio weights
    RAW_WEIGHTS = {
        "META": 0.073,
        "MSFT": 0.059,
        "GOOGL": 0.056,
        "TSM": 0.055,
        "GEV": 0.055,
        "AMZN": 0.047,
        "AVGO": 0.047,
        "CEG": 0.046,
        "NVDA": 0.045,
        "ETN": 0.044,
        "APP": 0.040,
        "RDDT": 0.033,
        "ORCL": 0.033,
        "LRCX": 0.033,
        "SPOT": 0.031,
        "CRWV": 0.023,
    }

if __name__ == "__main__":
    # Example usage:
    # python coatue_portfolio.py
    # Or with custom date range: python coatue_portfolio.py 2025-01-01 2025-12-31
    import sys
    
    # Default date range: 2025-01-01 to 2025-12-31
    DEFAULT_START_DATE = "2025-01-01"
    DEFAULT_END_DATE = "2025-12-31"
    
    # Get date range from command line or use defaults
    start_date = sys.argv[1] if len(sys.argv) > 1 else DEFAULT_START_DATE
    end_date = sys.argv[2] if len(sys.argv) > 2 else DEFAULT_END_DATE
    
    # Run the analysis
    print(f"Running COATUE portfolio analysis from {start_date} to {end_date}")
    CoatuePortfolio.from_command_line(start_date, end_date)
