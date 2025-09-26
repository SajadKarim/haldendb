#!/usr/bin/env python3
"""
Simple viewer for the thread comparison box plot PDF.
"""

import os
import sys

def main():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    plot_path = os.path.join(script_dir, 'thread_comparison_boxplot.pdf')
    
    if not os.path.exists(plot_path):
        print(f"Plot not found: {plot_path}")
        print("Run thread_comparison_boxplot.py first to generate the plot.")
        return
    
    print("Thread comparison box plot PDF generated!")
    print(f"Plot file: {plot_path}")
    print("\nVisualization shows:")
    print("- Two subplots comparing Thread Count = 1 vs Thread Count = 4")
    print("- X-axis: Cache policy names (CLOCK, LRU, A2Q)")
    print("- Y-axis: Throughput (Operations per Second)")
    print("- Box plots show: Median, Q1, Q3, whiskers, outliers, and means")
    print("- Color coding: Blue (CLOCK), Purple (LRU), Orange (A2Q)")
    print("- Legend: Located in top right of second subplot")
    print("- Format: PDF for high-quality printing and publication")
    
    # Try to open with system default PDF viewer
    try:
        if os.name == 'nt':  # Windows
            os.startfile(plot_path)
        elif os.name == 'posix':  # macOS and Linux
            os.system(f'xdg-open "{plot_path}"')
        print(f"\nOpening PDF with system default viewer...")
    except Exception as e:
        print(f"\nCould not open PDF automatically: {e}")
        print(f"Please open manually: {plot_path}")

if __name__ == "__main__":
    main()