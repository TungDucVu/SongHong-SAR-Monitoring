"""
Clean and Structure outputs/2024/2024_dry Directory into Organized Subfolders.
Subfolders:
- maps/    : Interactive Folium HTML maps
- vectors/ : Shoreline & reference GeoJSON vector files
- figures/ : Error histogram & CDF plot images (PNG)
- stats/   : CSV & TXT performance metric files
"""

import os
import sys
import shutil

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TARGET_DIR = os.path.join(PROJECT_ROOT, "outputs", "2024", "2024_dry")

def clean_and_organize():
    if not os.path.exists(TARGET_DIR):
        print(f"[Error] Directory not found: {TARGET_DIR}")
        return

    maps_dir = os.path.join(TARGET_DIR, "maps")
    vectors_dir = os.path.join(TARGET_DIR, "vectors")
    figures_dir = os.path.join(TARGET_DIR, "figures")
    stats_dir = os.path.join(TARGET_DIR, "stats")

    for d in [maps_dir, vectors_dir, figures_dir, stats_dir]:
        os.makedirs(d, exist_ok=True)

    moved_count = 0
    for fname in os.listdir(TARGET_DIR):
        fpath = os.path.join(TARGET_DIR, fname)
        
        # Skip subdirectories
        if os.path.isdir(fpath):
            continue

        target_subfolder = None
        if fname.endswith(".html"):
            target_subfolder = maps_dir
        elif fname.endswith(".geojson"):
            target_subfolder = vectors_dir
        elif fname.endswith(".png"):
            target_subfolder = figures_dir
        elif fname.endswith(".csv") or fname.endswith(".txt"):
            target_subfolder = stats_dir

        if target_subfolder:
            shutil.copy2(fpath, os.path.join(target_subfolder, fname))
            moved_count += 1
            print(f"  [Organized] {fname} -> {os.path.basename(target_subfolder)}/")

    print(f"\n[Success] Organized {moved_count} files into structured subfolders in {TARGET_DIR}")

if __name__ == "__main__":
    clean_and_organize()
