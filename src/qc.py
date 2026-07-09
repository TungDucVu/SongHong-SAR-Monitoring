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
    WATER_REF_POLYGON, LAND_REF_POLYGON,
    WATER_REF_POLYGONS, LAND_REF_POLYGONS,
    EXPECTED_WATER_VV_MAX, EXPECTED_WATER_VH_MAX, EXPECTED_LAND_VV_MIN,
    PROJECT_ROOT
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
    Evaluates backscatter values at reference coordinates/polygons (water and land)
    and returns a verification status report.
    Uses spatial mean over reference polygons to be robust against pixel-level noise.
    
    Soft Range Validation: Issues warnings but does not halt execution if values
    are outside expected thresholds.
    """
    # Create FeatureCollections for water and land polygon lists
    water_features = [ee.Feature(ee.Geometry.Polygon(p)) for p in WATER_REF_POLYGONS]
    water_fc = ee.FeatureCollection(water_features)
    
    land_features = [ee.Feature(ee.Geometry.Polygon(p)) for p in LAND_REF_POLYGONS]
    land_fc = ee.FeatureCollection(land_features)
    
    # Calculate mean backscatter values (scale=10 to preserve Sentinel-1 resolution)
    water_stats = composite.select(['VV', 'VH']).reduceRegions(
        collection=water_fc,
        reducer=ee.Reducer.mean(),
        scale=10
    ).filter(ee.Filter.notNull(['VV', 'VH'])).getInfo()
    
    land_stats = composite.select(['VV', 'VH']).reduceRegions(
        collection=land_fc,
        reducer=ee.Reducer.mean(),
        scale=10
    ).filter(ee.Filter.notNull(['VV', 'VH'])).getInfo()
    
    # Aggregate statistics
    water_vv_list = [f['properties']['VV'] for f in water_stats.get('features', [])]
    water_vh_list = [f['properties']['VH'] for f in water_stats.get('features', [])]
    land_vv_list = [f['properties']['VV'] for f in land_stats.get('features', [])]
    land_vh_list = [f['properties']['VH'] for f in land_stats.get('features', [])]
    
    vv_water = sum(water_vv_list) / len(water_vv_list) if water_vv_list else None
    vh_water = sum(water_vh_list) / len(water_vh_list) if water_vh_list else None
    vv_land = sum(land_vv_list) / len(land_vv_list) if land_vv_list else None
    vh_land = sum(land_vh_list) / len(land_vh_list) if land_vh_list else None
    
    # Check for NaN/None which are hard failures
    import math
    for val, name in [(vv_water, "Water VV"), (vh_water, "Water VH"), (vv_land, "Land VV")]:
        if val is None or math.isnan(val) or math.isinf(val):
            raise ValueError(f"QC FAILED: Invalid pixel value {val} detected in {name} reference polygon.")
            
    # Soft quality checks (warnings only)
    water_check = "PASS" if vv_water <= EXPECTED_WATER_VV_MAX else "WARNING"
    land_check = "PASS" if vv_land >= EXPECTED_LAND_VV_MIN else "WARNING"
    
    status = "SUCCESS" if (water_check == "PASS" and land_check == "PASS") else "WARNING"
    
    report = {
        "water_ref_vv": vv_water,
        "water_ref_vh": vh_water,
        "water_check": water_check,
        "land_ref_vv": vv_land,
        "land_ref_vh": vh_land,
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

def get_s2_metadata(year, season, aoi_geometry):
    """
    Retrieves image count and dates list for Sentinel-2 collection of the given year/season.
    """
    s2_col = (ee.ImageCollection('COPERNICUS/S2_SR_HARMONIZED')
              .filterBounds(aoi_geometry)
              .filterDate(f'{year}-01-01', f'{year}-12-31')
              .filter(ee.Filter.lt('CLOUDY_PIXEL_PERCENTAGE', 25)))
              
    if season == 'dry':
        s2_col = s2_col.filter(ee.Filter.Or(
            ee.Filter.calendarRange(1, 4, 'month'),
            ee.Filter.calendarRange(11, 12, 'month')
        ))
    elif season == 'wet':
        s2_col = s2_col.filter(ee.Filter.calendarRange(5, 10, 'month'))
              
    try:
        s2_dates = s2_col.aggregate_array('system:time_start').map(
            lambda t: ee.Date(t).format('YYYY-MM-dd')
        ).getInfo()
        s2_dates_sorted = sorted(list(set(s2_dates)))
        return {
            'count': len(s2_dates_sorted),
            'dates': s2_dates_sorted
        }
    except Exception as e:
        print(f"[Warning] Failed to fetch Sentinel-2 metadata: {e}")
        return {
            'count': 0,
            'dates': []
        }

def get_s2_rgb_composite(year, season, aoi_geometry):
    """
    Retrieves a cloud-free Sentinel-2 RGB composite for the specified year, season, and AOI.
    """
    s2_col = (ee.ImageCollection('COPERNICUS/S2_SR_HARMONIZED')
              .filterBounds(aoi_geometry)
              .filterDate(f'{year}-01-01', f'{year}-12-31')
              .filter(ee.Filter.lt('CLOUDY_PIXEL_PERCENTAGE', 25)))
              
    if season == 'dry':
        s2_col = s2_col.filter(ee.Filter.Or(
            ee.Filter.calendarRange(1, 4, 'month'),
            ee.Filter.calendarRange(11, 12, 'month')
        ))
    elif season == 'wet':
        s2_col = s2_col.filter(ee.Filter.calendarRange(5, 10, 'month'))
              
    # Fetch, deduplicate, and print S2 image dates
    s2_info = get_s2_metadata(year, season, aoi_geometry)
    print(f"\nSentinel-2 {season.capitalize()}")
    print(f"Images: {s2_info['count']}")
    for d in s2_info['dates']:
        print(f"  {d}")
    
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
    
    Includes mandatory elements: LayerControl, Legend, Scale Bar, North Arrow,
    and Click Coordinate popup.
    """
    from folium.plugins import MousePosition
    
    # 1. Get Sentinel-2 RGB image
    s2_img = get_s2_rgb_composite(year, season, aoi_geometry)
    
    # 2. Setup Folium Map centered on Hanoi Red River with native scale control enabled
    m = folium.Map(location=[21.04, 105.86], zoom_start=11, control_scale=True)
    
    # Add coordinate popup on click
    folium.LatLngPopup().add_to(m)
    
    # Add mouse position tracker
    MousePosition().add_to(m)
    
    # Add Google Satellite Base layer
    folium.TileLayer(
        tiles='https://mt1.google.com/vt/lyrs=s&x={x}&y={y}&z={z}',
        attr='Google',
        name='Google Satellite',
        overlay=False,
        control=True
    ).add_to(m)
    
    # GEE tile layers helper
    def add_ee_layer(folium_map, ee_image_object, vis_params, name, opacity=1.0):
        map_id_dict = ee.Image(ee_image_object).getMapId(vis_params)
        folium.raster_layers.TileLayer(
            tiles=map_id_dict['tile_fetcher'].url_format,
            attr='Google Earth Engine',
            name=name,
            overlay=True,
            control=True,
            opacity=opacity
        ).add_to(folium_map)
        
    # 1. Sentinel-2 RGB visualization (B4, B3, B2) - added first to be at the bottom
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

    # 2. Sentinel-1 VV visualization - added second so it sits above Sentinel-2 RGB layer
    s1_vis = {'bands': ['VV'], 'min': -22, 'max': -5, 'palette': ['black', 'white']}
    add_ee_layer(m, composite, s1_vis, f'Sentinel-1 VV ({year} {season})', opacity=0.45)
        
    # Add AOI Outline
    folium.GeoJson(
        aoi_geometry.getInfo(),
        name="Red River AOI (Hanoi)",
        style_function=lambda x: {'fillColor': 'none', 'color': '#1a73e8', 'weight': 2, 'opacity': 0.8}
    ).add_to(m)
    
    # Add Hanoi Boundary
    hanoi_geojson_path = os.path.join(PROJECT_ROOT, 'aoi', 'hanoi_boundary.geojson')
    if os.path.exists(hanoi_geojson_path):
        try:
            with open(hanoi_geojson_path, 'r', encoding='utf-8') as f:
                hanoi_data = json.load(f)
            folium.GeoJson(
                hanoi_data,
                name="Hanoi Boundary",
                style_function=lambda x: {'fillColor': 'none', 'color': '#ff3300', 'weight': 2.5, 'dashArray': '5, 5', 'opacity': 0.8}
            ).add_to(m)
            print("[QC] Added Hanoi Boundary layer to map.")
        except Exception as e:
            print(f"[QC] Failed to add Hanoi Boundary: {e}")
            
    # Add custom HTML/CSS floating legend
    legend_html = f'''
    <div style="position: fixed; 
                bottom: 100px; left: 10px; width: 220px; height: 160px; 
                z-index:9999; font-size:12px; background-color:rgba(255, 255, 255, 0.9);
                border: 2px solid grey; border-radius: 6px; padding: 10px;
                box-shadow: 2px 2px 5px rgba(0,0,0,0.2); font-family: sans-serif;">
        <h4 style="margin: 0 0 8px 0; font-size: 14px; font-weight: bold; text-align: center;">QC Map Legend ({year} {season})</h4>
        <div style="display: flex; align-items: center; margin-bottom: 6px;">
            <div style="width: 18px; height: 18px; background-color: #1a73e8; border: 1px solid #000; margin-right: 8px;"></div>
            <span>Red River AOI (Hanoi)</span>
        </div>
        <div style="display: flex; align-items: center; margin-bottom: 6px;">
            <div style="width: 18px; height: 0px; border-top: 2px dashed #ff3300; margin-right: 8px;"></div>
            <span>Hanoi Province Boundary</span>
        </div>
        <div style="display: flex; align-items: center; margin-bottom: 6px;">
            <div style="width: 18px; height: 18px; background: linear-gradient(to right, black, white); border: 1px solid #000; margin-right: 8px;"></div>
            <span>S1 VV Backscatter (-22 to -5 dB)</span>
        </div>
        <div style="display: flex; align-items: center;">
            <div style="width: 18px; height: 18px; background-color: #2ca02c; border: 1px solid #000; margin-right: 8px;"></div>
            <span>S2 RGB Composite</span>
        </div>
    </div>
    '''
    m.get_root().html.add_child(folium.Element(legend_html))
    
    # Add custom HTML/CSS North Arrow
    north_arrow_html = '''
    <div style="position: fixed; 
                bottom: 50px; left: 10px; width: 40px; height: 40px; 
                z-index:9999; font-size:16px; background-color:rgba(255, 255, 255, 0.8);
                border: 2px solid grey; border-radius: 4px; padding: 2px;
                text-align: center; font-weight: bold; line-height: 38px; font-family: sans-serif;">
        N ↑
    </div>
    '''
    m.get_root().html.add_child(folium.Element(north_arrow_html))
    
    folium.LayerControl().add_to(m)
    
    html_path = os.path.join(OUTPUT_DIR, f'comparison_{year}_{season}.html')
    m.save(html_path)
    print(f"[QC] Saved comparison map to: {html_path}")
    return html_path

