"""
Verification script for Phase 5: Water-Sand Shared Boundary Extraction.
Runs the GEE-to-local Python vector extraction pipeline on 2024 Dry and Wet composites.
Verifies the output geometries, projection, and generates interactive Folium HTML maps.
"""

import sys
import os
import time
import ee
import folium
import geopandas as gpd
from folium.plugins import MousePosition

# Add project root to python path
sys.path.insert(0, os.getcwd())

from src.config import (
    GEE_PROJECT, CLASSIFIER_FEATURES, OUTPUT_DIR,
    SHORELINE_RAW_DRY_PATH, SHORELINE_RAW_WET_PATH
)
from src.aoi import get_aoi_geometry
from src.collection import create_seasonal_composite
from src.classification import load_training_polygons, train_classifier, classify_image
from src.shoreline import refine_classification, load_centerline, extract_shared_boundary

def main():
    print("="*60)
    print("   PHASE 5 VERIFICATION: SHARED BOUNDARY EXTRACTION   ")
    print("="*60)
    
    # 1. Initialize GEE
    try:
        ee.Initialize(project=GEE_PROJECT)
        print(f"[GEE] Initialized successfully with project: {GEE_PROJECT}")
    except Exception as e:
        print(f"[Error] GEE initialization failed: {e}")
        sys.exit(1)
        
    aoi_geometry = get_aoi_geometry()
    centerline_fc = load_centerline()
    training_fc = load_training_polygons()
    
    # 2. Define seasonal parameters
    dry_features = CLASSIFIER_FEATURES
    wet_features = [f for f in CLASSIFIER_FEATURES if not f.startswith('VH_')]
    
    seasons = {
        'dry': {
            'features': dry_features,
            'params': {
                'numberOfTrees': 300,
                'variablesPerSplit': 3,
                'bagFraction': 0.5
            },
            'output_path': SHORELINE_RAW_DRY_PATH
        },
        'wet': {
            'features': wet_features,
            'params': {
                'numberOfTrees': 100,
                'variablesPerSplit': None,
                'bagFraction': 1.0
            },
            'output_path': SHORELINE_RAW_WET_PATH
        }
    }
    
    # Create outputs directory
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    
    for season, config in seasons.items():
        print(f"\n[Run] Processing 2024 {season.upper()}...")
        composite = create_seasonal_composite(2024, season, aoi_geometry)
        
        # Train RF model
        final_cf, _ = train_classifier(
            training_fc,
            composite,
            config['features'],
            best_params=config['params']
        )
        
        # Clip composite to 2km centerline buffer to restrict feature engineering & classification area
        corridor_geom = centerline_fc.geometry().buffer(2000)
        composite_clipped = composite.clip(corridor_geom)
        
        # Classify entire composite
        classified, _ = classify_image(composite_clipped, final_cf, config['features'])
        
        # Apply Refinement (Phase 4)
        print("[Refinement] Running morphological opening/closing & corridor routing...")
        water_refined, sand_refined, _ = refine_classification(
            classified=classified,
            aoi_geometry=aoi_geometry,
            centerline_fc=centerline_fc,
            open_radius=2,
            close_radius=3
        )
        
        # Apply Boundary Extraction (Phase 5)
        print("[Boundary Extraction] Running polygonization and shared boundary extraction...")
        shoreline_gdf, metrics = extract_shared_boundary(
            classified=classified,
            aoi_geometry=aoi_geometry,
            centerline_fc=centerline_fc,
            scale=30
        )
        
        # Save output GeoJSON
        shoreline_gdf.to_file(config['output_path'], driver='GeoJSON')
        print(f"[Success] Saved raw shoreline to: {config['output_path']}")
        
        # Log Metrics
        print(f"--- Phase 5 Metrics for 2024 {season.upper()} ---")
        print(f"  Execution Time      : {metrics['runtime_seconds']:.2f} seconds")
        print(f"  Total Shoreline Length: {metrics['total_length_m']/1000:.3f} km")
        print(f"  Segments Extracted  : {metrics['num_segments']}")
        print(f"  Invalid Geoms Fixed : {metrics['invalid_geoms_fixed']}")
        print(f"  Closed Loops Removed: {metrics['removed_loops']}")
        
        # Assertions
        assert os.path.exists(config['output_path']), f"Output file does not exist: {config['output_path']}"
        assert shoreline_gdf.crs == "EPSG:32648", f"Output CRS is not EPSG:32648, got: {shoreline_gdf.crs}"
        assert not shoreline_gdf.empty, "Output shoreline GeoDataFrame is empty!"
        assert all(shoreline_gdf.geometry.is_valid), "Output contains invalid geometries!"
        print("[QC PASS] All Phase 5 assertions passed successfully.")
        
        # Create Folium Map
        print("[Map] Rendering raw shoreline verification map...")
        m = folium.Map(location=[21.04, 105.86], zoom_start=11, control_scale=True)
        folium.LatLngPopup().add_to(m)
        MousePosition().add_to(m)
        
        # Google Satellite
        folium.TileLayer(
            tiles='https://mt1.google.com/vt/lyrs=s&x={x}&y={y}&z={z}',
            attr='Google',
            name='Google Satellite',
            overlay=False,
            control=True
        ).add_to(m)
        
        def add_ee_layer(folium_map, ee_image_object, vis_params, name, opacity=1.0, show=True):
            map_id_dict = ee.Image(ee_image_object).getMapId(vis_params)
            folium.raster_layers.TileLayer(
                tiles=map_id_dict['tile_fetcher'].url_format,
                attr='Google Earth Engine',
                name=name,
                overlay=True,
                control=True,
                opacity=opacity,
                show=show
            ).add_to(folium_map)
            
        # S1 VV
        add_ee_layer(m, composite, {'bands': ['VV'], 'min': -22, 'max': -5, 'palette': ['black', 'white']}, 
                     'Sentinel-1 VV Backscatter', opacity=0.45, show=False)
        
        # Refined Water mask (Blue)
        add_ee_layer(m, water_refined.selfMask(), {'palette': ['0000ff']}, 
                     'Refined Water Mask', opacity=0.35, show=True)
        
        # Refined Sand mask (Orange)
        add_ee_layer(m, sand_refined.selfMask(), {'palette': ['ff8c00']}, 
                     'Refined Sand Mask', opacity=0.35, show=True)
        
        # Add centerline
        folium.GeoJson(
            centerline_fc.getInfo(),
            name="OSM Red River Centerline",
            style_function=lambda x: {'color': '#e74c3c', 'weight': 2.0, 'dashArray': '5, 5'}
        ).add_to(m)
        
        # Add Extracted Raw Shoreline (Reprojected back to WGS 84 for Folium rendering)
        shoreline_wgs84 = shoreline_gdf.to_crs("EPSG:4326")
        folium.GeoJson(
            shoreline_wgs84,
            name="Extracted Raw Shoreline (Phase 5)",
            style_function=lambda x: {'color': '#e74c3c', 'weight': 2.5}
        ).add_to(m)
        
        # Legend HTML
        legend_html = f"""
        <div style="position: fixed; 
                    bottom: 100px; left: 10px; width: 260px; height: 230px; 
                    z-index:9999; font-size:12px; background-color:rgba(255, 255, 255, 0.9);
                    border: 2px solid grey; border-radius: 6px; padding: 10px;
                    box-shadow: 2px 2px 5px rgba(0,0,0,0.2); font-family: sans-serif;">
            <h4 style="margin: 0 0 8px 0; font-size: 13px; font-weight: bold; text-align: center;">Raw Shoreline (2024 {season.upper()})</h4>
            <div style="display: flex; align-items: center; margin-bottom: 5px;">
                <div style="width: 16px; height: 16px; background-color: #0000ff; opacity: 0.35; border: 1px solid #000; margin-right: 8px;"></div>
                <span>Refined Water Mask</span>
            </div>
            <div style="display: flex; align-items: center; margin-bottom: 5px;">
                <div style="width: 16px; height: 16px; background-color: #ff8c00; opacity: 0.35; border: 1px solid #000; margin-right: 8px;"></div>
                <span>Refined Sand Mask</span>
            </div>
            <div style="display: flex; align-items: center; margin-bottom: 5px;">
                <div style="width: 16px; height: 3px; background-color: #e74c3c; margin-right: 8px;"></div>
                <span>Raw Shoreline Polyline</span>
            </div>
            <div style="display: flex; align-items: center; margin-bottom: 8px;">
                <div style="width: 16px; height: 3px; border-top: 2px dashed #e74c3c; margin-right: 8px;"></div>
                <span>OSM Centerline</span>
            </div>
            <hr style="margin: 4px 0 6px 0;">
            <div>Total Length: <b>{metrics['total_length_m']/1000:.3f} km</b></div>
            <div>Segments: <b>{metrics['num_segments']}</b></div>
            <div>Loops Removed: <b>{metrics['removed_loops']}</b></div>
        </div>
        """
        m.get_root().html.add_child(folium.Element(legend_html))
        
        # North Arrow
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
        
        html_path = os.path.join(OUTPUT_DIR, f'shoreline_raw_2024_{season}.html')
        m.save(html_path)
        print(f"[QC] Saved raw shoreline verification map to: {html_path}")
        
    print("\n[Success] Completed verification runs for Phase 5!")

if __name__ == '__main__':
    main()
