#!/usr/bin/env python3
"""
View all three visualization options
"""

import subprocess
import sys
import os

def main():
    """Open all three PDF files"""
    pdf_files = [
        'option1_overlay_comparison.pdf',
        'option2_speedup_ratio.pdf', 
        'option3_before_after.pdf'
    ]
    
    print("Opening all three visualization options:")
    for i, pdf_file in enumerate(pdf_files, 1):
        if os.path.exists(pdf_file):
            print(f"Option {i}: {pdf_file}")
            try:
                subprocess.run(['xdg-open', pdf_file], check=True)
            except subprocess.CalledProcessError:
                print(f"  Could not open {pdf_file}")
        else:
            print(f"Option {i}: {pdf_file} - FILE NOT FOUND")
    
    print("\nVisualization Options Summary:")
    print("Option 1: Overlay Comparison - Shows vanilla vs optimized with grouped bars and speedup annotations")
    print("Option 2: Speedup Ratio Plot - Shows how many times faster optimized is compared to vanilla")
    print("Option 3: Before/After Comparison - Shows vanilla (before) and optimized (after) side by side")

if __name__ == "__main__":
    main()