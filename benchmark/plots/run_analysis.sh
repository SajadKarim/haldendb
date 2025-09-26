#!/bin/bash

# Cache Benchmark Analysis Runner Script
# This script installs dependencies and generates all plots

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "Cache Benchmark Analysis Runner"
echo "==============================="

# Check if Python 3 is available
if ! command -v python3 &> /dev/null; then
    echo "Error: Python 3 is not installed"
    exit 1
fi

# Check if pip is available
if ! command -v pip3 &> /dev/null; then
    echo "Error: pip3 is not installed"
    exit 1
fi

echo "Installing Python dependencies..."
pip3 install -r requirements.txt --user

echo ""
echo "Running analysis and generating plots..."
python3 generate_all_plots.py

echo ""
echo "Analysis complete! Check the plots folder for generated visualizations."
echo "Generated files:"
ls -la *.png *.txt 2>/dev/null || echo "No files generated - check for errors above"