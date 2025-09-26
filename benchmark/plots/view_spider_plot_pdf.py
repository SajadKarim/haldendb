#!/usr/bin/env python3
"""
View the operation spider plot PDF
"""

import os
import subprocess
import sys

def view_spider_plot_pdf():
    """View the generated spider plot PDF"""
    
    script_dir = os.path.dirname(os.path.abspath(__file__))
    pdf_path = os.path.join(script_dir, 'operation_spider_plot.pdf')
    
    if not os.path.exists(pdf_path):
        print(f"❌ PDF file not found: {pdf_path}")
        print("Run 'python operation_spider_plot.py' first to generate the plot.")
        return
    
    print("Operation spider plot PDF generated!")
    print(f"Plot file: {pdf_path}")
    print()
    print("Visualization shows:")
    print("- Two spider/radar plots comparing Thread Count = 1 vs Thread Count = 4")
    print("- Radial axes: Different operations (delete, insert, search_random, etc.)")
    print("- Radial scale: Operations per second (throughput)")
    print("- Three cache policies: CLOCK (blue), LRU (purple), A2Q (orange)")
    print("- Spider web shows performance 'fingerprint' of each cache algorithm")
    print("- Legend: Located in top right of second subplot")
    print("- Format: PDF for high-quality printing and publication")
    print("- No main title for cleaner appearance")
    
    # Try to open the PDF
    try:
        if sys.platform.startswith('linux'):
            # Try xdg-open first (most Linux distributions)
            try:
                subprocess.run(['xdg-open', pdf_path], check=True)
            except (subprocess.CalledProcessError, FileNotFoundError):
                print("Error: no \"view\" mailcap rules found for type \"application/pdf\"")
                print()
                print("Opening PDF with system default viewer...")
                # Try other common PDF viewers
                viewers = ['evince', 'okular', 'firefox', 'chromium-browser', 'google-chrome']
                opened = False
                for viewer in viewers:
                    try:
                        subprocess.run([viewer, pdf_path], check=True)
                        opened = True
                        break
                    except (subprocess.CalledProcessError, FileNotFoundError):
                        continue
                
                if not opened:
                    print(f"Could not find a suitable PDF viewer. Please open manually: {pdf_path}")
        
        elif sys.platform == 'darwin':  # macOS
            subprocess.run(['open', pdf_path], check=True)
        
        elif sys.platform == 'win32':  # Windows
            os.startfile(pdf_path)
        
        else:
            print(f"Unsupported platform: {sys.platform}")
            print(f"Please open the PDF manually: {pdf_path}")
    
    except Exception as e:
        print(f"Error opening PDF: {e}")
        print(f"Please open the PDF manually: {pdf_path}")

if __name__ == "__main__":
    view_spider_plot_pdf()