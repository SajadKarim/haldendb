#!/usr/bin/env python3
"""
Simple viewer for the operation comparison box plot
"""

import matplotlib.pyplot as plt
import matplotlib.image as mpimg
import os

def view_operation_comparison():
    """Display the operation comparison box plot"""
    plot_path = "/home/skarim/Code/haldendb_ex/haldendb/benchmark/plots/operation_comparison_boxplot.png"
    
    if not os.path.exists(plot_path):
        print(f"Plot file not found: {plot_path}")
        return
    
    # Load and display image
    img = mpimg.imread(plot_path)
    plt.figure(figsize=(20, 10))
    plt.imshow(img)
    plt.axis('off')
    plt.title("Operation Performance Comparison by Cache Type and Thread Count", 
              fontsize=16, fontweight='bold', pad=20)
    plt.tight_layout()
    plt.show()
    
    print("Operation comparison box plot displayed!")

if __name__ == "__main__":
    view_operation_comparison()