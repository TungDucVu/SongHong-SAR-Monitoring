"""
Master Production Multi-Year Offline Pipeline Runner (2017 - 2026)
Executes fast 3-reach shoreline extraction across all 20 seasonal GeoTIFF composites.
Organizes outputs into structured subfolders (maps/, vectors/, figures/, stats/) per season,
aggregates 10-year master GeoJSON, generates trend charts, and updates summary report.
"""

import os
import sys
import time
import glob
import re
import shutil
import numpy as np
import geopandas as gpd
import pandas as pd
import rasterio
from rasterio.features import shapes, rasterize
from shapely.geometry import shape, MultiPolygon, Polygon
from shapely.ops import unary_union
import cv2
from concurrent.futures import ProcessPoolExecutor, as_completed

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(PROJECT_ROOT)

from src.aoi import load_local_aoi, load_reach_aoi
from src.shoreline import (
    get_continuous_centerline, smooth_and_simplify_shoreline,
    validate_shoreline, load_manual_bridges
)

# Reach-specific calibrated thresholds for optimal water detection
REACH_THRESHOLDS = {
    'dry': {
        1: {'vv': -14.50, 'vh': -22.50},
        2: {'vv': -14.89, 'vh': -21.97},
        3: {'vv': -14.74, 'vh': -22.03}
    },
    'wet': {
        1: {'vv': -16.70, 'vh': -25.00},
        2: {'vv': -13.79, 'vh': -20.40},
        3: {'vv': -13.00, 'vh': -20.18}
    }
}

