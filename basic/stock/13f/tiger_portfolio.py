"""
Tiger portfolio analysis implementation.
"""
from base_portfolio import BasePortfolio

class TigerPortfolio(BasePortfolio):
    """
    Tiger portfolio implementation.
    """
    FUND_NAME = "Tiger"
    
    # Tiger portfolio weights (converted from percentages to fractions)
    RAW_WEIGHTS = {
        "MSFT": 0.105,
        "SE": 0.089,
        "GOOGL": 0.08,
        "AMZN": 0.075,
        "NVDA": 0.068,
        "META": 0.064,
        "TTWO": 0.047,
        "APP": 0.045,
        "TSM": 0.04,
        "RDDT": 0.033,
        "AVGO": 0.03,
        "FLUT": 0.029,
        "SPOT": 0.027,
        "APO": 0.026,
        "VEEV": 0.022,
        "GEV": 0.022,
    }

if __name__ == "__main__":
    # Example usage:
    # python tiger_portfolio.py
    # Or with custom date range: python tiger_portfolio.py 2025-01-01 2025-12-31 1
    import sys
    
    # Default date range: 2025-01-01 to 2025-12-31
    DEFAULT_START_DATE = "2025-01-01"
    DEFAULT_END_DATE = "2025-12-31"
    
    # Get date range from command line or use defaults
    start_date = sys.argv[1] if len(sys.argv) > 1 else DEFAULT_START_DATE
    end_date = sys.argv[2] if len(sys.argv) > 2 else DEFAULT_END_DATE
    mode = sys.argv[3] if len(sys.argv) > 3 else None
    
    # Run the analysis
    print(f"Running Tiger portfolio analysis from {start_date} to {end_date}")
    TigerPortfolio.from_command_line(start_date, end_date, mode)