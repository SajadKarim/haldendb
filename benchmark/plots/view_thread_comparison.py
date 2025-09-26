#!/usr/bin/env python3
"""
Simple viewer for the thread comparison box plot
"""

import matplotlib.pyplot as plt
import matplotlib.image as mpimg
import os

def view_thread_comparison():
    """Display the thread comparison box plot"""
    plot_path = "/home/skarim/Code/haldendb_ex/haldendb/benchmark/plots/thread_comparison_boxplot.png"
    
    if not os.path.exists(plot_path):
        print(f"Plot file not found: {plot_path}")
        return
    
    # Load and display image
    img = mpimg.imread(plot_path)
    plt.figure(figsize=(16, 8))
    plt.imshow(img)
    plt.axis('off')
    plt.title("Cache Policy Performance Comparison by Thread Count", 
              fontsize=16, fontweight='bold', pad=20)
    plt.tight_layout()
    plt.show()
    
    print("Thread comparison box plot displayed!")

if __name__ == "__main__":
    view_thread_comparison()