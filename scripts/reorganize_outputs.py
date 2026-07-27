"""
Outputs Folder Restructuring & Reorganization Script

Scans outputs/ and outputs/others/ to organize all seasonal files into:
- outputs/{year}/{year}_{season}/ (All season-specific vector GeoJSONs, interactive HTML maps, error PNGs, CSV stats)
- outputs/REPORT/ (All markdown reports, TeX files, slides)
- outputs/others/ (Master multi-temporal files, export tasks, metadata)
"""

import os
import sys
import re
import shutil

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUTPUTS_DIR = os.path.join(PROJECT_ROOT, "outputs")

def get_season_output_dir(year, season):
    season_dir = os.path.join(OUTPUTS_DIR, str(year), f"{year}_{season.lower()}")
    os.makedirs(season_dir, exist_ok=True)
    return season_dir

def reorganize_outputs():
    print(f"[Reorganize] Starting reorganization of: {OUTPUTS_DIR}")
    
    if not os.path.exists(OUTPUTS_DIR):
        print(f"[Error] Outputs directory does not exist: {OUTPUTS_DIR}")
        return

    report_dir = os.path.join(OUTPUTS_DIR, "REPORT")
    others_dir = os.path.join(OUTPUTS_DIR, "others")
    os.makedirs(report_dir, exist_ok=True)
    os.makedirs(others_dir, exist_ok=True)
    
    pattern = re.compile(r'_(20\d{2})_(dry|wet)(_|\.|$)', re.IGNORECASE)

    # 1. Process files in outputs/others/
    if os.path.exists(others_dir):
        for fname in os.listdir(others_dir):
            fpath = os.path.join(others_dir, fname)
            if os.path.isfile(fpath):
                if fname.startswith("master") or fname.startswith("shorelines_"):
                    continue
                match = pattern.search(fname)
                if match:
                    yr = match.group(1)
                    ssn = match.group(2).lower()
                    target_season_dir = get_season_output_dir(yr, ssn)
                    target_path = os.path.join(target_season_dir, fname)
                    shutil.move(fpath, target_path)
                    print(f"  Moved from [others] to [{yr}/{yr}_{ssn}]: {fname}")

    # 2. Process root outputs/ directory files
    for fname in os.listdir(OUTPUTS_DIR):
        fpath = os.path.join(OUTPUTS_DIR, fname)
        if os.path.isdir(fpath):
            continue
            
        match = pattern.search(fname)
        if match:
            yr = match.group(1)
            ssn = match.group(2).lower()
            target_season_dir = get_season_output_dir(yr, ssn)
            target_path = os.path.join(target_season_dir, fname)
            shutil.move(fpath, target_path)
            print(f"  Moved to [{yr}/{yr}_{ssn}]: {fname}")
        elif fname.endswith(('.md', '.tex', '.pdf')):
            if fname.lower() != 'readme.md':
                target_path = os.path.join(report_dir, fname)
                shutil.move(fpath, target_path)
                print(f"  Moved to [REPORT]: {fname}")

    print("[Reorganize] Reorganization completed successfully!")

if __name__ == '__main__':
    reorganize_outputs()
