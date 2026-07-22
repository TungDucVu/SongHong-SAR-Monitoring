"""
Main Production Workflow: Reach 2 & 3 Global RF Model (Hanoi Urban & Agricultural Delta Corridor)

Features:
- Streamlined 300-Tree Global Random Forest Classifier
- 193 Broad-area Training Polygons
- Active Channel Constraints (S2 150m Reference Corridor Buffer)
- 2D Binary Morphological Cleaning & Graph Pruning
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
from src.aoi import load_local_aoi
from src.classification import train_classifier, classify_image, load_training_polygons
from src.shoreline import (
    get_continuous_centerline, load_centerline,
    extract_shared_boundary, clean_shoreline_graph,
    smooth_and_simplify_shoreline, validate_shoreline,
    calibrate_s1_water_mask, generate_validation_shoreline_s2,
    refine_classification
)
from src.collection import create_seasonal_composite

def run_pipeline_for_reach2_3(year=2024, season='dry'):
    print(f"\n=============================================================")
    print(f" REACH 2 & 3 GLOBAL RF EXECUTION (YEAR: {year}, SEASON: {season.upper()})")
    print("=============================================================")
    
    start_time = time.time()
    
    cl_linestring = get_continuous_centerline()
    cl_gdf = gpd.GeoDataFrame(geometry=[cl_linestring], crs="EPSG:4326").to_crs("EPSG:32648")
    centerline_geom_utm = cl_gdf.geometry.iloc[0]
    centerline_fc = load_centerline()
    
    total_len = centerline_geom_utm.length
    split_pt_wgs = Point(105.5415, 21.1528)
    split_pt_utm = gpd.GeoSeries([split_pt_wgs], crs="EPSG:4326").to_crs("EPSG:32648").iloc[0]
    limit1 = centerline_geom_utm.project(split_pt_utm)
    
    reach2_3_line_utm = substring(centerline_geom_utm, limit1, total_len)
    
    aoi_geojson = load_local_aoi()
    aoi_gdf = gpd.GeoDataFrame.from_features(aoi_geojson['features'], crs="EPSG:4326")
    aoi_utm = aoi_gdf.to_crs("EPSG:32648").geometry.union_all()
    
    reach2_3_corridor_utm = reach2_3_line_utm.buffer(2000).intersection(aoi_utm)
    reach2_3_corridor_wgs84 = gpd.GeoDataFrame(geometry=[reach2_3_corridor_utm], crs="EPSG:32648").to_crs("EPSG:4326").geometry.iloc[0]
    reach2_3_geojson = json.loads(gpd.GeoSeries([reach2_3_corridor_wgs84]).to_json())
    reach2_3_ee_geom = ee.Geometry(reach2_3_geojson['features'][0]['geometry'])
    
    s2_ref_gdf, s2_water_poly = generate_validation_shoreline_s2(year, season, reach2_3_ee_geom, bridge_mask=None)
    if not s2_ref_gdf.empty:
        s2_ref_gdf = s2_ref_gdf[s2_ref_gdf.geometry.intersects(reach2_3_corridor_utm)]
        
    composite_r23 = create_seasonal_composite(year, season, reach2_3_ee_geom)
    training_fc_r23 = load_training_polygons().filterBounds(reach2_3_ee_geom)
    r23_best_params = {'numberOfTrees': 300, 'variablesPerSplit': 3, 'bagFraction': 0.5}
    r23_classifier, _ = train_classifier(training_fc_r23, composite_r23, GLOBAL_FEATURES, r23_best_params)
    
    classified_r23, _ = classify_image(composite_r23.clip(reach2_3_ee_geom), r23_classifier, GLOBAL_FEATURES)
    reach2_3_water = classified_r23.eq(1)
    
    calibrated_water = calibrate_s1_water_mask(reach2_3_water.rename('classification'), composite_r23, s2_ref_gdf)
    water_refined, _, _ = refine_classification(
        calibrated_water, reach2_3_ee_geom, centerline_fc,
        open_radius=SHORELINE_OPEN_SIZE, close_radius=SHORELINE_CLOSE_SIZE
    )
    
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
        raw_gdf = raw_gdf[raw_gdf.geometry.intersects(reach2_3_corridor_utm)]
        
    cleaned_gdf = clean_shoreline_graph(raw_gdf)
    smoothed_gdf, smooth_metrics = smooth_and_simplify_shoreline(cleaned_gdf)
    
    output_dir = "outputs"
    os.makedirs(output_dir, exist_ok=True)
    
    out_s1_path = os.path.join(output_dir, f"shoreline_{year}_{season}_final.geojson")
    out_s2_path = os.path.join(output_dir, f"shoreline_{year}_{season}_s2_ref.geojson")
    
    if not smoothed_gdf.empty:
        smoothed_gdf.to_crs("EPSG:4326").to_file(out_s1_path, driver="GeoJSON")
        print(f"[Phase 7] Saved Reach 2&3 S1 shoreline to: {out_s1_path}")
        
    if not s2_ref_gdf.empty:
        s2_ref_gdf.to_crs("EPSG:4326").to_file(out_s2_path, driver="GeoJSON")
        print(f"[Phase 8] Saved Reach 2&3 S2 reference shoreline to: {out_s2_path}")
        
    val_stats = validate_shoreline(smoothed_gdf, s2_ref_gdf)
    
    stats_summary = {
        'Season': season,
        'Points': val_stats.get('num_points', 0),
        'Mean': round(val_stats.get('mean_distance_m', 0.0), 2),
        'Median': round(val_stats.get('median_distance_m', 0.0), 2),
        'RMSE': round(val_stats.get('rmse_m', 0.0), 2),
        'Hausdorff': round(val_stats.get('hausdorff_distance_m', 0.0), 2),
        'P95': round(val_stats.get('percentile_95_m', 0.0), 2),
        'RuntimeSec': round(time.time() - start_time, 1)
    }
    
    print(f"[{season.upper()} Results] Reach 2&3 Mean={stats_summary['Mean']}m, RMSE={stats_summary['RMSE']}m, P95={stats_summary['P95']}m")
    return stats_summary

def main():
    ee.Initialize(project=GEE_PROJECT)
    run_pipeline_for_reach2_3(year=2024, season='dry')
    run_pipeline_for_reach2_3(year=2024, season='wet')

if __name__ == "__main__":
    main()
