"""
Download utility to export pre-computed seasonal S1 composites from GEE Assets locally.
Clips to a high-resolution central Hanoi bounding box (approx 5x5 km) at full 10m scale
to remain within GEE's 50MB direct download limits.

Usage:
  python scripts/download_asset.py --year 2017 --season dry
"""

import sys
import os
import argparse
import requests

sys.path.insert(0, os.getcwd())

import ee
from src.config import GEE_PROJECT, OUTPUT_DIR

def main():
    parser = argparse.ArgumentParser(description="Download pre-computed GEE S1 composite assets locally.")
    parser.add_argument("--year", type=int, default=2017, help="Year of composite (2017-2026)")
    parser.add_argument("--season", type=str, default="dry", choices=["dry", "wet"], help="Season (dry or wet)")
    args = parser.parse_args()

    # 1. Initialize GEE
    if not ee.data.is_initialized():
        ee.Initialize(project=GEE_PROJECT)
        
    # 2. Geometry - 5x5 km box around central Hanoi (covers Long Bien bridge)
    qa_bbox = ee.Geometry.Rectangle([105.83, 21.01, 105.89, 21.07])
    
    # 3. Load pre-computed GEE Asset
    asset_id = f"projects/{GEE_PROJECT}/assets/s1_composite_{args.year}_{args.season}"
    print(f"[1/3] Loading pre-computed asset: {asset_id}...")
    
    try:
        asset_img = ee.Image(asset_id)
        
        # Select bands to export (VV, VH, VV_VH_ratio)
        export_bands = ['VV', 'VH', 'VV_VH_ratio']
        export_img = asset_img.select(export_bands)
        
        # 4. Get Download URL (direct GeoTIFF)
        print("[2/3] Requesting download URL from GEE at full 10m resolution...")
        url = export_img.getDownloadURL({
            'scale': 10,
            'region': qa_bbox,
            'format': 'GeoTIFF'
        })
        
        # 5. Download the file
        output_path = os.path.join(OUTPUT_DIR, f"s1_composite_{args.year}_{args.season}.tif")
        print(f"[3/3] Downloading file to: {output_path}...")
        
        r = requests.get(url, stream=True)
        if r.status_code == 200:
            with open(output_path, 'wb') as f:
                for chunk in r.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
            print(f"Download complete! Saved to {output_path}")
            print(f"File size: {os.path.getsize(output_path) / (1024*1024):.2f} MB")
        else:
            print(f"GEE returned status code {r.status_code}")
            print(f"Response: {r.text}")
            
    except Exception as e:
        print(f"Error during export: {e}")
        print(f"Please ensure the task for {args.year}_{args.season} has finished and state is SUCCEEDED on GEE.")

if __name__ == '__main__':
    main()
