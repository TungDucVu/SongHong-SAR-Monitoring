"""
Script to expand Random Forest training polygons by identifying spatial hotspots from validation outliers,
automatically labeling them via Sentinel-2 NDWI/NDVI/NDBI in Earth Engine, and appending them to training_polygons.geojson.
"""

import os
import json
import shutil
import geopandas as gpd
from shapely.geometry import Polygon, Point
import ee
import numpy as np

import sys
# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Load configurations
from src.config import GEE_PROJECT, TRAINING_POLYGONS_PATH, OUTPUT_DIR, AOI_GEOJSON_PATH

def initialize_ee():
    print(f"Initializing Earth Engine with project: {GEE_PROJECT}")
    try:
        ee.Initialize(project=GEE_PROJECT)
    except Exception as e:
        print(f"EE Initialize failed: {e}. Attempting default authorization...")
        ee.Authenticate()
        ee.Initialize()

def load_outliers():
    dry_path = os.path.join(OUTPUT_DIR, "validation_outliers_2024_dry.geojson")
    wet_path = os.path.join(OUTPUT_DIR, "validation_outliers_2024_wet.geojson")
    
    outliers = []
    if os.path.exists(dry_path):
        print(f"Loading dry season outliers from: {dry_path}")
        outliers.append(gpd.read_file(dry_path))
    else:
        print(f"[Warning] Dry season outliers file not found: {dry_path}")
        
    if os.path.exists(wet_path):
        print(f"Loading wet season outliers from: {wet_path}")
        outliers.append(gpd.read_file(wet_path))
    else:
        print(f"[Warning] Wet season outliers file not found: {wet_path}")
        
    if not outliers:
        raise FileNotFoundError("No outlier GeoJSON files found. Run the extraction pipeline first.")
        
    combined = gpd.GeoDataFrame(gpd.pd.concat(outliers, ignore_index=True), crs=outliers[0].crs)
    print(f"Loaded {len(combined)} total outlier points.")
    return combined

def extract_hotspots(outliers_gdf, min_dist_m=200.0, max_hotspots=100):
    """
    Performs greedy spatial thinning in UTM projection (EPSG:32648)
    to select well-distributed hotspot points that are at least min_dist_m apart.
    """
    print(f"Performing greedy spatial thinning (min distance: {min_dist_m}m)...")
    # Reproject to UTM Zone 48N
    outliers_utm = outliers_gdf.to_crs("EPSG:32648")
    
    # Sort outliers by distance descending to prioritize largest errors
    outliers_utm = outliers_utm.sort_values(by='distance', ascending=False)
    
    selected_pts = []
    selected_distances = []
    
    for idx, row in outliers_utm.iterrows():
        pt = row.geometry
        if not isinstance(pt, Point):
            continue
            
        # Check distance to all already selected points
        too_close = False
        for s_pt in selected_pts:
            if pt.distance(s_pt) < min_dist_m:
                too_close = True
                break
                
        if not too_close:
            selected_pts.append(pt)
            selected_distances.append(row['distance'])
            if len(selected_pts) >= max_hotspots:
                break
                
    print(f"Selected {len(selected_pts)} spatially distributed hotspot coordinates.")
    
    # Create GeoDataFrame in UTM
    hotspots_gdf = gpd.GeoDataFrame({
        'geometry': selected_pts,
        'outlier_distance': selected_distances
    }, crs="EPSG:32648")
    
    return hotspots_gdf

def build_s2_composite(aoi_geom):
    """
    Builds a cloud-free annual median Sentinel-2 composite for 2024
    and computes spectral indices.
    """
    s2_col = (ee.ImageCollection('COPERNICUS/S2_SR_HARMONIZED')
              .filterBounds(aoi_geom)
              .filterDate('2024-01-01', '2024-12-31')
              .filter(ee.Filter.lt('CLOUDY_PIXEL_PERCENTAGE', 25)))
              
    def mask_clouds(img):
        qa = img.select('QA60')
        cloud_bit = 1 << 10
        cirrus_bit = 1 << 11
        mask = qa.bitwiseAnd(cloud_bit).eq(0).And(qa.bitwiseAnd(cirrus_bit).eq(0))
        return img.updateMask(mask)
        
    s2_masked = s2_col.map(mask_clouds)
    s2_median = s2_masked.median()
    
    # Compute indices
    ndwi = s2_median.normalizedDifference(['B3', 'B8']).rename('NDWI')
    ndvi = s2_median.normalizedDifference(['B8', 'B4']).rename('NDVI')
    ndbi = s2_median.normalizedDifference(['B11', 'B8']).rename('NDBI')
    
    composite = s2_median.select(['B3', 'B4', 'B8', 'B11']).addBands([ndwi, ndvi, ndbi])
    return composite

