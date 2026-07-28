"""
Master Experiment Script for 2024 Dry Shoreline Extraction & Tree Count Tuning [80, 100, 150, 200].

Executes Reach 1, Reach 2, Reach 3 workflows using production specifications from docs/model.md.
Outputs:
- Comparative validation statistics for tree counts [80, 100, 150, 200].
- 3 Separate Interactive HTML Maps (Reach 1, Reach 2, Reach 3).
- Shoreline GeoJSON files & S2 Reference files.
- Strictly DOES NOT generate a combined master shoreline map.
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

def evaluate_reach_output(reach_name, n_trees, year=2024, season='dry'):
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
        'Mean': round(val_stats.get('mean_dist_m', 0.0), 2),
        'Median': round(val_stats.get('median_dist_m', 0.0), 2),
        'RMSE': round(val_stats.get('rmse_dist_m', 0.0), 2),
        'Hausdorff': round(val_stats.get('hausdorff_dist_m', 0.0), 2),
        'P95': round(val_stats.get('p95_dist_m', 0.0), 2),
        **ratings
    }

def main():
    print("=============================================================")
    print(" 2024 DRY SHORELINE EXTRACTION & RF TREE TUNING EXPERIMENT")
    print(" Testing n_trees in [80, 100, 150, 200] across Reach 1, 2, 3")
    print(" Model Specification: docs/model.md")
    print("=============================================================")
    
    ee.Initialize(project=GEE_PROJECT)
    year = 2024
    season = 'dry'
    
    # Load shared assets for Reach 1
    cl_linestring = get_continuous_centerline()
    cl_gdf = gpd.GeoDataFrame(geometry=[cl_linestring], crs="EPSG:4326").to_crs("EPSG:32648")
    centerline_fc = load_centerline()
    
    r1_json = load_reach_aoi(1)
    r1_gdf = gpd.GeoDataFrame.from_features(r1_json['features'], crs="EPSG:4326")
    r1_corridor_utm = r1_gdf.to_crs("EPSG:32648").geometry.union_all()
    r1_ee_geom = ee.Geometry(r1_json['features'][0]['geometry'])
    
    bridges_path = os.path.join(PROJECT_ROOT, 'data', 'bridges.geojson')
    bridges_gdf = load_manual_bridges(bridges_path)
    
    tree_counts = [80, 100, 150, 200]
    experiment_results = []
    
    for n_trees in tree_counts:
        print(f"\n#############################################################")
        print(f" EXPERIMENT ITERATION: n_trees = {n_trees}")
        print(f"#############################################################")
        
        # 1. Run Reach 1
        print(f"\n>>> Running Reach 1 (n_trees={n_trees}) <<<")
        run_pipeline_for_reach1(season=season, reach1_ee_geom=r1_ee_geom, reach1_corridor_utm=r1_corridor_utm, centerline_fc=centerline_fc, bridges_gdf=bridges_gdf, year=year, n_trees=n_trees)
        res1 = evaluate_reach_output('Reach 1', n_trees, year, season)
        experiment_results.append(res1)
        print(f"[Reach 1 | n_trees={n_trees}] Mean={res1['Mean']}m, Median={res1['Median']}m, RMSE={res1['RMSE']}m, Good={res1['Good_pct']}%, Mod={res1['Moderate_pct']}%, Poor={res1['Poor_pct']}%")
        
        # 2. Run Reach 2
        print(f"\n>>> Running Reach 2 (n_trees={n_trees}) <<<")
        run_pipeline_for_reach2(year=year, season=season, n_trees=n_trees)
        res2 = evaluate_reach_output('Reach 2', n_trees, year, season)
        experiment_results.append(res2)
        print(f"[Reach 2 | n_trees={n_trees}] Mean={res2['Mean']}m, Median={res2['Median']}m, RMSE={res2['RMSE']}m, Good={res2['Good_pct']}%, Mod={res2['Moderate_pct']}%, Poor={res2['Poor_pct']}%")
        
        # 3. Run Reach 3
        print(f"\n>>> Running Reach 3 (n_trees={n_trees}) <<<")
        run_pipeline_for_reach3(year=year, season=season, n_trees=n_trees)
        res3 = evaluate_reach_output('Reach 3', n_trees, year, season)
        experiment_results.append(res3)
        print(f"[Reach 3 | n_trees={n_trees}] Mean={res3['Mean']}m, Median={res3['Median']}m, RMSE={res3['RMSE']}m, Good={res3['Good_pct']}%, Mod={res3['Moderate_pct']}%, Poor={res3['Poor_pct']}%")

    # Export overall experiment summary CSV
    season_dir = os.path.join(OUTPUT_DIR, str(year), f"{year}_{season}")
    exp_df = pd.DataFrame(experiment_results)
    exp_csv_path = os.path.join(season_dir, f"rf_tree_tuning_experiment_{year}_{season}.csv")
    exp_df.to_csv(exp_csv_path, index=False)
    print(f"\n[Experiment Summary Saved] -> {exp_csv_path}")

    # Ensure final production run with n_trees = 200 (docs/model.md specification)
    print(f"\n=============================================================")
    print(f" FINAL PRODUCTION RUN (n_trees = 200 per docs/model.md)")
    print(f"=============================================================")
    run_pipeline_for_reach1(season=season, reach1_ee_geom=r1_ee_geom, reach1_corridor_utm=r1_corridor_utm, centerline_fc=centerline_fc, bridges_gdf=bridges_gdf, year=year, n_trees=200)
    run_pipeline_for_reach2(year=year, season=season, n_trees=200)
    run_pipeline_for_reach3(year=year, season=season, n_trees=200)

    print("\n[SUCCESS] 2024 Dry Shoreline Extraction & RF Tuning Experiment Complete!")
    print("Generated 3 Interactive Maps:")
    print(f"  - Reach 1 Map: {os.path.join(season_dir, f'reach1_interactive_map_{year}_{season}.html')}")
    print(f"  - Reach 2 Map: {os.path.join(season_dir, f'reach2_interactive_map_{year}_{season}.html')}")
    print(f"  - Reach 3 Map: {os.path.join(season_dir, f'reach3_interactive_map_{year}_{season}.html')}")
    print("Note: NO Master shoreline map was created.")

if __name__ == "__main__":
    main()
