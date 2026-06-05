#!/bin/bash

# Get the directory where this script is located
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Change to the script's directory
cd "$SCRIPT_DIR" || exit 1

# Get current year and last year
CURRENT_YEAR=$(date +%Y)
LAST_YEAR=$((CURRENT_YEAR - 1))

# Start date is Jan 1 of last year
START_DATE="${LAST_YEAR}-01-01"
# End date is Dec 31 of last year
END_DATE="${LAST_YEAR}-12-31"

echo "Running all fund analyses for ${LAST_YEAR} (${START_DATE} to ${END_DATE})..."
echo "=================================================="

# Find all portfolio files and run them
for portfolio_file in *_portfolio.py; do
    if [ -f "$portfolio_file" ]; then
        fund_name=$(basename "$portfolio_file" _portfolio.py)
        echo "\n🔍 Analyzing $fund_name..."
        
        # Run the portfolio analysis with mode 1 (YTD)
        python3 "$portfolio_file" "$START_DATE" "$END_DATE" 1
        
        if [ $? -eq 0 ]; then
            echo "✅ Successfully analyzed $fund_name"
        else
            echo "❌ Error analyzing $fund_name"
        fi
        
        echo "--------------------------------------------------"
    fi
done

echo "\n🎉 All fund analyses complete!"
