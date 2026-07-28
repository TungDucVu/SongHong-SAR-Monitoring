"""
Fast Offline Local Shoreline Extraction Engine (2017-2026)
Processes downloaded GeoTIFF composites locally using Rasterio & GeoPandas.
Bypasses GEE API memory limits and completes seasonal shoreline extraction in 10-30 seconds per season!
"""

import os
import sys
import time
import glob
import re
import numpy as np
import geopandas as gpd
import pandas as pd
import rasterio
from rasterio.features import shapes
from shapely.geometry import shape, MultiPolygon, Polygon
from shapely.ops import unary_union
import cv2
from concurrent.futures import ProcessPoolExecutor, as_completed

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(PROJECT_ROOT)

from src.aoi import load_local_aoi, load_reach_aoi
from src.shoreline import get_continuous_centerline, smooth_and_simplify_shoreline, validate_shoreline

def process_geotiff_season(geotiff_path, year, season):
    print(f"\n=============================================================")
    print(f" FAST OFFLINE SHORELINE EXTRACTION: {year} {season.upper()}")
    print(f" Raster: {os.path.basename(geotiff_path)}")
    print("=============================================================")
    
    start_t = time.time()
    
    # 1. Open GeoTIFF raster
    with rasterio.open(geotiff_path) as src:
        raster_data = src.read()
        transform = src.transform
        crs = src.crs
        nodata = src.nodata
        
    print(f"  [Raster] Shape: {raster_data.shape}, CRS: {crs}")
    
    # Extract VV & VH bands (Assuming Band 1 = VV, Band 2 = VH)
    vv_band = raster_data[0]
    vh_band = raster_data[1] if raster_data.shape[0] > 1 else vv_band
    
    # Mask invalid nodata
    valid_mask = (vv_band != 0) & (~np.isnan(vv_band))
    
    # 2. Local Thresholding (Dry vs Wet threshold calibration)
    # Default VV threshold for water: <= -14.5 dB (Dry), <= -13.5 dB (Wet)
    vv_thresh = -14.5 if season.lower() == 'dry' else -13.5
    water_mask = (vv_band <= vv_thresh) & valid_mask
    
    # Convert to uint8 for morphological processing
    water_img = (water_mask.astype(np.uint8)) * 255
    
    # 3. Local Morphological Cleaning (Open/Close Filter)
    kernel_small = cv2.getStructuringElement(cv2.MORPH_RECT, (3, 3))
    kernel_large = cv2.getStructuringElement(cv2.MORPH_RECT, (5, 5))
    
    # Remove small noise pixels (Opening) & fill small internal holes (Closing)
    water_cleaned = cv2.morphologyEx(water_img, cv2.MORPH_OPEN, kernel_small)
    water_cleaned = cv2.morphologyEx(water_cleaned, cv2.MORPH_CLOSE, kernel_large)
    
    binary_mask = (water_cleaned > 0).astype(np.uint8)
    
    # 4. Polygonize water raster locally using Rasterio
    results = (
        {'properties': {'raster_val': v}, 'geometry': s}
        for i, (s, v) in enumerate(shapes(binary_mask, mask=binary_mask, transform=transform))
    )
    
    poly_list = [shape(r['geometry']) for r in results]
    if not poly_list:
        print(f"  [Warning] No water polygons extracted for {year} {season}")
        return None
        
    water_gdf = gpd.GeoDataFrame(geometry=poly_list, crs=crs)
    if crs != "EPSG:32648":
        water_gdf = water_gdf.to_crs("EPSG:32648")
        
    # Calculate area and filter small polygons (< 8,000 m2 ~ 20 pixels)
    water_gdf['area_m2'] = water_gdf.geometry.area
    water_gdf = water_gdf[water_gdf['area_m2'] >= 8000.0]
    
    if water_gdf.empty:
        print(f"  [Warning] All water polygons filtered out by size constraint.")
        return None
        
    # 5. Apply Active Channel Buffer Constraint (150m buffer from Centerline/S2 Ref)
    cl_linestring = get_continuous_centerline()
    cl_gdf = gpd.GeoDataFrame(geometry=[cl_linestring], crs="EPSG:4326").to_crs("EPSG:32648")
    cl_buffer_150m = cl_gdf.geometry.iloc[0].buffer(800.0)  # Active channel corridor buffer
    
    water_gdf = water_gdf[water_gdf.geometry.intersects(cl_buffer_150m)]
    merged_water = unary_union(water_gdf.geometry)
    
    if merged_water.is_empty:
        print("  [Warning] Active channel buffer yielded empty geometry.")
        return None
        
    # 6. Extract Shoreline Boundary
    boundary_geom = merged_water.boundary
    if boundary_geom.geom_type == 'MultiLineString':
        lines = list(boundary_geom.geoms)
    elif boundary_geom.geom_type == 'LineString':
        lines = [boundary_geom]
    else:
        lines = []
        
    shoreline_gdf = gpd.GeoDataFrame(geometry=lines, crs="EPSG:32648")
    
    # 7. Smooth & Simplify Shoreline (Douglas-Peucker & Chaikin)
    shoreline_smoothed, _ = smooth_and_simplify_shoreline(shoreline_gdf)
    
    # Save season output directory
    season_dir = os.path.join(PROJECT_ROOT, "outputs", str(year), f"{year}_{season.lower()}")
    os.makedirs(season_dir, exist_ok=True)
    
    out_file = os.path.join(season_dir, f"shoreline_{year}_{season.lower()}_final.geojson")
    shoreline_smoothed.to_file(out_file, driver="GeoJSON")
    
    # Split shoreline per reach
    for r_num in [1, 2, 3]:
        reach_json = load_reach_aoi(r_num)
        reach_gdf = gpd.GeoDataFrame.from_features(reach_json['features'], crs="EPSG:4326").to_crs("EPSG:32648")
        r_corridor = reach_gdf.geometry.union_all()
        
        reach_lines = shoreline_smoothed[shoreline_smoothed.geometry.intersects(r_corridor)]
        r_out = os.path.join(season_dir, f"reach{r_num}_s1_shoreline_{year}_{season.lower()}.geojson")
        if not reach_lines.empty:
            reach_lines.to_file(r_out, driver="GeoJSON")
            
    elapsed = time.time() - start_t
    print(f"  [Success] Saved offline shoreline: {out_file} (Completed in {elapsed:.2f}s!)")
    
    # 8. Validate against S2 reference if available
    s2_ref_file = os.path.join(PROJECT_ROOT, "data", f"s2_ref_shoreline_{year}_{season.lower()}.geojson")
    if not os.path.exists(s2_ref_file):
        s2_ref_file = os.path.join(season_dir, f"shoreline_{year}_{season.lower()}_s2_ref.geojson")
        
    if os.path.exists(s2_ref_file):
        s2_ref_gdf = gpd.read_file(s2_ref_file)
        val_stats = validate_shoreline(shoreline_smoothed, s2_ref_gdf)
        print(f"  [Validation Stats {year} {season.upper()}]")
        print(f"    • Mean Error: {val_stats.get('mean_dist_m', 0):.2f} m")
        print(f"    • RMSE      : {val_stats.get('rmse_dist_m', 0):.2f} m")
        print(f"    • P95 Error : {val_stats.get('p95_dist_m', 0):.2f} m")
        
    return out_file