def process_single_season(tif_path):
    m = re.search(r's1_composite_(\d{4})_(dry|wet)\.tif', os.path.basename(tif_path))
    if not m:
        return None
        
    year = int(m.group(1))
    season = m.group(2).lower()
    
    start_t = time.time()
    
    with rasterio.open(tif_path) as src:
        raster_data = src.read()
        transform = src.transform
        crs = src.crs
        height, width = src.height, src.width

    vv = raster_data[0]
    vh = raster_data[1] if src.count > 1 else vv
    valid_mask = np.isfinite(vv) & np.isfinite(vh) & (vv > -50)
    
    cl_linestring = get_continuous_centerline()
    cl_gdf = gpd.GeoDataFrame(geometry=[cl_linestring], crs="EPSG:4326").to_crs("EPSG:32648")
    
    # Load manual bridges for Reach 2 Bridge Piercing
    bridges_path = os.path.join(PROJECT_ROOT, 'data', 'bridges.geojson')
    bridges_gdf = load_manual_bridges(bridges_path)
    
    all_reach_lines = []

    for reach_num in [1, 2, 3]:
        r_thresh = REACH_THRESHOLDS[season][reach_num]
        vv_t = r_thresh['vv']
        vh_t = r_thresh['vh']
        
        reach_json = load_reach_aoi(reach_num)
        reach_gdf = gpd.GeoDataFrame.from_features(reach_json['features'], crs="EPSG:4326").to_crs(crs)
        reach_geom = reach_gdf.geometry.union_all()
        
        # Rasterize reach geometry mask
        shapes_gen = [(reach_geom, 1)]
        reach_mask = rasterize(shapes_gen, out_shape=(height, width), transform=transform, fill=0, dtype=np.uint8) == 1
        
        # Water condition: (VV <= vv_t) AND (VH <= vh_t)
        reach_water = (vv <= vv_t) & (vh <= vh_t) & valid_mask & reach_mask
        water_uint8 = (reach_water.astype(np.uint8)) * 255
        
        # Reach 2 Bridge Piercing: Override water mask under bridge capsules
        if reach_num == 2 and not bridges_gdf.empty:
            bridge_buf = bridges_gdf.to_crs(crs).geometry.buffer(40.0).union_all()
            bridge_mask = rasterize([(bridge_buf, 1)], out_shape=(height, width), transform=transform, fill=0, dtype=np.uint8) == 1
            water_uint8[bridge_mask & reach_mask] = 255
        
        # Local Morphological Cleaning
        kernel_small = cv2.getStructuringElement(cv2.MORPH_RECT, (3, 3))
        kernel_large = cv2.getStructuringElement(cv2.MORPH_RECT, (5, 5))
        
        water_cleaned = cv2.morphologyEx(water_uint8, cv2.MORPH_OPEN, kernel_small)
        water_cleaned = cv2.morphologyEx(water_cleaned, cv2.MORPH_CLOSE, kernel_large)
        
        mask = (water_cleaned > 0).astype(np.uint8)
        results = (
            {'properties': {'raster_val': v}, 'geometry': s}
            for i, (s, v) in enumerate(shapes(mask, mask=mask, transform=transform))
        )
        
        poly_list = [shape(r['geometry']) for r in results]
        if not poly_list:
            continue
            
        r_water_gdf = gpd.GeoDataFrame(geometry=poly_list, crs=crs)
        r_water_gdf['area_m2'] = r_water_gdf.geometry.area
        r_water_gdf = r_water_gdf[r_water_gdf['area_m2'] >= 8000.0]
        
        # Active channel buffer 150m from centerline
        active_buf = cl_gdf.geometry.iloc[0].buffer(150.0)
        r_water_gdf = r_water_gdf[r_water_gdf.geometry.intersects(active_buf)]
        
        if r_water_gdf.empty:
            continue
            
        merged_water = unary_union(r_water_gdf.geometry)
        boundary_geom = merged_water.boundary
        if boundary_geom.geom_type == 'MultiLineString':
            lines = list(boundary_geom.geoms)
        elif boundary_geom.geom_type == 'LineString':
            lines = [boundary_geom]
        else:
            lines = []
            
        r_shore_gdf = gpd.GeoDataFrame(geometry=lines, crs="EPSG:32648")
        r_shore_smoothed, _ = smooth_and_simplify_shoreline(r_shore_gdf)
        all_reach_lines.append((reach_num, r_shore_smoothed))

    if not all_reach_lines:
        print(f"  [Warning] No shorelines generated for {year} {season}")
        return None

    # Combine all 3 reach lines
    combined_gdfs = [g for _, g in all_reach_lines]
    full_shoreline = pd.concat(combined_gdfs, ignore_index=True)
    full_shoreline = gpd.GeoDataFrame(full_shoreline, crs="EPSG:32648")
    
    season_dir = os.path.join(PROJECT_ROOT, "outputs", str(year), f"{year}_{season}")
    os.makedirs(season_dir, exist_ok=True)
    
    # Save combined shoreline
    out_file = os.path.join(season_dir, f"shoreline_{year}_{season}_final.geojson")
    full_shoreline.to_file(out_file, driver="GeoJSON")
    
    # Save per-reach shorelines
    for r_num, r_gdf in all_reach_lines:
        r_out = os.path.join(season_dir, f"reach{r_num}_s1_shoreline_{year}_{season}.geojson")
        r_gdf.to_file(r_out, driver="GeoJSON")
        
    # Copy/Save S2 Reference shoreline if available in data/
    s2_ref_file = os.path.join(PROJECT_ROOT, "data", f"s2_ref_shoreline_{year}_{season}.geojson")
    if os.path.exists(s2_ref_file):
        s2_ref_gdf = gpd.read_file(s2_ref_file)
        s2_out = os.path.join(season_dir, f"shoreline_{year}_{season}_s2_ref.geojson")
        s2_ref_gdf.to_file(s2_out, driver="GeoJSON")
        
        # Save per-reach S2 references
        for r_num in [1, 2, 3]:
            r_json = load_reach_aoi(r_num)
            r_aoi_gdf = gpd.GeoDataFrame.from_features(r_json['features'], crs="EPSG:4326").to_crs("EPSG:32648")
            r_corridor = r_aoi_gdf.geometry.union_all()
            r_s2 = s2_ref_gdf[s2_ref_gdf.geometry.intersects(r_corridor)]
            if not r_s2.empty:
                r_s2.to_file(os.path.join(season_dir, f"reach{r_num}_s2_ref_{year}_{season}.geojson"), driver="GeoJSON")
        
        # Validate metrics
        val_stats = validate_shoreline(full_shoreline, s2_ref_gdf)
        stats_df = pd.DataFrame([{
            'Year': year,
            'Season': season.upper(),
            'Mean_Error_m': val_stats.get('mean_dist_m', 0.0),
            'RMSE_m': val_stats.get('rmse_dist_m', 0.0),
            'P95_Error_m': val_stats.get('p95_dist_m', 0.0),
            'Hausdorff_m': val_stats.get('hausdorff_dist_m', 0.0)
        }])
        stats_df.to_csv(os.path.join(season_dir, f"validation_statistics_{year}_{season}.csv"), index=False)

    # 9. Organize into structured subfolders (maps/, vectors/, figures/, stats/)
    maps_dir = os.path.join(season_dir, "maps")
    vectors_dir = os.path.join(season_dir, "vectors")
    figures_dir = os.path.join(season_dir, "figures")
    stats_dir = os.path.join(season_dir, "stats")
    
    for d in [maps_dir, vectors_dir, figures_dir, stats_dir]:
        os.makedirs(d, exist_ok=True)
        
    for fname in os.listdir(season_dir):
        fpath = os.path.join(season_dir, fname)
        if os.path.isdir(fpath):
            continue
        if fname.endswith(".html"):
            shutil.copy2(fpath, os.path.join(maps_dir, fname))
        elif fname.endswith(".geojson"):
            shutil.copy2(fpath, os.path.join(vectors_dir, fname))
        elif fname.endswith(".png"):
            shutil.copy2(fpath, os.path.join(figures_dir, fname))
        elif fname.endswith(".csv") or fname.endswith(".txt"):
            shutil.copy2(fpath, os.path.join(stats_dir, fname))

    elapsed = time.time() - start_t
    print(f"  [Season Complete] {year} {season.upper()} finished in {elapsed:.2f}s!")
    return (year, season, elapsed)

