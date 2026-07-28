"""
Fast Downloader for 2017-2026 Sentinel-1 SAR Seasonal Composite GeoTIFFs.
Uses multi-threaded parallel tile downloads (num_threads=8) for maximum speed.
"""

import os
import sys
import time
import ee
import geemap
import geopandas as gpd

if sys.platform == 'win32':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')
    except Exception:
        pass

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(PROJECT_ROOT)

from src.config import GEE_PROJECT, OUTPUT_DIR
from src.aoi import get_aoi_geometry
from src.shoreline import get_continuous_centerline
from src.collection import create_seasonal_composite

def main():
    print("=============================================================")
    print(" FAST GEOTIFF DOWNLOADER FOR SENTINEL-1 COMPOSITES (2017-2026)")
    print("=============================================================")
    
    ee.Initialize(project=GEE_PROJECT)
    
    out_dir = os.path.join(OUTPUT_DIR, "geotiffs")
    os.makedirs(out_dir, exist_ok=True)
    
    aoi_geom = get_aoi_geometry()
    
    # 2km corridor buffer along river centerline for bounded export
    cl_linestring = get_continuous_centerline()
    cl_gdf = gpd.GeoDataFrame(geometry=[cl_linestring], crs="EPSG:4326").to_crs("EPSG:32648")
    corridor_utm = cl_gdf.geometry.buffer(2000).union_all()
    corridor_wgs = gpd.GeoDataFrame(geometry=[corridor_utm], crs="EPSG:32648").to_crs("EPSG:4326")
    export_geom = ee.Geometry(corridor_wgs.geometry.iloc[0].__geo_interface__)
    bbox = export_geom.bounds().getInfo()

    years = list(range(2017, 2027))
    seasons = ['dry', 'wet']
    
    total_tasks = len(years) * len(seasons)
    task_idx = 0
    
    start_all_time = time.time()
    
    for yr in years:
        for season in seasons:
            task_idx += 1
            out_path = os.path.join(out_dir, f"s1_composite_{yr}_{season}.tif")
            
            if os.path.exists(out_path) and os.path.getsize(out_path) > 100000:
                print(f"[{task_idx}/{total_tasks}] [Skip] {yr} {season.upper()} GeoTIFF already exists: {out_path}")
                continue
                
            print(f"\n[{task_idx}/{total_tasks}] Requesting S1 Composite for {yr} {season.upper()}...")
            t0 = time.time()
            
            try:
                composite = create_seasonal_composite(yr, season, aoi_geom, reducer_type='percentile_10', force_on_the_fly=True)
                if composite is None:
                    print(f"[Warning] Empty composite for {yr} {season.upper()}")
                    continue
                    
                export_img = composite.select(['VV', 'VH'])
                
                print(f"Downloading GeoTIFF via 8 parallel threads to: {out_path}...")
                geemap.download_ee_image(
                    image=export_img.clip(export_geom),
                    filename=out_path,
                    region=bbox,
                    crs='EPSG:32648',
                    scale=20,
                    max_tile_dim=512,
                    num_threads=8,
                    overwrite=True
                )
                
                elapsed = time.time() - t0
                file_size_mb = os.path.getsize(out_path) / (1024 * 1024) if os.path.exists(out_path) else 0.0
                print(f"✅ Finished {yr} {season.upper()} in {elapsed:.1f}s ({file_size_mb:.2f} MB)")
                
            except Exception as e:
                print(f"❌ Failed downloading {yr} {season.upper()}: {e}")
                
    total_elapsed = time.time() - start_all_time
    print(f"\n=============================================================")
    print(f" BATCH DOWNLOAD COMPLETE in {total_elapsed/60.0:.2f} minutes!")
    print(f" Saved GeoTIFFs to: {out_dir}")
    print("=============================================================")

if __name__ == "__main__":
    main()
