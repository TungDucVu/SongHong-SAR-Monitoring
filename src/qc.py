"""
Quality Control (QC) module for Sentinel-1 Preprocessing Pipeline.
Handles image count validation, backscatter histogram sampling and plotting,
Sentinel-2 validation overlay maps, and metadata logging.
"""

import os
import json
import ee
import folium
import matplotlib.pyplot as plt
import numpy as np
from src.config import (
    OUTPUT_DIR, METADATA_JSON_PATH, WATER_REF_POINT, LAND_REF_POINT,
    EXPECTED_WATER_VV_MAX, EXPECTED_LAND_VV_MIN
)

def update_metadata_json(year, season, stats_dict):
    """
    Logs details of the seasonal composite to outputs/s1_dataset_metadata.json.
    """
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    
    metadata = {}
    if os.path.exists(METADATA_JSON_PATH):
        try:
            with open(METADATA_JSON_PATH, 'r', encoding='utf-8') as f:
                metadata = json.load(f)
        except Exception:
            metadata = {}
            
    key = f"{year}_{season}"
    metadata[key] = stats_dict
    
    with open(METADATA_JSON_PATH, 'w', encoding='utf-8') as f:
        json.dump(metadata, f, indent=2)
    print(f"[QC] Metadata updated for {year} {season} in: {METADATA_JSON_PATH}")

def evaluate_reference_points(composite):
    """
    Evaluates backscatter values at reference coordinates (water and land)
    and returns a verification status report.
    """
    water_pt = ee.Geometry.Point(WATER_REF_POINT)
    land_pt = ee.Geometry.Point(LAND_REF_POINT)
    
    # Sample backscatter values
    water_vals = composite.select(['VV', 'VH']).reduceRegion(
        reducer=ee.Reducer.first(),
        geometry=water_pt,
        scale=10
    ).getInfo()
    
    land_vals = composite.select(['VV', 'VH']).reduceRegion(
        reducer=ee.Reducer.first(),
        geometry=land_pt,
        scale=10
    ).getInfo()
    
    vv_water = water_vals.get('VV')
    vv_land = land_vals.get('VV')
    
    # Assess quality
    water_check = "PASS" if (vv_water is not None and vv_water <= EXPECTED_WATER_VV_MAX) else "FAIL"
    land_check = "PASS" if (vv_land is not None and vv_land >= EXPECTED_LAND_VV_MIN) else "FAIL"
    
    status = "SUCCESS" if (water_check == "PASS" and land_check == "PASS") else "WARNING"
    
    report = {
        "water_ref_vv": vv_water,
        "water_ref_vh": water_vals.get('VH'),
        "water_check": water_check,
        "land_ref_vv": vv_land,
        "land_ref_vh": land_vals.get('VH'),
        "land_check": land_check,
        "status": status
    }
    
    return report

def plot_backscatter_histograms(composite, aoi_geometry, year, season):
    """
    Samples pixel values from the composite within the AOI and plots histograms of VV and VH.
    Saves the plot to outputs/histogram_YYYY_season.png.
    Uses optimized sampling parameters to avoid GEE memory limit exceeded errors.
    """
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    
    # Use coarse scale (150m) and fewer pixels (200) to keep memory footprint very low during on-the-fly Refined Lee computation
    samples = composite.select(['VV', 'VH']).sample(
        region=aoi_geometry,
        scale=150,
        numPixels=200,
        geometries=False
    )
    
    try:
        features = samples.getInfo().get('features', [])
        vv_list = []
        vh_list = []
        
        for f in features:
            props = f.get('properties', {})
            if 'VV' in props and props['VV'] is not None:
                vv_list.append(props['VV'])
            if 'VH' in props and props['VH'] is not None:
                vh_list.append(props['VH'])
                
        if not vv_list:
            print("[QC] No sampled pixels found to plot histogram.")
            return None
            
        fig, axes = plt.subplots(1, 2, figsize=(12, 5))
        
        # Plot VV
        axes[0].hist(vv_list, bins=25, color='#1f77b4', alpha=0.7, edgecolor='black')
        axes[0].set_title(f'VV Backscatter distribution ({year} {season})')
        axes[0].set_xlabel('Backscatter (dB)')
        axes[0].set_ylabel('Pixel Count')
        axes[0].grid(True, linestyle='--', alpha=0.5)
        
        # Plot VH
        axes[1].hist(vh_list, bins=25, color='#ff7f0e', alpha=0.7, edgecolor='black')
        axes[1].set_title(f'VH Backscatter distribution ({year} {season})')
        axes[1].set_xlabel('Backscatter (dB)')
        axes[1].set_ylabel('Pixel Count')
        axes[1].grid(True, linestyle='--', alpha=0.5)
        
        plt.tight_layout()
        plot_path = os.path.join(OUTPUT_DIR, f'histogram_{year}_{season}.png')
        plt.savefig(plot_path, dpi=150)
        plt.close()
        print(f"[QC] Saved histogram plot to: {plot_path}")
        return plot_path
        
    except Exception as e:
        print(f"[QC] Failed to generate histogram: {e}")
        return None

