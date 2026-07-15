import os
import sys
import time
import ee
import geopandas as gpd
import pandas as pd
import folium
from folium.plugins import MousePosition
import shapely

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.config import (
    GEE_PROJECT, CLASSIFIER_FEATURES, OUTPUT_DIR,
    SHORELINE_OPEN_SIZE, SHORELINE_CLOSE_SIZE
)
from src.aoi import get_aoi_geometry, load_local_aoi
from src.collection import create_seasonal_composite
from src.classification import load_training_polygons, train_classifier, classify_image
from src.shoreline import load_centerline, refine_classification, extract_shared_boundary, clean_shoreline_graph

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

def process_season(year, season, aoi_geometry, centerline_fc, training_fc):
    print(f"\n=============================================================")
    print(f" PROCESSING {year} {season.upper()}...")
    print(f"=============================================================")
    
    # 1. Create seasonal composite
    composite = create_seasonal_composite(year, season, aoi_geometry)
    
    # 2. Train RF Classifier
    best_params = {'numberOfTrees': 300, 'variablesPerSplit': 3, 'bagFraction': 0.5}
    classifier, _ = train_classifier(training_fc, composite, CLASSIFIER_FEATURES, best_params)
    
    # 3. Classify composite
    corridor_geom = centerline_fc.geometry().buffer(2000)
    composite_clipped = composite.clip(corridor_geom)
    classified, _ = classify_image(composite_clipped, classifier, CLASSIFIER_FEATURES)
    
    # 4. Refine classification (Single pass)
    water_mask_refined, sand_mask_refined, qc_stats = refine_classification(
        classified, aoi_geometry, centerline_fc,
        open_radius=SHORELINE_OPEN_SIZE,
        close_radius=SHORELINE_CLOSE_SIZE
    )
    
    # 5. Extract Shoreline Boundary (Phase 5)
    scale = 30  # processing scale in meters
    shoreline_gdf, water_dissolved_gdf, metrics = extract_shared_boundary(
        water_mask_refined=water_mask_refined,
        centerline_fc=centerline_fc,
        scale=scale,
        year=year,
        season=season
    )
    
    # 6. QC Validation (Assertions)
    # Checkpoint 5: Verify geometries
    assert not shoreline_gdf.empty, f"[QC Error] Shoreline GDF is empty for {year} {season}!"
    assert shoreline_gdf.geometry.is_valid.all(), f"[QC Error] Invalid geometries found in shoreline GDF!"
    
    # Save raw vector outputs
    out_geojson_path = os.path.join(OUTPUT_DIR, f"shoreline_{year}_{season}_raw.geojson")
    shoreline_gdf.to_file(out_geojson_path, driver="GeoJSON")
    print(f"[Phase 5] Saved raw shoreline GeoJSON to: {out_geojson_path}")
    
    # Save verification metrics
    print(f"[Metrics] Segment count: {metrics['num_segments']}, Total length: {metrics['total_length_m']/1000:.2f} km")
    
    # 7. Graph Cleaning (Phase 6)
    cleaned_gdf = clean_shoreline_graph(shoreline_gdf)
    out_cleaned_geojson_path = os.path.join(OUTPUT_DIR, f"shoreline_{year}_{season}_cleaned.geojson")
    cleaned_gdf.to_file(out_cleaned_geojson_path, driver="GeoJSON")
    print(f"[Phase 6] Saved cleaned shoreline GeoJSON to: {out_cleaned_geojson_path}")
    
    # Initialize map
    m = folium.Map(location=[21.03, 105.85], zoom_start=11, control_scale=True)
    folium.TileLayer('openstreetmap', name='OpenStreetMap').add_to(m)
    folium.TileLayer(
        tiles='https://mt1.google.com/vt/lyrs=s&x={x}&y={y}&z={z}',
        attr='Google',
        name='Google Satellite',
        overlay=False,
        control=True
    ).add_to(m)
    folium.LatLngPopup().add_to(m)
    MousePosition().add_to(m)
    
    # Song Hong AOI outline
    aoi_geojson = load_local_aoi()
    folium.GeoJson(
        aoi_geojson,
        name="Song Hong AOI",
        style_function=lambda x: {'fillColor': 'none', 'color': '#7f8c8d', 'weight': 2.0, 'dashArray': '6, 6'}
    ).add_to(m)
    
    # GEE Refined Water Mask layer (Reprojected to the exact scale used for polygonization)
    water_mask_map = water_mask_refined.reproject(crs='EPSG:32648', scale=scale)
    add_ee_layer(m, water_mask_map.selfMask(), {'palette': ['#2980b9']}, f"Water Mask ({season})", opacity=0.3)
    
    # Centerline buffer corridor outline
    folium.GeoJson(
        corridor_geom.bounds().getInfo(),
        name="2km Centerline Corridor Bounding Box",
        style_function=lambda x: {'fillColor': 'none', 'color': '#d35400', 'weight': 1.5, 'dashArray': '4, 4'}
    ).add_to(m)
    
    # Centerline representation
    centerline_geojson = centerline_fc.getInfo()
    folium.GeoJson(
        centerline_geojson,
        name="Active Centerline",
        style_function=lambda x: {'fillColor': 'none', 'color': '#8e44ad', 'weight': 2.0}
    ).add_to(m)
    
    # Dissolved Main Water Polygon
    if not water_dissolved_gdf.empty:
        water_dissolved_wgs84 = water_dissolved_gdf.to_crs("EPSG:4326")
        folium.GeoJson(
            water_dissolved_wgs84,
            name="Dissolved Main Water Polygon",
            style_function=lambda x: {'fillColor': 'none', 'color': '#2ecc71', 'weight': 1.5, 'dashArray': '3, 3'}
        ).add_to(m)
        
    # Extracted raw shoreline
    if not shoreline_gdf.empty:
        shoreline_wgs84 = shoreline_gdf.to_crs("EPSG:4326")
        
        # Color islands differently from banks
        def style_shoreline(feature):
            is_island = feature['properties']['is_island']
            color = '#e74c3c' if not is_island else '#f1c40f'  # Red for main banks, Yellow for islands
            weight = 1.2 if not is_island else 1.0
            return {'color': color, 'weight': weight, 'opacity': 0.7}
            
        folium.GeoJson(
            shoreline_wgs84,
            name="Raw Shoreline (Red: Banks, Yellow: Islands)",
            style_function=style_shoreline,
            show=False,
            popup=folium.GeoJsonPopup(fields=['id', 'length_m', 'is_island'])
        ).add_to(m)
        
    # Cleaned shoreline (Phase 6)
    if not cleaned_gdf.empty:
        cleaned_wgs84 = cleaned_gdf.to_crs("EPSG:4326")
        
        # Color islands differently from banks
        def style_cleaned_shoreline(feature):
            is_island = feature['properties']['is_island']
            color = '#1abc9c' if not is_island else '#e67e22'  # Teal for main banks, Orange for islands
            weight = 2.0 if not is_island else 1.8
            return {'color': color, 'weight': weight, 'opacity': 1.0}
            
        folium.GeoJson(
            cleaned_wgs84,
            name="Cleaned Shoreline (Teal: Banks, Orange: Islands)",
            style_function=style_cleaned_shoreline,
            popup=folium.GeoJsonPopup(fields=['id', 'length_m', 'is_island'])
        ).add_to(m)
        
    # Key Bridges Markers
    bridges = [
        {"name": "Nhật Tân Bridge", "loc": [21.0825, 105.8236]},
        {"name": "Long Biên Bridge", "loc": [21.0423, 105.8643]},
        {"name": "Vĩnh Tuy Bridge", "loc": [20.9995, 105.8924]},
        {"name": "Thanh Trì Bridge", "loc": [20.9763, 105.9083]}
    ]
    for b in bridges:
        folium.Marker(
            location=b["loc"],
            popup=b["name"],
            icon=folium.Icon(color="blue", icon="info-sign")
        ).add_to(m)
        
    # Legend HTML
    cleaned_len_km = cleaned_gdf.geometry.length.sum() / 1000.0 if not cleaned_gdf.empty else 0.0
    legend_html = f"""
    <div style="position: fixed; 
                bottom: 100px; left: 10px; width: 350px; height: 420px; 
                z-index:9999; font-size:12px; background-color:rgba(255, 255, 255, 0.95);
                border: 2px solid grey; border-radius: 6px; padding: 10px;
                box-shadow: 2px 2px 5px rgba(0,0,0,0.2); font-family: sans-serif;">
        <h4 style="margin: 0 0 8px 0; font-size: 13px; font-weight: bold; text-align: center;">Phase 5 & 6 QC - {season.upper()} Season</h4>
        <div style="display: flex; align-items: center; margin-bottom: 5px;">
            <div style="width: 16px; height: 16px; background-color: #2980b9; opacity: 0.3; margin-right: 8px;"></div>
            <span>Refined GEE Water Mask (Blue)</span>
        </div>
        <div style="display: flex; align-items: center; margin-bottom: 5px;">
            <div style="width: 16px; height: 5px; background-color: #1abc9c; margin-right: 8px;"></div>
            <span style="font-weight: bold; color: #1abc9c;">Cleaned River Banks (Teal)</span>
        </div>
        <div style="display: flex; align-items: center; margin-bottom: 5px;">
            <div style="width: 16px; height: 5px; background-color: #e67e22; margin-right: 8px;"></div>
            <span style="font-weight: bold; color: #e67e22;">Cleaned Islands (Orange)</span>
        </div>
        <div style="display: flex; align-items: center; margin-bottom: 5px;">
            <div style="width: 16px; height: 5px; background-color: #e74c3c; opacity: 0.7; margin-right: 8px;"></div>
            <span style="color: #e74c3c;">Raw River Banks (Red, Hidden)</span>
        </div>
        <div style="display: flex; align-items: center; margin-bottom: 5px;">
            <div style="width: 16px; height: 5px; background-color: #f1c40f; opacity: 0.7; margin-right: 8px;"></div>
            <span style="color: #d4ac0d;">Raw Islands (Yellow, Hidden)</span>
        </div>
        <div style="display: flex; align-items: center; margin-bottom: 5px;">
            <div style="width: 16px; height: 5px; border-top: 2px dashed #2ecc71; margin-right: 8px;"></div>
            <span>Main Water Polygon (Dashed Green)</span>
        </div>
        <div style="display: flex; align-items: center; margin-bottom: 5px;">
            <div style="width: 16px; height: 5px; border-top: 2px dotted #d35400; margin-right: 8px;"></div>
            <span>2km Corridor Bounding Box (Orange)</span>
        </div>
        <div style="display: flex; align-items: center; margin-bottom: 5px;">
            <div style="width: 16px; height: 5px; border-top: 2px dashed #7f8c8d; margin-right: 8px;"></div>
            <span>Song Hong AOI (Dashed Grey)</span>
        </div>
        <div style="display: flex; align-items: center; margin-bottom: 8px;">
            <div style="width: 16px; height: 5px; background-color: #8e44ad; margin-right: 8px;"></div>
            <span>Active Centerline (Purple)</span>
        </div>
        <hr style="margin: 4px 0 6px 0;">
        <div><b>Phase 5 (Raw) Metrics:</b></div>
        <div style="margin-top: 2px;">Segments: <b>{metrics['num_segments']}</b> | Length: <b>{metrics['total_length_m']/1000:.2f} km</b></div>
        <div>QC Passed: <b style="color: {'green' if metrics['qc_passed'] else 'red'};">{'YES' if metrics['qc_passed'] else 'NO'}</b></div>
        <hr style="margin: 4px 0 6px 0;">
        <div><b>Phase 6 (Cleaned) Metrics:</b></div>
        <div style="margin-top: 2px;">Segments: <b>{len(cleaned_gdf)}</b> | Length: <b>{cleaned_len_km:.2f} km</b></div>
    </div>
    """
    m.get_root().html.add_child(folium.Element(legend_html))
    
    # Scale Bar & North Arrow
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
    
    qc_map_path = os.path.join(OUTPUT_DIR, f"phase5_qc_{year}_{season}.html")
    m.save(qc_map_path)
    print(f"[Folium] Saved Phase 5 QC overlay map to: {qc_map_path}")
    return out_geojson_path, qc_map_path

def main():
    if not ee.data.is_initialized():
        ee.Initialize(project=GEE_PROJECT)
    print(f"[GEE] Initialized successfully with project: {GEE_PROJECT}")
    
    aoi_geometry = get_aoi_geometry()
    centerline_fc = load_centerline()
    training_fc = load_training_polygons()
    
    # Process 2024 Dry
    process_season(2024, 'dry', aoi_geometry, centerline_fc, training_fc)
    
    # Process 2024 Wet
    process_season(2024, 'wet', aoi_geometry, centerline_fc, training_fc)
    
    print("\n[Success] Phase 5 processing and QC map generation completed successfully.")

if __name__ == '__main__':
    main()
