"""
Main Production Workflow: Reach 2 Local RF Model (Middle Reach - Urban Hanoi Corridor: 57.28km - 114.56km)

Features:
- Focused Random Forest Model for Reach 2 Urban Corridor
- Urban Riverbank & Sandbar/Island (Bãi nổi/Đảo nổi) Boundary Extraction
- Active Channel Constraints (S2 150m Reference Corridor Buffer)
- Standard Extraction (Ignoring Bridge Interference)
- Dedicated Interactive HTML Map with Validation Error Mask
"""

import os
import sys
import json
import time
import ee
import geopandas as gpd
import pandas as pd
from shapely.geometry import Point
from shapely.ops import substring

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.config import (
    GEE_PROJECT, SHORELINE_OPEN_SIZE, 
    SHORELINE_CLOSE_SIZE
)

GLOBAL_FEATURES = [
    'VV', 'VH', 'VV_ratio', 'VV_sum', 'VV_mean',
    'VV_contrast', 'VV_entropy', 'VV_homogeneity', 'VV_correlation', 'VV_ASM', 'VV_variance',
    'VH_contrast', 'VH_entropy', 'VH_homogeneity', 'VH_correlation', 'VH_ASM', 'VH_variance'
]

from src.aoi import load_local_aoi, load_reach_aoi
from src.classification import train_classifier, classify_image, load_training_polygons
from src.shoreline import (
    get_continuous_centerline, load_centerline,
    extract_shared_boundary, clean_shoreline_graph,
    smooth_and_simplify_shoreline, validate_shoreline,
    calibrate_s1_water_mask, generate_validation_shoreline_s2,
    refine_classification, generate_reach_interactive_map
)
from src.collection import create_seasonal_composite