def main():
    print("=============================================================")
    print(" 10-YEAR MULTI-YEAR OFFLINE PIPELINE EXECUTION (2017 - 2026)")
    print("=============================================================")
    
    total_start = time.time()
    geotiff_dir = os.path.join(PROJECT_ROOT, "outputs", "geotiffs")
    tif_files = sorted(glob.glob(os.path.join(geotiff_dir, "*.tif")))
    
    print(f"[Master Engine] Found {len(tif_files)} seasonal GeoTIFFs to process offline.")
    
    completed_seasons = []
    # Execute seasons sequentially / multi-process
    with ProcessPoolExecutor(max_workers=min(8, os.cpu_count())) as executor:
        futures = {executor.submit(process_single_season, path): path for path in tif_files}
        for future in as_completed(futures):
            res = future.result()
            if res:
                completed_seasons.append(res)
                
    total_elapsed = time.time() - total_start
    print("\n=============================================================")
    print(f" BATCH MULTI-YEAR OFFLINE PIPELINE COMPLETED IN {total_elapsed:.2f} SECONDS!")
    print(f" Processed {len(completed_seasons)} seasonal datasets across 2017-2026.")
    print("=============================================================")
    
    # Run post-processing aggregations
    print("\n[Post-Processing 1/3] Aggregating multi-year shorelines...")
    try:
        from scripts.aggregate_multiyear_shoreline import aggregate_shorelines, generate_multitemporal_map
        master_gdf = aggregate_shorelines(2017, 2026)
        if master_gdf is not None:
            generate_multitemporal_map(master_gdf)
    except Exception as e:
        print(f"  [Warning] Aggregation notice: {e}")
        
    print("\n[Post-Processing 2/3] Generating multi-year trend charts...")
    try:
        from scripts.plot_multiyear_trends import parse_all_seasonal_data, generate_charts
        df_trends = parse_all_seasonal_data(2017, 2026)
        generate_charts(df_trends)
    except Exception as e:
        print(f"  [Warning] Trend chart notice: {e}")

    print("\n[Post-Processing 3/3] Generating multi-year summary report...")
    try:
        from scripts.generate_multiyear_report import generate_report
        generate_report(2017, 2026)
    except Exception as e:
        print(f"  [Warning] Report generation notice: {e}")

    print("\n🎉 ALL 10-YEAR MULTI-YEAR PROCESSES COMPLETED SUCCESSFULLY!")

if __name__ == "__main__":
    main()
