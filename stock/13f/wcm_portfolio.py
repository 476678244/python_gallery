"""
WCM portfolio analysis implementation.
"""
from base_portfolio import BasePortfolio

class WCMPortfolio(BasePortfolio):
    """
    WCM portfolio implementation.
    """
    FUND_NAME = "WCM"
    
    # WCM portfolio weights
    RAW_WEIGHTS = {
        "SE": 0.098,
        "APP": 0.073,
        "TSM": 0.057,
        "SPOT": 0.051,
        "ASML": 0.039,
        "PM": 0.038,
        "IBN": 0.034,
        "LIN": 0.034,
        "CPNG": 0.033,
        "AMZN": 0.029,
        "MELI": 0.026,
    }

if __name__ == "__main__":
    # Example usage:
    # python wcm_portfolio.py
    # Or with custom date range: python wcm_portfolio.py 2025-01-01 2025-12-31
    import sys
    
    # Default date range: 2025-01-01 to 2025-12-31
    DEFAULT_START_DATE = "2025-01-01"
    DEFAULT_END_DATE = "2025-12-31"
    
    # Get date range from command line or use defaults
    start_date = sys.argv[1] if len(sys.argv) > 1 else DEFAULT_START_DATE
    end_date = sys.argv[2] if len(sys.argv) > 2 else DEFAULT_END_DATE
    
    # Run the analysis
    print(f"Running WCM portfolio analysis from {start_date} to {end_date}")
    WCMPortfolio.from_command_line(start_date, end_date)
