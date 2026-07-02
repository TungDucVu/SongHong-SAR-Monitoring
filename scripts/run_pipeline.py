"""
Execution pipeline script for Sentinel-1 Preprocessing.
Supports:
1. Prototype Mode (single year, e.g. 2024): Generates and evaluates seasonal composites with local plots & maps.
2. Production Mode (2017-2026): Submits batch export tasks to save seasonal composites as GEE Assets.
"""

import sys
import os
import time

# Ensure workspace root is in python path
sys.path.insert(0, os.getcwd())

import ee
from src.config import GEE_PROJECT, START_YEAR, END_YEAR, EXPORT_SCALE, EXPORT_CRS, ASSET_COMPOSITE_TEMPLATE
from src.aoi import get_aoi_geometry
from src.collection import create_seasonal_composite
from src.qc import evaluate_reference_points, plot_backscatter_histograms, create_comparison_map, update_metadata_json

def run_prototype(year=2024):
    """
    Runs the prototype phase for a single year.
    Generates local quality control plots, histograms, and interactive map sheets.
    """
    print(f"\n==========================================")
    print(f"       STARTING PROTOTYPE YEAR: {year}")
    print(f"==========================================\n")
    
    # 1. Initialize GEE
    print("[1/5] Initializing Earth Engine...")
    if not ee.data.is_initialized():
        ee.Initialize(project=GEE_PROJECT)
    
    # 2. Get AOI
    print("[2/5] Loading AOI geometry...")
    aoi_geometry = get_aoi_geometry()
    
    # 3. Process Seasons
    seasons = ['dry', 'wet']
    for season in seasons:
        print(f"\n--- Processing {season.upper()} Season {year} ---")
        
        # Generate composite
        print("  Generating median composite (Refined Lee)...")
        composite = create_seasonal_composite(year, season, aoi_geometry)
        
        if composite is None:
            continue
            
        # Run QC reference point checks
        print("  Evaluating quality against reference points...")
        qc_report = evaluate_reference_points(composite)
        print(f"  QC Report Status: {qc_report['status']}")
        print(f"    - Water VV backscatter (expected <= -15dB): {qc_report['water_ref_vv']:.2f} dB ({qc_report['water_check']})")
        print(f"    - Land VV backscatter (expected >= -10dB): {qc_report['land_ref_vv']:.2f} dB ({qc_report['land_check']})")
        
        # Generate histograms
        print("  Sampling pixels and generating backscatter histograms...")
        hist_path = plot_backscatter_histograms(composite, aoi_geometry, year, season)
        
        # Create comparison map
        print("  Creating interactive comparison map (S1 vs S2)...")
        map_path = create_comparison_map(composite, aoi_geometry, year, season)
        
        # Save metadata
        stats_dict = {
            "year": year,
            "season": season,
            "image_count": composite.get('image_count').getInfo(),
            "status": qc_report['status'],
            "water_vv": qc_report['water_ref_vv'],
            "land_vv": qc_report['land_ref_vv'],
            "histogram_plot": os.path.basename(hist_path) if hist_path else None,
            "comparison_map": os.path.basename(map_path) if map_path else None
        }
        update_metadata_json(year, season, stats_dict)

def run_production(start_year=START_YEAR, end_year=END_YEAR):
    """
    Runs the production phase for the entire period (2017-2026).
    Submits batch export tasks to export each seasonal composite to GEE Assets.
    """
    print(f"\n==========================================")
    print(f"   STARTING PRODUCTION RUN ({start_year}-{end_year})")
    print(f"==========================================\n")
    
    # 1. Initialize GEE
    if not ee.data.is_initialized():
        ee.Initialize(project=GEE_PROJECT)
        
    aoi_geometry = get_aoi_geometry()
    
    # Track submitted tasks
    submitted_tasks = []
    
    for year in range(start_year, end_year + 1):
        for season in ['dry', 'wet']:
            asset_path = ASSET_COMPOSITE_TEMPLATE.format(year=year, season=season)
            print(f"\nProcessing {year} {season.upper()} season...")
            
            # Generate composite
            composite = create_seasonal_composite(year, season, aoi_geometry)
            if composite is None:
                continue
                
            # Submit GEE Export task
            task_description = f'Export_S1_{year}_{season}'
            task = ee.batch.Export.image.toAsset(
                image=composite,
                description=task_description,
                assetId=asset_path,
                region=aoi_geometry,
                scale=EXPORT_SCALE,
                crs=EXPORT_CRS,
                maxPixels=1e9
            )
            task.start()
            print(f"  Submitted GEE Export task: {task_description}")
            print(f"  Asset Destination: {asset_path}")
            print(f"  Task ID: {task.id}")
            
            submitted_tasks.append({
                "year": year,
                "season": season,
                "task_id": task.id,
                "asset_path": asset_path
            })
            
    print(f"\n[Production] All {len(submitted_tasks)} export tasks submitted successfully!")
    print("Monitor the tasks at: https://code.earthengine.google.com/tasks")
    return submitted_tasks

if __name__ == '__main__':
    # Default to running the prototype
    run_prototype(2024)
