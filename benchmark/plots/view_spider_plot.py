#!/usr/bin/env python3
"""
Simple viewer for the operation spider plot.
"""

import os
import sys

def main():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    plot_path = os.path.join(script_dir, 'operation_spider_plot.png')
    
    if not os.path.exists(plot_path):
        print(f"Plot not found: {plot_path}")
        print("Run operation_spider_plot.py first to generate the plot.")
        return
    
    try:
        import matplotlib.pyplot as plt
        import matplotlib.image as mpimg
        
        # Load and display the image
        img = mpimg.imread(plot_path)
        
        plt.figure(figsize=(16, 8))
        plt.imshow(img)
        plt.axis('off')
        plt.title('Cache Performance Spider Plot - Operations Comparison', fontsize=16, pad=20)
        plt.tight_layout()
        plt.show()
        
    except ImportError:
        print("matplotlib not available for display")
        print(f"Plot saved at: {plot_path}")
    except Exception as e:
        print(f"Error displaying plot: {e}")
        print(f"Plot saved at: {plot_path}")

if __name__ == "__main__":
    main()