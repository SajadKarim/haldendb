#!/usr/bin/env python3
"""
View Cache Metrics Box Plots PDF
Opens the cache metrics box plots PDF file for viewing.
"""

import os
import subprocess
import sys

def main():
    """Open the cache metrics box plots PDF."""
    script_dir = os.path.dirname(os.path.abspath(__file__))
    pdf_path = os.path.join(script_dir, 'cache_metrics_boxplots.pdf')
    
    if not os.path.exists(pdf_path):
        print(f"❌ PDF file not found: {pdf_path}")
        print("Run cache_metrics_boxplots.py first to generate the PDF.")
        return
    
    print(f"📊 Opening cache metrics box plots PDF...")
    print(f"📁 File: {pdf_path}")
    
    try:
        # Try to open with default PDF viewer
        if sys.platform.startswith('linux'):
            subprocess.run(['xdg-open', pdf_path])
        elif sys.platform.startswith('darwin'):  # macOS
            subprocess.run(['open', pdf_path])
        elif sys.platform.startswith('win'):  # Windows
            os.startfile(pdf_path)
        else:
            print(f"Please open manually: {pdf_path}")
    except Exception as e:
        print(f"Could not open PDF automatically: {e}")
        print(f"Please open manually: {pdf_path}")

if __name__ == "__main__":
    main()