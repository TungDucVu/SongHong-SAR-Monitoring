"""
Utility and validation module for SongHong SAR Monitoring.
Handles HTML map output, CSV/JSON reporting, and backscatter validations.
"""

import os
import csv
import json
import ee
from datetime import datetime
from src.config import (
    OUTPUT_DIR, EXPORT_CRS, EXPORT_SCALE, 
    EXPECTED_WATER_VV_MAX, EXPECTED_LAND_VV_MIN
)

def get_output_path(filename):
    """
    Returns absolute path for a filename in output directory.
    Creates outputs/ directory if it doesn't exist.
    """
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    return os.path.join(OUTPUT_DIR, filename)

def save_interactive_map(map_object, filename):
    """
    Saves a geemap.Map object to an interactive HTML file in outputs directory.
    """
    out_path = get_output_path(filename)
    map_object.to_html(out_path)
    print(f"[Map] Saved interactive map to: {out_path}")
    return out_path

def save_stats_to_csv(data, filename, fieldnames):
    """
    Saves a list of dicts to a CSV file in the outputs directory.
    """
    out_path = get_output_path(filename)
    with open(out_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(data)
    print(f"[Stats] Saved CSV report to: {out_path}")
    return out_path

def save_stats_to_json(data, filename):
    """
    Saves a dictionary to a JSON file in the outputs directory.
    """
    out_path = get_output_path(filename)
    with open(out_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    print(f"[Stats] Saved JSON report to: {out_path}")
    return out_path



def verify_backscatter_values(composite, water_pt_coords, land_pt_coords):
    """
    Validates backscatter values at reference water and land coordinates.
    
    Args:
        composite: ee.Image processed monthly composite.
        water_pt_coords: list [lon, lat].
        land_pt_coords: list [lon, lat].
        
    Returns:
        dict containing mean band values for both points and validation results.
    """
    water_point = ee.Geometry.Point(water_pt_coords)
    land_point = ee.Geometry.Point(land_pt_coords)
    
    # Extract mean values in a 100m buffer
    water_val = composite.reduceRegion(
        reducer=ee.Reducer.mean(),
        geometry=water_point.buffer(100),
        scale=EXPORT_SCALE
    ).getInfo()
    
    land_val = composite.reduceRegion(
        reducer=ee.Reducer.mean(),
        geometry=land_point.buffer(100),
        scale=EXPORT_SCALE
    ).getInfo()
    
    # Run thresholds check
    water_vv = water_val.get('VV', 0.0)
    land_vv = land_val.get('VV', 0.0)
    
    water_ok = water_vv < EXPECTED_WATER_VV_MAX if water_vv is not None else False
    land_ok = land_vv > EXPECTED_LAND_VV_MIN if land_vv is not None else False
    
    print(f"\n[Validation] Backscatter Validation Check:")
    print(f"   Water Point VV: {water_vv:.2f} dB (Expected < {EXPECTED_WATER_VV_MAX} dB) -> {'PASSED' if water_ok else 'WARNING'}")
    print(f"   Land Point VV : {land_vv:.2f} dB (Expected > {EXPECTED_LAND_VV_MIN} dB) -> {'PASSED' if land_ok else 'WARNING'}")
    
    return {
        'timestamp': datetime.utcnow().isoformat() + 'Z',
        'water_point': {
            'coordinates': water_pt_coords,
            'VV': water_vv,
            'VH': water_val.get('VH'),
            'ratio': water_val.get('VV_VH_ratio'),
            'validation_passed': water_ok
        },
        'land_point': {
            'coordinates': land_pt_coords,
            'VV': land_vv,
            'VH': land_val.get('VH'),
            'ratio': land_val.get('VV_VH_ratio'),
            'validation_passed': land_ok
        }
    }
