"""
Generate Separate Reach Maps (Reach 1, Reach 2, Reach 3) for 2024 Dry & Wet
Generates both:
1. Interactive Folium HTML maps (reach1, reach2, reach3 separately for Dry & Wet)
2. High-resolution publication-grade PNG map figures (reach1_dry.png, reach1_wet.png, reach2_dry.png, reach2_wet.png, reach3_dry.png, reach3_wet.png)
"""

import os
import sys
import geopandas as gpd
import numpy as np
import folium
from folium.plugins import MousePosition
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from shapely.geometry import Point

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(PROJECT_ROOT)

from src.aoi import load_reach_aoi
from src.shoreline import get_continuous_centerline, validate_shoreline

def build_interactive_reach_map(reach_num, year=2024, season='dry'):
    reach_name = f"Reach {reach_num}"
    season_dir = os.path.join(PROJECT_ROOT, "outputs", str(year), f"{year}_{season}")
    
    s1_path = os.path.join(season_dir, f"reach{reach_num}_s1_shoreline_{year}_{season}.geojson")
    s2_path = os.path.join(season_dir, f"reach{reach_num}_s2_ref_{year}_{season}.geojson")
    
    if not os.path.exists(s1_path):
        s1_path = os.path.join(PROJECT_ROOT, "outputs", "others", f"reach{reach_num}_s1_shoreline_{year}_{season}.geojson")
    if not os.path.exists(s2_path):
        s2_path = os.path.join(PROJECT_ROOT, "outputs", "others", f"reach{reach_num}_s2_ref_{year}_{season}.geojson")
        
    if not os.path.exists(s1_path) or not os.path.exists(s2_path):
        print(f"  [Skip HTML] Missing GeoJSON files for {reach_name} ({year} {season})")
        return
        
    s1_gdf = gpd.read_file(s1_path).to_crs("EPSG:4326")
    s2_gdf = gpd.read_file(s2_path).to_crs("EPSG:4326")
    
    reach_json = load_reach_aoi(reach_num)
    reach_gdf = gpd.GeoDataFrame.from_features(reach_json['features'], crs="EPSG:4326")
    centroid = reach_gdf.geometry.iloc[0].centroid
    center_lat, center_lon = centroid.y, centroid.x
    
    m = folium.Map(location=[center_lat, center_lon], zoom_start=11, control_scale=True)
    folium.TileLayer('openstreetmap', name='OpenStreetMap').add_to(m)
    folium.TileLayer(
        tiles='https://mt1.google.com/vt/lyrs=s&x={x}&y={y}&z={z}',
        attr='Google Satellite',
        name='Google Satellite',
        overlay=False,
        control=True
    ).add_to(m)
    folium.LatLngPopup().add_to(m)
    MousePosition().add_to(m)
    
    # Display AOI Corridor
    folium.GeoJson(
        reach_gdf,
        name=f"AOI Corridor - {reach_name}",
        style_function=lambda x: {'fillColor': 'none', 'color': '#f39c12', 'weight': 2.5, 'dashArray': '6, 6'}
    ).add_to(m)
    
    # Display Centerline
    cl_linestring = get_continuous_centerline()
    cl_gdf = gpd.GeoDataFrame(geometry=[cl_linestring], crs="EPSG:4326")
    folium.GeoJson(
        cl_gdf,
        name="Continuous River Centerline",
        style_function=lambda x: {'fillColor': 'none', 'color': '#8e44ad', 'weight': 2.0}
    ).add_to(m)
    
    # Display S2 Reference (Red Dashed)
    folium.GeoJson(
        s2_gdf,
        name="Sentinel-2 NDWI Reference Shoreline (Red)",
        style_function=lambda x: {'color': '#e74c3c', 'weight': 2.0, 'dashArray': '4, 4', 'opacity': 0.85}
    ).add_to(m)
    
    # Display S1 RF Shoreline (Cyan Solid)
    folium.GeoJson(
        s1_gdf,
        name=f"Sentinel-1 SAR Shoreline ({reach_name})",
        style_function=lambda x: {'color': '#00d2d3', 'weight': 3.0, 'opacity': 0.95}
    ).add_to(m)
    
    s1_utm = gpd.read_file(s1_path)
    s2_utm = gpd.read_file(s2_path)
    val_stats = validate_shoreline(s1_utm, s2_utm)
    med_m = val_stats.get('median_dist_m', 0.0)
    mean_m = val_stats.get('mean_dist_m', 0.0)
    rmse_m = val_stats.get('rmse_dist_m', 0.0)
    p95_m = val_stats.get('p95_dist_m', 0.0)
    
    legend_html = f"""
    <div style="position: fixed; 
                bottom: 30px; left: 10px; width: 340px; 
                z-index:9999; font-size:12px; background-color:rgba(255, 255, 255, 0.95);
                border: 2px solid #2c3e50; border-radius: 8px; padding: 12px;
                box-shadow: 2px 2px 6px rgba(0,0,0,0.3); font-family: sans-serif;">
        <h4 style="margin: 0 0 8px 0; font-size: 14px; font-weight: bold; text-align: center; color: #2c3e50;">
            {reach_name} ({year} {season.upper()}) Shoreline Map
        </h4>
        <div style="margin-bottom: 6px; font-size: 11px; background: #ecf0f1; padding: 6px; border-radius: 4px;">
            <b>Performance Metrics (vs S2 Reference):</b><br>
            • Median Error (P50): <b>{med_m:.2f} m</b><br>
            • Mean Distance: <b>{mean_m:.2f} m</b><br>
            • RMSE: <b>{rmse_m:.2f} m</b><br>
            • 95th Percentile: <b>{p95_m:.2f} m</b>
        </div>
        <div style="display: flex; align-items: center; margin-bottom: 5px;">
            <div style="width: 20px; height: 3px; background-color: #00d2d3; margin-right: 8px;"></div>
            <span><b>Sentinel-1 SAR Shoreline</b></span>
        </div>
        <div style="display: flex; align-items: center; margin-bottom: 5px;">
            <div style="width: 20px; height: 3px; background-color: #e74c3c; border-top: 1px dashed #e74c3c; margin-right: 8px;"></div>
            <span>Sentinel-2 NDWI Reference</span>
        </div>
        <div style="display: flex; align-items: center; margin-bottom: 5px;">
            <div style="width: 20px; height: 3px; background-color: #8e44ad; margin-right: 8px;"></div>
            <span>River Centerline</span>
        </div>
    </div>
    """
    m.get_root().html.add_child(folium.Element(legend_html))
    folium.LayerControl(collapsed=False).add_to(m)
    
    # Save HTML output to season dir and outputs/maps/
    out_html = os.path.join(season_dir, f"reach{reach_num}_interactive_map_{year}_{season}.html")
    others_map_dir = os.path.join(PROJECT_ROOT, "outputs", "others", "map")
    os.makedirs(others_map_dir, exist_ok=True)
    others_html = os.path.join(others_map_dir, f"reach{reach_num}_interactive_map_{year}_{season}.html")
    
    m.save(out_html)
    m.save(others_html)
    print(f"  [OK HTML] Saved Reach {reach_num} ({season.upper()}) interactive map.")

