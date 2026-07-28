"""
Execution script to run 2024 WET Season Shoreline Extraction across all 3 Reaches using 50-Tree RF.
Evaluates positional validation metrics (Mean, RMSE, P95, Hausdorff) against S2 NDWI reference.
"""

import os
import sys
import json
import time
import geopandas as gpd
import pandas as pd
import numpy as np
import ee

if sys.platform == 'win32':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')
    except Exception:
        pass

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(PROJECT_ROOT)

from src.config import GEE_PROJECT, OUTPUT_DIR
from src.aoi import load_reach_aoi
from src.shoreline import get_continuous_centerline, load_centerline, load_manual_bridges, validate_shoreline
from main_workflow.run_reach1_local import run_pipeline_for_reach1
from main_workflow.run_reach2_local import run_pipeline_for_reach2
from main_workflow.run_reach3_local import run_pipeline_for_reach3
from scripts.generate_interactive_maps_50trees import build_reach_map

def calc_rating_breakdown(distances):
    if len(distances) == 0:
        return {'Good_pct': 0.0, 'Moderate_pct': 0.0, 'Poor_pct': 0.0, 'Good_cnt': 0, 'Moderate_cnt': 0, 'Poor_cnt': 0, 'Total_pts': 0}
    
    good_cnt = int(np.sum(distances <= 30.0))
    mod_cnt = int(np.sum((distances > 30.0) & (distances <= 70.0)))
    poor_cnt = int(np.sum(distances > 70.0))
    total = len(distances)
    
    return {
        'Good_pct': round((good_cnt / total) * 100.0, 2),
        'Moderate_pct': round((mod_cnt / total) * 100.0, 2),
        'Poor_pct': round((poor_cnt / total) * 100.0, 2),
        'Good_cnt': good_cnt,
        'Moderate_cnt': mod_cnt,
        'Poor_cnt': poor_cnt,
        'Total_pts': total
    }

def evaluate_reach_output(reach_name, n_trees, year=2024, season='wet'):
    season_dir = os.path.join(OUTPUT_DIR, str(year), f"{year}_{season}")
    s1_path = os.path.join(season_dir, f"{reach_name.lower().replace(' ', '')}_s1_shoreline_{year}_{season}.geojson")
    s2_path = os.path.join(season_dir, f"{reach_name.lower().replace(' ', '')}_s2_ref_{year}_{season}.geojson")
    
    if not os.path.exists(s1_path) or not os.path.exists(s2_path):
        return {'Reach': reach_name, 'n_trees': n_trees, 'Mean': 0.0, 'Median': 0.0, 'RMSE': 0.0, 'Hausdorff': 0.0, 'P95': 0.0, 'Good_pct': 0.0, 'Moderate_pct': 0.0, 'Poor_pct': 0.0}
        
    s1_gdf = gpd.read_file(s1_path)
    s2_gdf = gpd.read_file(s2_path)
    
    val_stats = validate_shoreline(s1_gdf, s2_gdf)
    dists = val_stats.get('distances', np.array([]))
    ratings = calc_rating_breakdown(dists)
    
    return {
        'Reach': reach_name,
        'n_trees': n_trees,
        'Points': val_stats.get('num_points', 0),
        'Min': round(float(np.min(dists)) if len(dists)>0 else 0.0, 2),
        'Median': round(val_stats.get('median_dist_m', 0.0), 2),
        'Mean': round(val_stats.get('mean_dist_m', 0.0), 2),
        'RMSE': round(val_stats.get('rmse_dist_m', 0.0), 2),
        'P95': round(val_stats.get('p95_dist_m', 0.0), 2),
        'Hausdorff': round(val_stats.get('hausdorff_dist_m', 0.0), 2),
        **ratings
    }

def main():
    print("=============================================================")
    print(" 2024 WET SEASON SHORELINE EXTRACTION EXPERIMENT: n_trees = 50")
    print("=============================================================")
    
    ee.Initialize(project=GEE_PROJECT)
    year = 2024
    season = 'wet'
    n_trees = 50
    
    cl_linestring = get_continuous_centerline()
    cl_gdf = gpd.GeoDataFrame(geometry=[cl_linestring], crs="EPSG:4326").to_crs("EPSG:32648")
    centerline_fc = load_centerline()
    
    r1_json = load_reach_aoi(1)
    r1_gdf = gpd.GeoDataFrame.from_features(r1_json['features'], crs="EPSG:4326")
    r1_corridor_utm = r1_gdf.to_crs("EPSG:32648").geometry.union_all()
    r1_ee_geom = ee.Geometry(r1_json['features'][0]['geometry'])
    
    bridges_path = os.path.join(PROJECT_ROOT, 'data', 'bridges.geojson')
    bridges_gdf = load_manual_bridges(bridges_path)
    
    print(f"\n>>> Running Reach 1 (2024 WET, n_trees={n_trees}) <<<")
    run_pipeline_for_reach1(season=season, reach1_ee_geom=r1_ee_geom, reach1_corridor_utm=r1_corridor_utm, centerline_fc=centerline_fc, bridges_gdf=bridges_gdf, year=year, n_trees=n_trees, generate_map=False)
    res1 = evaluate_reach_output('Reach 1', n_trees, year, season)
    
    print(f"\n>>> Running Reach 2 (2024 WET, n_trees={n_trees}) <<<")
    run_pipeline_for_reach2(year=year, season=season, n_trees=n_trees, generate_map=False)
    res2 = evaluate_reach_output('Reach 2', n_trees, year, season)
    
    print(f"\n>>> Running Reach 3 (2024 WET, n_trees={n_trees}) <<<")
    run_pipeline_for_reach3(year=year, season=season, n_trees=n_trees, generate_map=False)
    res3 = evaluate_reach_output('Reach 3', n_trees, year, season)
    
    print("\n=============================================================")
    print(f" EXPERIMENT RESULTS FOR 2024 WET (n_trees = 50)")
    print("=============================================================")
    for res in [res1, res2, res3]:
        print(f"\n--- {res['Reach']} (2024 WET, n_trees=50) ---")
        print(f"  Points: {res['Points']}")
        print(f"  Min: {res['Min']} m | Median: {res['Median']} m | Mean: {res['Mean']} m")
        print(f"  RMSE: {res['RMSE']} m | P95: {res['P95']} m | Hausdorff: {res['Hausdorff']} m")
        print(f"  Rating: Good(<=30m): {res['Good_pct']}% ({res['Good_cnt']} pts) | Mod(30-70m): {res['Moderate_pct']}% ({res['Moderate_cnt']} pts) | Poor(>70m): {res['Poor_pct']}% ({res['Poor_cnt']} pts)")

    print("\n[Done] 2024 WET 50-tree extraction complete (Fast Mode - No Map).")

if __name__ == "__main__":
    main()
