#!/usr/bin/env python3
"""
Simple viewer for the cumulative cache metrics heatmap.
"""

import os
import sys

def main():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    plot_path = os.path.join(script_dir, 'cache_metrics_stacked_bars.png')
    
    if not os.path.exists(plot_path):
        print(f"Plot not found: {plot_path}")
        print("Run cache_metrics_stacked_bars.py first to generate the plot.")
        return
    
    try:
        import matplotlib.pyplot as plt
        import matplotlib.image as mpimg
        
        # Load and display the image
        img = mpimg.imread(plot_path)
        
        plt.figure(figsize=(12, 6))
        plt.imshow(img)
        plt.axis('off')
        plt.title('Cumulative Cache Metrics Heatmap', fontsize=16, pad=20)
        plt.tight_layout()
        plt.show()
        
        print("Cumulative cache metrics heatmap displayed!")
        print(f"Plot file: {plot_path}")
        print("\nVisualization shows:")
        print("- Two heatmaps: Thread Count 1 vs Thread Count 4")
        print("- X-axis: Cache metrics (Hits, Misses, Evictions, Dirty Evictions)")
        print("- Y-axis: Cache types (CLOCK, LRU, SSARC)")
        print("- Color coding: White = Best performance, Green = Worst performance")
        print("- Numbers: Actual cumulative values (averaged across runs)")
        print("- Each metric column uses independent scaling with proper best/worst logic")
        
    except ImportError:
        print("matplotlib not available for display")
        print(f"Plot saved at: {plot_path}")
    except Exception as e:
        print(f"Error displaying plot: {e}")
        print(f"Plot saved at: {plot_path}")

if __name__ == "__main__":
    main()