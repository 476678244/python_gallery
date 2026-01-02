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
  - `viking_portfolio.py`: Viking portfolio implementation
  - `three_lines/`: Generated trend charts (PNG)
- `stock/tiger/`: Trading strategies and position management
  - Individual stock analysis (AMD, NVDA, UVXY, etc.)
  - Real-time cash and position tracking

### Example Usage

Run a portfolio analysis from CLI:

```bash
python stock/13f/wcm_portfolio.py 2025-01-01 2025-12-31
python stock/13f/coatue_portfolio.py 2025-01-01 2025-12-31
python stock/13f/viking_portfolio.py 2025-01-01 2025-12-31
```

Trend charts will be saved to:

```text
stock/13f/three_lines/${FUND_NAME}_${start_date}_${end_date}.png
```

Notes:

- **Default cash behavior**: `BasePortfolio.NORMALIZE_WEIGHTS = False` by default. If your `RAW_WEIGHTS` sum to `< 1.0`, the remaining `1 - sum(weights)` is treated as cash.
- **Aggressive mode**: set `NORMALIZE_WEIGHTS = True` in a portfolio class to fully invest (normalize weights to sum to 1).
- **IPO handling**: missing price history (e.g., IPO mid-year) is treated as cash (0 return) before the first available price.

Example output (WCM):

![WCM Trend Example](stock/13f/three_lines/WCM_2025-01-01_2025-12-31.png)

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
