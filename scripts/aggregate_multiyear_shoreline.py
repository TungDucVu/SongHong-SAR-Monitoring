"""
Multi-Year Shoreline Aggregation & Master Folium Map Generator (2017 - 2026)

Combines all extracted Sentinel-1 seasonal shorelines across 2017-2026,
generates a master GeoJSON dataset, and renders an interactive multi-temporal
Folium HTML visualization.
"""

import os
import sys
import glob
import json
import numpy as np
import pandas as pd
import geopandas as gpd
import folium
from folium.plugins import MousePosition

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(PROJECT_ROOT)

from src.config import OUTPUT_DIR
from src.aoi import load_local_aoi
from src.shoreline import get_continuous_centerline

# Color palette for 2017-2026 timeline
YEAR_COLORS = {
    2017: '#1f77b4',  # Deep Blue
    2018: '#00a896',  # Teal
    2019: '#2ec4b6',  # Light Turquoise
    2020: '#20bf6b',  # Green
    2021: '#f7b731',  # Gold / Yellow
    2022: '#fa8231',  # Orange
    2023: '#eb3b5a',  # Red-Orange
    2024: '#8e44ad',  # Purple
    2025: '#d63031',  # Crimson
    2026: '#6c5ce7'   # Violet
}

def aggregate_shorelines(start_year=2017, end_year=2026):
    print(f"[Aggregation] Searching for shoreline files in outputs/ ({start_year}-{end_year})...")
    
    gdfs = []
    
    for yr in range(start_year, end_year + 1):
        for ssn in ['dry', 'wet']:
            file_candidates = [
                os.path.join(OUTPUT_DIR, str(yr), f"{yr}_{ssn}", f"shoreline_{yr}_{ssn}_final.geojson"),
                os.path.join(OUTPUT_DIR, f"shoreline_{yr}_{ssn}_final.geojson"),
                os.path.join(OUTPUT_DIR, "others", f"shoreline_s1_{yr}_{ssn}.geojson")
            ]

            found = False
            for fpath in file_candidates:
                if os.path.exists(fpath):
                    try:
                        gdf = gpd.read_file(fpath)
                        gdf['year'] = yr
                        gdf['season'] = ssn
                        gdfs.append(gdf)
                        print(f"  Loaded: {yr} {ssn.upper()} ({len(gdf)} segments from {os.path.basename(fpath)})")
                        found = True
                        break
                    except Exception as e:
                        print(f"  [Warning] Could not read {fpath}: {e}")
            if not found:
                print(f"  [Missing] {yr} {ssn.upper()}")
                
    if not gdfs:
        print("[Error] No shoreline vector files found!")
        return None
        
    master_gdf = pd.concat(gdfs, ignore_index=True)
    master_gdf = gpd.GeoDataFrame(master_gdf, crs="EPSG:32648")
    
    others_dir = os.path.join(OUTPUT_DIR, 'others')
    os.makedirs(others_dir, exist_ok=True)
    master_output_path = os.path.join(others_dir, "shorelines_2017_2026_master.geojson")
    master_gdf.to_file(master_output_path, driver="GeoJSON")
    print(f"[Aggregation] Saved master shoreline GeoJSON: {master_output_path} ({len(master_gdf)} total segments)")
    
    return master_gdf

def generate_multitemporal_map(master_gdf):
    print("[Folium] Creating Master Multi-Temporal Map (2017-2026)...")
    
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
    
    # Add AOI
    try:
        aoi_geojson = load_local_aoi()
        folium.GeoJson(
            aoi_geojson,
            name="Song Hong AOI Corridor",
            style_function=lambda x: {'fillColor': 'none', 'color': '#7f8c8d', 'weight': 2.0, 'dashArray': '6, 6'}
        ).add_to(m)
    except Exception as e:
        print(f"  [Warning] Could not load AOI: {e}")
        
    # Add Continuous Centerline
    try:
        cl_linestring = get_continuous_centerline()
        cl_gdf = gpd.GeoDataFrame(geometry=[cl_linestring], crs="EPSG:4326").to_crs("EPSG:32648")
        cl_wgs84 = cl_gdf.to_crs("EPSG:4326")
        folium.GeoJson(
            cl_wgs84,
            name="Continuous Centerline (171.84 km)",
            style_function=lambda x: {'fillColor': 'none', 'color': '#2c3e50', 'weight': 2.5}
        ).add_to(m)
    except Exception as e:
        print(f"  [Warning] Could not load centerline: {e}")

    # Add Shoreline layers grouped by Year & Season
    years = sorted(master_gdf['year'].unique())
    
    for yr in years:
        yr_color = YEAR_COLORS.get(yr, '#34495e')
        yr_fg = folium.FeatureGroup(name=f"Shorelines {yr}", show=(yr in [2017, 2024, 2026]))
        
        yr_gdf = master_gdf[master_gdf['year'] == yr]
        yr_wgs84 = yr_gdf.to_crs("EPSG:4326")
        
        def make_style(color, ssn):
            dash = '5, 5' if ssn == 'wet' else None
            weight = 2.2 if ssn == 'dry' else 1.8
            return lambda x: {'color': color, 'weight': weight, 'opacity': 0.9, 'dashArray': dash}

        folium.GeoJson(
            yr_wgs84,
            style_function=make_style(yr_color, 'dry'),
            popup=folium.GeoJsonPopup(fields=['id', 'year', 'season', 'bank_type', 'length_m'])
        ).add_to(yr_fg)
        
        yr_fg.add_to(m)
        
    # Dashboard Legend HTML
    legend_entries = "".join([
        f'''<div style="display: flex; align-items: center; margin-bottom: 4px;">
            <div style="width: 18px; height: 4px; background-color: {YEAR_COLORS.get(y, "#333")}; margin-right: 8px;"></div>
            <span><b>{y}</b> Shoreline</span>
        </div>''' for y in years
    ])
    
    legend_html = f"""
    <div style="position: fixed; 
                bottom: 50px; left: 10px; width: 320px; height: 380px; 
                z-index:9999; font-size:12px; background-color:rgba(255, 255, 255, 0.95);
                border: 2px solid grey; border-radius: 6px; padding: 10px;
                box-shadow: 2px 2px 5px rgba(0,0,0,0.2); font-family: sans-serif;">
        <h4 style="margin: 0 0 8px 0; font-size: 13px; font-weight: bold; text-align: center;">Master Multi-Temporal Shoreline Overlay (2017–2026)</h4>
        <div style="margin-bottom: 8px; font-size: 11px; color: #555;">
            Solid lines = Dry Season | Dashed lines = Wet Season
        </div>
        <hr style="margin: 4px 0 8px 0;">
        {legend_entries}
        <hr style="margin: 8px 0 4px 0;">
        <div style="font-size: 11px; color: #2c3e50;">
            Total Vector Segments: <b>{len(master_gdf)}</b><br>
            Time Span: <b>2017 – 2026 (10 Years)</b>
        </div>
    </div>
    """
    m.get_root().html.add_child(folium.Element(legend_html))
    
    folium.LayerControl(collapsed=False).add_to(m)
    
    map_dir = os.path.join(OUTPUT_DIR, 'others')
    os.makedirs(map_dir, exist_ok=True)
    map_output_path = os.path.join(map_dir, "master_multitemporal_shoreline_2017_2026.html")
    m.save(map_output_path)
    print(f"[Folium] Saved Master Multi-Temporal Map: {map_output_path}")


def main():
    master_gdf = aggregate_shorelines(2017, 2026)
    if master_gdf is not None:
        generate_multitemporal_map(master_gdf)

if __name__ == '__main__':
    main()
