#!/usr/bin/env python3
"""
Simple viewer for the cache metrics box plots.
"""

import os
import sys

def main():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    plot_path = os.path.join(script_dir, 'cache_metrics_boxplots.png')
    
    if not os.path.exists(plot_path):
        print(f"Plot not found: {plot_path}")
        print("Run cache_metrics_boxplots.py first to generate the plot.")
        return
    
    try:
        import matplotlib.pyplot as plt
        import matplotlib.image as mpimg
        
        # Load and display the image
        img = mpimg.imread(plot_path)
        
        plt.figure(figsize=(18, 12))
        plt.imshow(img)
        plt.axis('off')
        plt.title('Cache Metrics Box Plots - 2x3 Layout', fontsize=16, pad=20)
        plt.tight_layout()
        plt.show()
        
        print("Cache metrics box plots displayed!")
        print(f"Plot file: {plot_path}")
        print("\nVisualization shows:")
        print("- 2x3 layout with 6 subplots")
        print("- Top row: Cache Hits, Cache Misses, Evictions")
        print("- Bottom row: Dirty Evictions, Instructions, User vs System Time")
        print("- X-axis: Cache policies (CLOCK, LRU, SSARC)")
        print("- Box plots show: Median, Q1, Q3, whiskers, and outliers")
        print("- Color coding: Blue (CLOCK), Orange (LRU), Green (SSARC)")
        print("- Data filtered for thread_count = 4")
        
    except ImportError:
        print("matplotlib not available for display")
        print(f"Plot saved at: {plot_path}")
    except Exception as e:
        print(f"Error displaying plot: {e}")
        print(f"Plot saved at: {plot_path}")

if __name__ == "__main__":
    main()