def build_static_reach_png(reach_num, year=2024, season='dry'):
    reach_name = f"Reach {reach_num}"
    season_dir = os.path.join(PROJECT_ROOT, "outputs", str(year), f"{year}_{season}")
    fig_dir = os.path.join(PROJECT_ROOT, "outputs", "REPORT", "figures")
    os.makedirs(fig_dir, exist_ok=True)
    
    s1_path = os.path.join(season_dir, f"reach{reach_num}_s1_shoreline_{year}_{season}.geojson")
    s2_path = os.path.join(season_dir, f"reach{reach_num}_s2_ref_{year}_{season}.geojson")
    
    if not os.path.exists(s1_path):
        s1_path = os.path.join(PROJECT_ROOT, "outputs", "others", f"reach{reach_num}_s1_shoreline_{year}_{season}.geojson")
    if not os.path.exists(s2_path):
        s2_path = os.path.join(PROJECT_ROOT, "outputs", "others", f"reach{reach_num}_s2_ref_{year}_{season}.geojson")
        
    if not os.path.exists(s1_path) or not os.path.exists(s2_path):
        print(f"  [Skip PNG] Missing GeoJSON files for {reach_name} ({year} {season})")
        return

    s1_gdf = gpd.read_file(s1_path).to_crs("EPSG:32648")
    s2_gdf = gpd.read_file(s2_path).to_crs("EPSG:32648")
    
    reach_json = load_reach_aoi(reach_num)
    reach_gdf = gpd.GeoDataFrame.from_features(reach_json['features'], crs="EPSG:4326").to_crs("EPSG:32648")
    
    fig, ax = plt.subplots(figsize=(10, 7), dpi=300)
    
    # Plot AOI corridor
    reach_gdf.plot(ax=ax, facecolor='none', edgecolor='#f39c12', linewidth=1.5, linestyle='--', label='AOI Corridor Boundary')
    
    # Plot S2 Reference
    s2_gdf.plot(ax=ax, color='#e74c3c', linewidth=1.8, linestyle=':', alpha=0.85, label='Sentinel-2 NDWI Reference')
    
    # Plot S1 RF Shoreline
    s1_gdf.plot(ax=ax, color='#16a085', linewidth=2.2, alpha=0.95, label='Sentinel-1 SAR Extracted Shoreline')
    
    val_stats = validate_shoreline(s1_gdf, s2_gdf)
    med_m = val_stats.get('median_dist_m', 0.0)
    rmse_m = val_stats.get('rmse_dist_m', 0.0)
    
    ax.set_title(f'Song Hong Shoreline Extraction - {reach_name} ({year} {season.upper()})\nMedian Error = {med_m:.2f} m | RMSE = {rmse_m:.2f} m', fontsize=12, fontweight='bold', pad=12)
    ax.set_xlabel('UTM Easting (m)', fontsize=10, fontweight='bold')
    ax.set_ylabel('UTM Northing (m)', fontsize=10, fontweight='bold')
    ax.legend(loc='upper right', frameon=True, facecolor='white', framealpha=0.9, fontsize=9)
    ax.grid(True, linestyle=':', alpha=0.6)
    
    plt.tight_layout()
    
    # Save PNG figure into REPORT/figures/ and season directory
    out_png_report = os.path.join(fig_dir, f"reach{reach_num}_{season}.png")
    out_png_season = os.path.join(season_dir, f"reach{reach_num}_{season}.png")
    
    fig.savefig(out_png_report)
    fig.savefig(out_png_season)
    plt.close(fig)
    print(f"  [OK PNG] Saved Reach {reach_num} ({season.upper()}) static PNG map figure.")

def main():
    print("=============================================================")
    print(" GENERATING SEPARATE MAPS FOR REACH 1, 2, 3 (2024 DRY & WET)")
    print("=============================================================")
    
    for yr in [2024]:
        for ssn in ['dry', 'wet']:
            for r in [1, 2, 3]:
                build_interactive_reach_map(r, yr, ssn)
                build_static_reach_png(r, yr, ssn)
                
    print("\n[SUCCESS] ALL SEPARATE 2024 REACH MAPS GENERATED SUCCESSFULLY!")

if __name__ == "__main__":
    main()