def get_s2_rgb_composite(year, season, aoi_geometry):
    """
    Retrieves a cloud-free Sentinel-2 RGB composite for the specified year, season, and AOI.
    """
    months = [5, 6, 7, 8, 9, 10] if season == 'wet' else [1, 2, 3, 4, 11, 12]
    
    s2_col = (ee.ImageCollection('COPERNICUS/S2_SR_HARMONIZED')
              .filterBounds(aoi_geometry)
              .filter(ee.Filter.calendarRange(months[0], months[-1], 'month'))
              .filterDate(f'{year}-01-01', f'{year}-12-31')
              .filter(ee.Filter.lt('CLOUDY_PIXEL_PERCENTAGE', 25)))
    
    def mask_s2_clouds(img):
        qa = img.select('QA60')
        cloud_bit = 1 << 10
        cirrus_bit = 1 << 11
        mask = qa.bitwiseAnd(cloud_bit).eq(0).And(qa.bitwiseAnd(cirrus_bit).eq(0))
        return img.updateMask(mask)
        
    s2_masked = s2_col.map(mask_s2_clouds)
    # Simple median composite
    s2_median = s2_masked.median().clip(aoi_geometry)
    return s2_median

def create_comparison_map(composite, aoi_geometry, year, season):
    """
    Creates an interactive HTML map comparing the Sentinel-1 SAR composite
    against a cloud-free Sentinel-2 RGB composite.
    Saves the file to outputs/comparison_YYYY_season.html.
    """
    # 1. Get Sentinel-2 RGB image
    s2_img = get_s2_rgb_composite(year, season, aoi_geometry)
    
    # 2. Setup Folium Map centered on Hanoi Red River
    m = folium.Map(location=[21.04, 105.86], zoom_start=11)
    
    # Add Google Satellite Base layer
    folium.TileLayer(
        tiles='https://mt1.google.com/vt/lyrs=s&x={x}&y={y}&z={z}',
        attr='Google',
        name='Google Satellite',
        overlay=False,
        control=True
    ).add_to(m)
    
    # GEE tile layers helper
    def add_ee_layer(folium_map, ee_image_object, vis_params, name):
        map_id_dict = ee.Image(ee_image_object).getMapId(vis_params)
        folium.raster_layers.TileLayer(
            tiles=map_id_dict['tile_fetcher'].url_format,
            attr='Google Earth Engine',
            name=name,
            overlay=True,
            control=True
        ).add_to(folium_map)
        
    # Sentinel-1 VV visualization
    s1_vis = {'bands': ['VV'], 'min': -22, 'max': -5, 'palette': ['black', 'white']}
    add_ee_layer(m, composite, s1_vis, f'Sentinel-1 VV ({year} {season})')
    
    # Sentinel-2 RGB visualization (B4, B3, B2)
    s2_vis = {'bands': ['B4', 'B3', 'B2'], 'min': 0, 'max': 3000}
    try:
        # Check if S2 composite is empty using bandNames() which is valid for ee.Image
        band_names = s2_img.bandNames().getInfo()
        if 'B4' in band_names:
            add_ee_layer(m, s2_img, s2_vis, f'Sentinel-2 RGB ({year} {season})')
            print(f"[QC] Sentinel-2 RGB layer added to map.")
        else:
            print("[QC] No S2 bands found for comparison.")
    except Exception as e:
        print(f"[QC] S2 imagery check failed: {e}")
        
    # Add AOI Outline
    folium.GeoJson(
        aoi_geometry.getInfo(),
        name="Red River AOI (Hanoi)",
        style_function=lambda x: {'fillColor': 'none', 'color': '#1a73e8', 'weight': 2, 'opacity': 0.8}
    ).add_to(m)
    
    folium.LayerControl().add_to(m)
    
    html_path = os.path.join(OUTPUT_DIR, f'comparison_{year}_{season}.html')
    m.save(html_path)
    print(f"[QC] Saved comparison map to: {html_path}")
    return html_path