def create_contrast_map(composite, aoi_geometry, year, season):
    """
    Creates an interactive HTML map visualizing the Sentinel-1 VV_contrast texture feature.
    Saves the file to outputs/contrast_map_YYYY_season.html.
    """
    from folium.plugins import MousePosition
    
    # 1. Get Sentinel-2 RGB image
    s2_img = get_s2_rgb_composite(year, season, aoi_geometry)
    
    # 2. Setup Folium Map centered on Hanoi Red River with scale control
    m = folium.Map(location=[21.04, 105.86], zoom_start=11, control_scale=True)
    
    # Add click coordinate popup
    folium.LatLngPopup().add_to(m)
    
    # Add mouse position tracker
    MousePosition().add_to(m)
    
    # Add Google Satellite Base layer
    folium.TileLayer(
        tiles='https://mt1.google.com/vt/lyrs=s&x={x}&y={y}&z={z}',
        attr='Google',
        name='Google Satellite',
        overlay=False,
        control=True
    ).add_to(m)
    
    # GEE tile layers helper
    def add_ee_layer(folium_map, ee_image_object, vis_params, name, opacity=1.0):
        map_id_dict = ee.Image(ee_image_object).getMapId(vis_params)
        folium.raster_layers.TileLayer(
            tiles=map_id_dict['tile_fetcher'].url_format,
            attr='Google Earth Engine',
            name=name,
            overlay=True,
            control=True,
            opacity=opacity
        ).add_to(folium_map)

    # 1. Sentinel-2 RGB layer (added first at bottom)
    s2_vis = {'bands': ['B4', 'B3', 'B2'], 'min': 0, 'max': 3000}
    try:
        band_names = s2_img.bandNames().getInfo()
        if 'B4' in band_names:
            add_ee_layer(m, s2_img, s2_vis, f'Sentinel-2 RGB ({year} {season})')
    except Exception as e:
        print(f"[QC] S2 imagery check failed: {e}")

    # 2. Sentinel-1 VV_contrast layer
    contrast_vis = {
        'bands': ['VV_contrast'],
        'min': 0,
        'max': 800,
        'palette': ['blue', 'green', 'yellow', 'orange', 'red']
    }
    add_ee_layer(m, composite, contrast_vis, f'S1 VV Contrast Texture ({year} {season})', opacity=0.6)

    # Add AOI Outline
    folium.GeoJson(
        aoi_geometry.getInfo(),
        name="Red River AOI (Hanoi)",
        style_function=lambda x: {'fillColor': 'none', 'color': '#1a73e8', 'weight': 2, 'opacity': 0.8}
    ).add_to(m)
    
    # Add Hanoi Boundary
    hanoi_geojson_path = os.path.join(PROJECT_ROOT, 'aoi', 'hanoi_boundary.geojson')
    if os.path.exists(hanoi_geojson_path):
        try:
            with open(hanoi_geojson_path, 'r', encoding='utf-8') as f:
                hanoi_data = json.load(f)
            folium.GeoJson(
                hanoi_data,
                name="Hanoi Boundary",
                style_function=lambda x: {'fillColor': 'none', 'color': '#ff3300', 'weight': 2.5, 'dashArray': '5, 5', 'opacity': 0.8}
            ).add_to(m)
        except Exception as e:
            print(f"[QC] Failed to add Hanoi Boundary: {e}")

    # Add Legend
    legend_html = f'''
    <div style="position: fixed; 
                bottom: 100px; left: 10px; width: 220px; height: 165px; 
                z-index:9999; font-size:12px; background-color:rgba(255, 255, 255, 0.9);
                border: 2px solid grey; border-radius: 6px; padding: 10px;
                box-shadow: 2px 2px 5px rgba(0,0,0,0.2); font-family: sans-serif;">
        <h4 style="margin: 0 0 8px 0; font-size: 14px; font-weight: bold; text-align: center;">VV Contrast Legend ({year} {season})</h4>
        <div style="display: flex; align-items: center; margin-bottom: 6px;">
            <div style="width: 18px; height: 18px; background-color: #1a73e8; border: 1px solid #000; margin-right: 8px;"></div>
            <span>Red River AOI (Hanoi)</span>
        </div>
        <div style="display: flex; align-items: center; margin-bottom: 6px;">
            <div style="width: 18px; height: 0px; border-top: 2px dashed #ff3300; margin-right: 8px;"></div>
            <span>Hanoi Province Boundary</span>
        </div>
        <div style="display: flex; align-items: center; margin-bottom: 6px;">
            <div style="width: 18px; height: 18px; background: linear-gradient(to right, blue, green, yellow, orange, red); border: 1px solid #000; margin-right: 8px;"></div>
            <span>VV Contrast (0 to 800)</span>
        </div>
        <div style="display: flex; align-items: center;">
            <div style="width: 18px; height: 18px; background-color: #2ca02c; border: 1px solid #000; margin-right: 8px;"></div>
            <span>S2 RGB Composite</span>
        </div>
    </div>
    '''
    m.get_root().html.add_child(folium.Element(legend_html))

    # Add North Arrow
    north_arrow_html = '''
    <div style="position: fixed; 
                bottom: 50px; left: 10px; width: 40px; height: 40px; 
                z-index:9999; font-size:16px; background-color:rgba(255, 255, 255, 0.8);
                border: 2px solid grey; border-radius: 4px; padding: 2px;
                text-align: center; font-weight: bold; line-height: 38px; font-family: sans-serif;">
        N ↑
    </div>
    '''
    m.get_root().html.add_child(folium.Element(north_arrow_html))

    folium.LayerControl().add_to(m)
    
    html_path = os.path.join(OUTPUT_DIR, f'contrast_map_{year}_{season}.html')
    m.save(html_path)
    print(f"[QC] Saved contrast map to: {html_path}")
    return html_path

