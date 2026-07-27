"""
Interactive Folium Map Screenshot Generator using Playwright

Opens interactive Folium HTML map files in Playwright headless Chromium,
waits for tile layers and vector GeoJSON lines to fully render,
and captures high-resolution publication-grade PNG screenshots for reports.
"""

import os
import sys
import time
from playwright.sync_api import sync_playwright

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUTPUTS_DIR = os.path.join(PROJECT_ROOT, "outputs")
FIGURES_DIR = os.path.join(OUTPUTS_DIR, "REPORT", "figures")
os.makedirs(FIGURES_DIR, exist_ok=True)

MAP_TARGETS = [
    {
        "html": os.path.join(OUTPUTS_DIR, "others", "master_multitemporal_shoreline_2017_2026.html"),
        "png": os.path.join(FIGURES_DIR, "fig_map_master_multitemporal_2017_2026.png"),
        "title": "Master Multi-Temporal Shoreline Map (2017-2026)"
    },
    {
        "html": os.path.join(OUTPUTS_DIR, "2024", "2024_dry", "shoreline_qc_2024_dry.html"),
        "png": os.path.join(FIGURES_DIR, "fig_map_shoreline_qc_2024_dry.png"),
        "title": "Shoreline QC Map (2024 Dry Season)"
    },
    {
        "html": os.path.join(OUTPUTS_DIR, "2024", "2024_dry", "validation_error_map_2024_dry.html"),
        "png": os.path.join(FIGURES_DIR, "fig_map_validation_error_2024_dry.png"),
        "title": "Positional Error Spatial Distribution Map (2024 Dry)"
    },
    {
        "html": os.path.join(OUTPUTS_DIR, "2024", "2024_wet", "shoreline_qc_2024_wet.html"),
        "png": os.path.join(FIGURES_DIR, "fig_map_shoreline_qc_2024_wet.png"),
        "title": "Shoreline QC Map (2024 Wet Season)"
    },
    {
        "html": os.path.join(OUTPUTS_DIR, "2026", "2026_dry", "shoreline_qc_2026_dry.html"),
        "png": os.path.join(FIGURES_DIR, "fig_map_shoreline_qc_2026_dry.png"),
        "title": "Shoreline QC Map (2026 Dry Season)"
    }
]

def capture_screenshots():
    print("[Screenshot Generator] Launching Playwright Chromium...")
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(viewport={"width": 1600, "height": 1000})
        page = context.new_page()
        
        for target in MAP_TARGETS:
            html_path = target["html"]
            png_path = target["png"]
            title = target["title"]
            
            if not os.path.exists(html_path):
                print(f"  [Skip] File not found: {html_path}")
                continue
                
            file_url = f"file:///{html_path.replace(os.sep, '/')}"
            print(f"  [Capturing] {title} -> {os.path.basename(png_path)}")
            
            try:
                page.goto(file_url, wait_until="commit", timeout=5000)
                # Pause 2 seconds for Leaflet map elements to render
                page.wait_for_timeout(2000)
                page.screenshot(path=png_path, full_page=False)
                print(f"  [Success] Saved: {png_path}")
            except Exception as e:
                print(f"  [Error] Failed to capture {title}: {e}")


                
        browser.close()
    print("[Screenshot Generator] Screenshot capture completed!")

if __name__ == '__main__':
    capture_screenshots()