def label_hotspots(hotspots_gdf, aoi_geom):
    """
    Generates 30m x 30m training polygons, queries S2 indices in Earth Engine,
    and assigns class labels (1: Water, 2: Sand, 3: Built-up, 4: Vegetation).
    """
    print("Generating 30m x 30m polygons and querying Sentinel-2 spectral indices in Earth Engine...")
    s2_composite = build_s2_composite(aoi_geom)
    
    labeled_features = []
    
    # Convert hotspots back to WGS84 for geojson extraction
    hotspots_wgs = hotspots_gdf.to_crs("EPSG:4326")
    hotspots_utm = hotspots_gdf
    
    for idx, (row_wgs, row_utm) in enumerate(zip(hotspots_wgs.itertuples(), hotspots_utm.itertuples())):
        # Generate 30m x 30m square buffer in UTM
        # buffer(15, cap_style=3) creates a square with side length 30m
        poly_utm = row_utm.geometry.buffer(15, cap_style=3)
        
        # Reproject square to WGS84
        poly_wgs = gpd.GeoSeries([poly_utm], crs="EPSG:32648").to_crs("EPSG:4326").iloc[0]
        
        # Convert coordinates to EE Polygon
        coords = [list(pt) for pt in poly_wgs.exterior.coords]
        ee_geom = ee.Geometry.Polygon([coords])
        
        # Query median values over polygon
        try:
            stats = s2_composite.reduceRegion(
                reducer=ee.Reducer.median(),
                geometry=ee_geom,
                scale=10,
                maxPixels=1e6
            ).getInfo()
        except Exception as e:
            print(f"[Warning] Failed to query GEE for hotspot {idx}: {e}")
            stats = {}
            
        ndwi = stats.get('NDWI')
        ndvi = stats.get('NDVI')
        ndbi = stats.get('NDBI')
        
        # Classify based on spectral signatures
        if ndwi is None or ndvi is None:
            label_class = 2  # default fallback
            label_name = "Sand"
        elif ndwi > 0.05:
            label_class = 1
            label_name = "Water"
        elif ndvi > 0.18:
            label_class = 4
            label_name = "Vegetation"
        else:
            if ndbi is not None and ndbi > 0.0:
                label_class = 3
                label_name = "Built-up"
            else:
                label_class = 2
                label_name = "Sand"
                
        print(f"  Hotspot {idx+1}/{len(hotspots_gdf)}: (Lat: {row_wgs.geometry.y:.5f}, Lon: {row_wgs.geometry.x:.5f}) -> {label_name} (Class {label_class}) [NDWI: {ndwi if ndwi else 'N/A':.3f}, NDVI: {ndvi if ndvi else 'N/A':.3f}, NDBI: {ndbi if ndbi else 'N/A':.3f}]")
        
        labeled_features.append({
            "type": "Feature",
            "geometry": {
                "geodesic": False,
                "type": "Polygon",
                "coordinates": [ [ [pt[0], pt[1]] for pt in coords ] ]
            },
            "id": f"added_hotspot_{idx}",
            "properties": {
                "class": label_class,
                "className": label_name,
                "id": f"{label_class}_new_{idx}"
            }
        })
        
    return labeled_features

def append_to_training_polygons(new_features):
    # Load original training polygons
    print(f"Loading existing training polygons from: {TRAINING_POLYGONS_PATH}")
    with open(TRAINING_POLYGONS_PATH, 'r') as f:
        training_fc = json.load(f)
        
    # Backup original training polygons
    backup_path = TRAINING_POLYGONS_PATH.replace(".geojson", "_backup.geojson")
    shutil.copyfile(TRAINING_POLYGONS_PATH, backup_path)
    print(f"Created backup of original training polygons at: {backup_path}")
    
    # Append new features
    if 'features' not in training_fc:
        training_fc['features'] = []
        
    original_count = len(training_fc['features'])
    training_fc['features'].extend(new_features)
    new_count = len(training_fc['features'])
    
    # Save back
    with open(TRAINING_POLYGONS_PATH, 'w') as f:
        json.dump(training_fc, f, indent=2)
        
    print(f"Successfully appended {len(new_features)} new hotspot training polygons.")
    print(f"Total training polygons expanded: {original_count} -> {new_count}")

def main():
    initialize_ee()
    
    # Load AOI geometry for S2 composite filtering
    with open(AOI_GEOJSON_PATH, 'r') as f:
        aoi_data = json.load(f)
        aoi_geom = ee.Geometry(aoi_data['features'][0]['geometry'])
        
    outliers_gdf = load_outliers()
    hotspots_gdf = extract_hotspots(outliers_gdf, min_dist_m=200.0, max_hotspots=100)
    
    if len(hotspots_gdf) == 0:
        print("[Info] No outlier hotspots found to expand.")
        return
        
    new_features = label_hotspots(hotspots_gdf, aoi_geom)
    append_to_training_polygons(new_features)
    print("[SUCCESS] Training set expanded. Now re-run the shoreline pipeline to train with updated polygons.")

if __name__ == "__main__":
    main()
