# Python Gallery

A collection of Python utilities and examples for stock analysis and music file management.

## 📈 Stock Analysis

### Features

- **Portfolio Tracking**: Monitor and analyze investment portfolios with support for multiple funds (WCM, Coatue, etc.)
- **Performance Visualization**: Generate performance charts and comparisons against benchmarks
- **Data Integration**: Fetch real-time and historical stock data using yfinance and efinance
- **Position Analysis**: Calculate position sizes, weights, and performance metrics

### Key Components

- `stock/13f/`: 13F portfolio analysis tools for institutional investors
  - `base_portfolio.py`: Core portfolio analysis functionality
  - `wcm_portfolio.py`: WCM Investment Management portfolio implementation
  - `coatue_portfolio.py`: Coatue Management portfolio implementation
- `stock/tiger/`: Trading strategies and position management
  - Individual stock analysis (AMD, NVDA, UVXY, etc.)
  - Real-time cash and position tracking

### Example Usage

```python
# Analyze WCM portfolio performance
from stock.wcm_portfolio import WCMPortfolio

portfolio = WCMPortfolio()
performance = portfolio.analyze_performance()
portfolio.plot_performance()
```

## 🎵 Music Management

### Features

- **FLAC File Organization**: Clean and organize FLAC music files
- **Tag Deduplication**: Remove duplicate tags from audio files
- **Metadata Normalization**: Standardize music metadata for better library management

### Key Components

- `music/normalize_flac_by_dedup_tags.py`: Main script for processing FLAC files
- Shell scripts for batch processing in `music/sh/`

### Example Usage

```bash
# Normalize FLAC files in a directory
python music/normalize_flac_by_dedup_tags.py /path/to/music
```

## 🚀 Getting Started

1. Clone the repository
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. For music processing, install required system tools:
   ```bash
   # On macOS
   brew install flac
   ```

## 📦 Dependencies

- Core: Python 3.11+
- See `requirements.txt` for Python package dependencies

## 🤝 Contributing

Feel free to submit issues and enhancement requests or contribute code via pull requests.
