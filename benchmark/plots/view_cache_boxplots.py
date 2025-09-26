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
        
        plt.figure(figsize=(15, 18))
        plt.imshow(img)
        plt.axis('off')
        plt.title('Cache Metrics Box Plots Analysis', fontsize=16, pad=20)
        plt.tight_layout()
        plt.show()
        
        print("Cache metrics box plots displayed!")
        print(f"Plot file: {plot_path}")
        print("\nVisualization shows:")
        print("- 3x2 layout with 6 subplots")
        print("- Top row: Cache Hits and Cache Misses by policy")
        print("- Middle row: Evictions and Dirty Evictions by policy")
        print("- Bottom row: Instructions by policy, User vs System Time by policy")
        print("- X-axis: Cache policies (CLOCK, LRU, SSARC)")
        print("- Box plots show distribution: median, quartiles, outliers")
        print("- Thread Count = 4 data used for all plots")
        
    except ImportError:
        print("matplotlib not available for display")
        print(f"Plot saved at: {plot_path}")
    except Exception as e:
        print(f"Error displaying plot: {e}")
        print(f"Plot saved at: {plot_path}")

if __name__ == "__main__":
    main()