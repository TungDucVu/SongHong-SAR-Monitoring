import sys
import os
import json
import math
import ee
import folium

sys.path.insert(0, os.getcwd())

from src.config import GEE_PROJECT, ASSET_COMPOSITE_TEMPLATE, OUTPUT_DIR
from src.aoi import get_aoi_geometry

def generate_candidates():
    # Initialize GEE
    try:
        ee.Initialize(project=GEE_PROJECT)
        print(f"Earth Engine initialized successfully for project: {GEE_PROJECT}")
    except Exception as e:
        print(f"GEE initialization failed: {e}. Running ee.Authenticate()...")
        ee.Authenticate()
        ee.Initialize(project=GEE_PROJECT)
        
    print("[DATA] Loading 2024 Dry composite and AOI geometry...")
    aoi_geometry = get_aoi_geometry()
    
    # Load composite
    composite_path = ASSET_COMPOSITE_TEMPLATE.format(year=2024, season='dry')
    composite = ee.Image(composite_path)
    
    # Generate 4,000 random candidate points within the AOI
    print("[DATA] Generating 4,000 random candidate points in GEE...")
    candidate_points = ee.FeatureCollection.randomPoints(aoi_geometry, 4000, seed=42)
    
    # Sample the S1 backscatter values
    sampled = composite.select(['VV', 'VH', 'angle']).sampleRegions(
        collection=candidate_points,
        scale=10,
        geometries=True,
        tileScale=4
    )
    
    print("[DATA] Downloading sampled pixel values from GEE...")
    features = sampled.getInfo().get('features', [])
    print(f"[DATA] Downloaded {len(features)} points.")
    
    # Screen candidates
    water_candidates = []
    sandbar_candidates = []
    
    for idx, f in enumerate(features):
        props = f.get('properties', {})
        geom = f.get('geometry', {})
        if not geom or geom.get('type') != 'Point':
            continue
            
        lon, lat = geom.get('coordinates')
        vv = props.get('VV')
        vh = props.get('VH')
        angle = props.get('angle')
        
        if vv is None or vh is None:
            continue
            
        # Water: low VV (specular reflection)
        if vv < -17.5 and vh < -23.0:
            water_candidates.append({
                "type": "Feature",
                "properties": {
                    "id": f"water_candidate_{len(water_candidates)+1}",
                    "class": 0,
                    "className": "Water",
                    "vv": vv,
                    "vh": vh,
                    "angle": angle
                },
                "geometry": {
                    "type": "Point",
                    "coordinates": [lon, lat]
                }
            })
            
        # Sandbar: moderate VV, lower VH
        elif -13.0 < vv < -3.5 and vh < -16.0:
            sandbar_candidates.append({
                "type": "Feature",
                "properties": {
                    "id": f"sandbar_candidate_{len(sandbar_candidates)+1}",
                    "class": 1,
                    "className": "Sandbar",
                    "vv": vv,
                    "vh": vh,
                    "angle": angle
                },
                "geometry": {
                    "type": "Point",
                    "coordinates": [lon, lat]
                }
            })
            
    print(f"[DATA] Screened: {len(water_candidates)} Water candidates, {len(sandbar_candidates)} Sandbar candidates.")
    
    # Merge candidates into single feature collection
    all_candidates = water_candidates + sandbar_candidates
    candidates_geojson = {
        "type": "FeatureCollection",
        "features": all_candidates
    }
    
    # Save to file
    os.makedirs("aoi", exist_ok=True)
    geojson_path = os.path.join("aoi", "candidates.geojson")
    with open(geojson_path, "w", encoding="utf-8") as f:
        json.dump(candidates_geojson, f, indent=2)
    print(f"[DATA] Saved candidates GeoJSON to: {geojson_path}")
    
    # Generate Interactive HTML Map for checking candidates
    print("[MAP] Generating candidates check map HTML...")
    m = folium.Map(location=[21.04, 105.86], zoom_start=11)
    
    # Base: Google Satellite
    folium.TileLayer(
        tiles='https://mt1.google.com/vt/lyrs=s&x={x}&y={y}&z={z}',
        attr='Google',
        name='Google Satellite',
        overlay=False,
        control=True
    ).add_to(m)
    
    # Overlay: Sentinel-1 VV
    map_id_dict = composite.getMapId({'bands': ['VV'], 'min': -22, 'max': -5, 'palette': ['black', 'white']})
    folium.raster_layers.TileLayer(
        tiles=map_id_dict['tile_fetcher'].url_format,
        attr='Google Earth Engine',
        name='Sentinel-1 VV',
        overlay=True,
        control=True,
        opacity=0.5
    ).add_to(m)
    
    # Overlay: Red River AOI Outline
    folium.GeoJson(
        aoi_geometry.getInfo(),
        name="Red River AOI (Hanoi)",
        style_function=lambda x: {'fillColor': 'none', 'color': '#1a73e8', 'weight': 2.0, 'opacity': 0.8}
    ).add_to(m)
    
    # Add Markers for Water candidates
    water_group = folium.FeatureGroup(name="Water Candidates (Blue)")
    for feat in water_candidates:
        coords = feat["geometry"]["coordinates"]
        props = feat["properties"]
        folium.CircleMarker(
            location=[coords[1], coords[0]],
            radius=5,
            color='#0000ff',
            fill=True,
            fill_color='#0000ff',
            fill_opacity=0.8,
            tooltip=f"ID: {props['id']}<br>VV: {props['vv']:.2f} dB<br>VH: {props['vh']:.2f} dB"
        ).add_to(water_group)
    water_group.add_to(m)
    
    # Add Markers for Sandbar candidates
    sandbar_group = folium.FeatureGroup(name="Sandbar Candidates (Yellow)")
    for feat in sandbar_candidates:
        coords = feat["geometry"]["coordinates"]
        props = feat["properties"]
        folium.CircleMarker(
            location=[coords[1], coords[0]],
            radius=5,
            color='#ffd700',
            fill=True,
            fill_color='#ffd700',
            fill_opacity=0.8,
            tooltip=f"ID: {props['id']}<br>VV: {props['vv']:.2f} dB<br>VH: {props['vh']:.2f} dB"
        ).add_to(sandbar_group)
    sandbar_group.add_to(m)
    
    # Add Layer Control
    folium.LayerControl().add_to(m)
    
    # Save the output HTML
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    html_path = os.path.join(OUTPUT_DIR, 'candidates_map.html')
    m.save(html_path)
    print(f"[MAP] Reference candidate map saved to: {html_path}")

if __name__ == "__main__":
    generate_candidates()
