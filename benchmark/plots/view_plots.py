#!/usr/bin/env python3
"""
Simple plot viewer script
Use this when you have a display available to view the generated plots
"""

import matplotlib.pyplot as plt
import matplotlib.image as mpimg
import os
import glob

def view_plots():
    """Display all generated plots in sequence"""
    plot_dir = "/home/skarim/Code/haldendb_ex/haldendb/benchmark/plots"
    
    # Find all PNG files
    png_files = glob.glob(os.path.join(plot_dir, "*.png"))
    png_files.sort()
    
    if not png_files:
        print("No PNG files found in the plots directory")
        return
    
    print(f"Found {len(png_files)} plots to display")
    print("Close each plot window to view the next one")
    
    for i, png_file in enumerate(png_files):
        filename = os.path.basename(png_file)
        print(f"\nDisplaying plot {i+1}/{len(png_files)}: {filename}")
        
        # Load and display image
        img = mpimg.imread(png_file)
        plt.figure(figsize=(16, 12))
        plt.imshow(img)
        plt.axis('off')
        plt.title(filename, fontsize=16, fontweight='bold', pad=20)
        plt.tight_layout()
        plt.show()
    
    print("\nAll plots displayed!")

if __name__ == "__main__":
    view_plots()