def main():
    import argparse
    parser = argparse.ArgumentParser(description="Fast Offline Shoreline Extraction")
    parser.add_argument("--year", type=int, default=2024, help="Year to process (2017-2026)")
    parser.add_argument("--season", choices=['dry', 'wet', 'all'], default='dry', help="Season to process")
    parser.add_argument("--all", action="store_true", help="Process all downloaded GeoTIFFs offline")
    args = parser.parse_args()

    geotiff_dir = os.path.join(PROJECT_ROOT, "outputs", "geotiffs")
    if not os.path.exists(geotiff_dir):
        print(f"[Error] GeoTIFF directory not found: {geotiff_dir}")
        return

    if args.all:
        tif_files = sorted(glob.glob(os.path.join(geotiff_dir, "*.tif")))
    else:
        if args.season == 'all':
            patterns = [f"s1_composite_{args.year}_dry.tif", f"s1_composite_{args.year}_wet.tif"]
        else:
            patterns = [f"s1_composite_{args.year}_{args.season}.tif"]
        tif_files = [os.path.join(geotiff_dir, p) for p in patterns if os.path.exists(os.path.join(geotiff_dir, p))]

    print(f"[Offline Engine] Found {len(tif_files)} GeoTIFF files to process locally.")
    
    for tif_path in tif_files:
        m = re.search(r's1_composite_(\d{4})_(dry|wet)\.tif', os.path.basename(tif_path))
        if m:
            yr = int(m.group(1))
            ssn = m.group(2)
            process_geotiff_season(tif_path, yr, ssn)

if __name__ == "__main__":
    main()