def run_pipeline_for_reach2(year=2024, season='dry'):
    print(f"\n=============================================================")
    print(f" REACH 2 LOCAL RF EXECUTION (YEAR: {year}, SEASON: {season.upper()})")
    print("=============================================================")
    
    start_time = time.time()
    
    cl_linestring = get_continuous_centerline()
    cl_gdf = gpd.GeoDataFrame(geometry=[cl_linestring], crs="EPSG:4326").to_crs("EPSG:32648")
    centerline_geom_utm = cl_gdf.geometry.iloc[0]
    centerline_fc = load_centerline()
    
    reach2_geojson = load_reach_aoi(2)
    reach2_gdf = gpd.GeoDataFrame.from_features(reach2_geojson['features'], crs="EPSG:4326")
    reach2_corridor_utm = reach2_gdf.to_crs("EPSG:32648").geometry.union_all()
    reach2_ee_geom = ee.Geometry(reach2_geojson['features'][0]['geometry'])
    
    s2_ref_gdf, s2_water_poly = generate_validation_shoreline_s2(year, season, reach2_ee_geom, bridge_mask=None)
    if not s2_ref_gdf.empty:
        s2_ref_gdf = s2_ref_gdf[s2_ref_gdf.geometry.intersects(reach2_corridor_utm)]
        
    composite_r2 = create_seasonal_composite(year, season, reach2_ee_geom)
    training_fc_r2 = load_training_polygons().filterBounds(reach2_ee_geom)
    r2_best_params = {'numberOfTrees': 300, 'variablesPerSplit': 3, 'bagFraction': 0.5}
    r2_classifier, _ = train_classifier(training_fc_r2, composite_r2, GLOBAL_FEATURES, r2_best_params)
    
    classified_r2, _ = classify_image(composite_r2.clip(reach2_ee_geom), r2_classifier, GLOBAL_FEATURES)
    reach2_water = classified_r2.eq(1)
    
    # Load manual bridge polygons, buffer by 50m along river flow, and strictly constrain to river channel (s2_water_poly) so land banks are NOT affected
    bridges_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'data', 'bridges.geojson')
    bridge_mask_img = None
    if os.path.exists(bridges_path):
        bridges_gdf = gpd.read_file(bridges_path)
        if bridges_gdf.crs is None:
            bridges_gdf.set_crs("EPSG:4326", inplace=True)
        bridges_utm = bridges_gdf.to_crs("EPSG:32648")
        bridges_buf_utm = bridges_utm.buffer(50)
        
        # Constrain strictly inside river water channel bounds (s2_water_poly + 20m buffer)
        if s2_water_poly is not None and not s2_water_poly.is_empty:
            water_channel_limit = s2_water_poly.buffer(20)
            bridges_constrained_utm = bridges_buf_utm.intersection(water_channel_limit)
        else:
            bridges_constrained_utm = bridges_buf_utm
            
        bridges_constrained_wgs = gpd.GeoDataFrame(geometry=bridges_constrained_utm, crs="EPSG:32648").to_crs("EPSG:4326")
        bridges_json = json.loads(bridges_constrained_wgs.to_json())
        bridges_fc = ee.FeatureCollection(bridges_json)
        bridge_mask_img = ee.Image(0).paint(bridges_fc, 1)
        reach2_water = reach2_water.where(bridge_mask_img.eq(1), 1)
        print("[Bridge Piercing] Applied river-channel constrained bridge water override (Land banks preserved).")
    
    calibrated_water = calibrate_s1_water_mask(reach2_water.rename('classification'), composite_r2, s2_ref_gdf)
    if bridge_mask_img is not None:
        calibrated_water = calibrated_water.where(bridge_mask_img.eq(1), 1)

    water_refined, _, _ = refine_classification(
        calibrated_water, reach2_ee_geom, centerline_fc,
        open_radius=SHORELINE_OPEN_SIZE, close_radius=SHORELINE_CLOSE_SIZE
    )
    if bridge_mask_img is not None:
        water_refined = water_refined.where(bridge_mask_img.eq(1), 1)
    
    scale = 20
    raw_gdf, _, _ = extract_shared_boundary(
        water_mask_refined=water_refined,
        centerline_fc=centerline_fc,
        scale=scale,
        year=year,
        season=season,
        bridge_mask=None,
        s2_water_poly=s2_water_poly
    )
    if not raw_gdf.empty:
        raw_gdf = raw_gdf[raw_gdf.geometry.intersects(reach2_corridor_utm)]
        
    cleaned_gdf = clean_shoreline_graph(raw_gdf)
    smoothed_gdf, smooth_metrics = smooth_and_simplify_shoreline(cleaned_gdf)
    
    output_dir = "outputs"
    os.makedirs(output_dir, exist_ok=True)
    
    out_s1_path = os.path.join(output_dir, f"reach2_s1_shoreline_{year}_{season}.geojson")
    out_s2_path = os.path.join(output_dir, f"reach2_s2_ref_{year}_{season}.geojson")
    
    if not smoothed_gdf.empty:
        smoothed_gdf.to_crs("EPSG:4326").to_file(out_s1_path, driver="GeoJSON")
        print(f"[Phase 7] Saved Reach 2 S1 shoreline to: {out_s1_path}")
        
    if not s2_ref_gdf.empty:
        s2_ref_gdf.to_crs("EPSG:4326").to_file(out_s2_path, driver="GeoJSON")
        print(f"[Phase 8] Saved Reach 2 S2 reference shoreline to: {out_s2_path}")
        
    val_stats = validate_shoreline(smoothed_gdf, s2_ref_gdf)
    
    map_dir = os.path.join(output_dir, "map")
    os.makedirs(map_dir, exist_ok=True)
    html_out_path = os.path.join(map_dir, f"reach2_interactive_map_{year}_{season}.html")
    generate_reach_interactive_map(
        extracted_gdf=smoothed_gdf,
        s2_ref_gdf=s2_ref_gdf,
        val_stats=val_stats,
        reach_title="Reach 2 (Trung lưu Hà Nội)",
        year=year,
        season=season,
        output_html_path=html_out_path
    )
    
    stats_summary = {
        'Season': season,
        'Points': val_stats.get('num_points', 0),
        'Mean': round(val_stats.get('mean_dist_m', 0.0), 2),
        'Median': round(val_stats.get('median_dist_m', 0.0), 2),
        'RMSE': round(val_stats.get('rmse_dist_m', 0.0), 2),
        'Hausdorff': round(val_stats.get('hausdorff_dist_m', 0.0), 2),
        'P95': round(val_stats.get('p95_dist_m', 0.0), 2),
        'RuntimeSec': round(time.time() - start_time, 1)
    }
    
    print(f"[{season.upper()} Results] Reach 2 Mean={stats_summary['Mean']}m, RMSE={stats_summary['RMSE']}m, P95={stats_summary['P95']}m")
    return stats_summary

def main():
    ee.Initialize(project=GEE_PROJECT)
    run_pipeline_for_reach2(year=2024, season='dry')
    run_pipeline_for_reach2(year=2024, season='wet')

if __name__ == "__main__":
    main()
