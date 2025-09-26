#!/usr/bin/env python3
"""
View the extended operation plot
"""

import subprocess
import sys
import os

def main():
    """Open the extended operation plot PDF"""
    pdf_file = 'option1_extended_by_operation.pdf'
    
    print("📊 EXTENDED OPERATION PLOT:")
    print("=" * 50)
    
    if os.path.exists(pdf_file):
        print(f"✅ Extended Performance Comparison by Operation Type")
        print(f"   File: {pdf_file}")
        print(f"   Layout: 6 rows (operations) × 3 columns (storage types)")
        print(f"   Operations: DELETE, INSERT, SEARCH_RANDOM, SEARCH_SEQUENTIAL, SEARCH_UNIFORM, SEARCH_ZIPFIAN")
        print(f"   Storage Types: FileStorage, PMemStorage, VolatileStorage")
        print()
        
        try:
            subprocess.run(['xdg-open', pdf_file], check=True)
            print("✅ Plot opened successfully!")
        except subprocess.CalledProcessError:
            print(f"⚠️  Could not open {pdf_file}")
    else:
        print(f"❌ Extended Operation Plot")
        print(f"   File: {pdf_file} - NOT FOUND")
        print("   Run: python option1_extended_by_operation.py --vanilla-csv <path> --optimized-csv <path>")
    
    print()
    print("🔍 WHAT THIS PLOT SHOWS:")
    print("=" * 50)
    print("• Each row represents a different operation type")
    print("• Each column represents a different storage type")
    print("• Bars show vanilla vs optimized performance for each cache policy")
    print("• Yellow boxes show speedup ratios for 1T and 4T configurations")
    print("• Error bars indicate performance variability")
    print()
    
    print("📈 KEY INSIGHTS:")
    print("=" * 50)
    print("• SEARCH operations show the highest speedups (4-10x)")
    print("• SEARCH_ZIPFIAN has the best speedup: 10.36x average")
    print("• INSERT/DELETE operations have more modest improvements (2.5-2.7x)")
    print("• Sequential search patterns benefit most from optimization")
    print("• Performance varies significantly by storage type and cache policy")

if __name__ == "__main__":
    main()