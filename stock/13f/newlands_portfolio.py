"""
Newlands portfolio analysis implementation.
"""
from base_portfolio import BasePortfolio

class NewlandsPortfolio(BasePortfolio):
    """
    Newlands portfolio implementation.
    """
    FUND_NAME = "Newlands"
    
    # Newlands portfolio weights
    RAW_WEIGHTS = {
        "META": 0.3456,
        "HOOD": 0.1641,
        "DASH": 0.0912,
        "TSLA": 0.0794,
        "GOOGL": 0.0726,
        "AMZN": 0.0686,
        "SHOP": 0.0446,
        "NFLX": 0.0381,
        "MSFT": 0.0258,
        "JD": 0.0194,
        "WDAY": 0.0156,
        "SCHW": 0.0145,
        "DOCU": 0.0141,
        "AAPL": 0.0030,
        "BABA": 0.0023,
        "FRSH": 0.0003
    }

if __name__ == "__main__":
    # Example usage:
    # python newlands_portfolio.py
    # Or with custom date range: python newlands_portfolio.py 2025-01-01 2025-12-31
    import sys
    
    # Default date range: 2025-01-01 to 2025-12-31
    DEFAULT_START_DATE = "2025-01-01"
    DEFAULT_END_DATE = "2025-12-31"
    
    # Get date range from command line or use defaults
    start_date = sys.argv[1] if len(sys.argv) > 1 else DEFAULT_START_DATE
    end_date = sys.argv[2] if len(sys.argv) > 2 else DEFAULT_END_DATE
    mode = sys.argv[3] if len(sys.argv) > 3 else None
    
    # Run the analysis
    print(f"Running Newlands portfolio analysis from {start_date} to {end_date}")
    NewlandsPortfolio.from_command_line(start_date, end_date, mode)