"""
Generate Interactive Folium Maps for 50-Tree RF Shoreline Outputs (2024 Dry)
Reads local GeoJSON vector files for Reach 1, Reach 2, and Reach 3 and builds HTML maps.
"""

import os
import sys
import geopandas as gpd
import folium
from folium.plugins import MousePosition

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(PROJECT_ROOT)

from src.aoi import load_local_aoi, load_reach_aoi
from src.shoreline import get_continuous_centerline, validate_shoreline

def build_reach_map(reach_num, year=2024, season='dry'):
    reach_name = f"Reach {reach_num}"
    print(f"[Folium] Building interactive map for {reach_name} ({year} {season.upper()} - 50 Trees)...")
    
    season_dir = os.path.join(PROJECT_ROOT, "outputs", str(year), f"{year}_{season}")
    s1_path = os.path.join(season_dir, f"reach{reach_num}_s1_shoreline_{year}_{season}.geojson")
    s2_path = os.path.join(season_dir, f"reach{reach_num}_s2_ref_{year}_{season}.geojson")
    
    if not os.path.exists(s1_path) or not os.path.exists(s2_path):
        print(f"  [Error] Missing GeoJSON files for {reach_name}")
        return
        
    s1_gdf = gpd.read_file(s1_path).to_crs("EPSG:4326")
    s2_gdf = gpd.read_file(s2_path).to_crs("EPSG:4326")
    
    # Calculate map center from Reach AOI
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
    
    # Load and display AOI
    folium.GeoJson(
        reach_gdf,
        name=f"AOI Corridor - {reach_name}",
        style_function=lambda x: {'fillColor': 'none', 'color': '#f39c12', 'weight': 2.0, 'dashArray': '6, 6'}
    ).add_to(m)
    
    # Display Centerline
    cl_linestring = get_continuous_centerline()
    cl_gdf = gpd.GeoDataFrame(geometry=[cl_linestring], crs="EPSG:4326")
    folium.GeoJson(
        cl_gdf,
        name="Continuous River Centerline",
        style_function=lambda x: {'fillColor': 'none', 'color': '#8e44ad', 'weight': 2.0}
    ).add_to(m)
    
    # Display S2 Reference Shoreline (Red Dashed)
    folium.GeoJson(
        s2_gdf,
        name="Sentinel-2 NDWI Reference Shoreline (Red Line)",
        style_function=lambda x: {'color': '#e74c3c', 'weight': 2.0, 'dashArray': '4, 4', 'opacity': 0.85}
    ).add_to(m)
    
    # Display S1 RF 50-Trees Shoreline (Cyan Solid)
    folium.GeoJson(
        s1_gdf,
        name=f"Sentinel-1 SAR Shoreline (50 Trees RF - {reach_name})",
        style_function=lambda x: {'color': '#00d2d3', 'weight': 3.0, 'opacity': 0.95}
    ).add_to(m)
    
    # Validation metrics & error markers
    s1_utm = gpd.read_file(s1_path)
    s2_utm = gpd.read_file(s2_path)
    val_stats = validate_shoreline(s1_utm, s2_utm)
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
            {reach_name} Interactive Shoreline Map (50 Trees)
        </h4>
        <div style="margin-bottom: 6px; font-size: 11px; background: #ecf0f1; padding: 6px; border-radius: 4px;">
            <b>Performance Metrics (vs S2 Reference):</b><br>
            • Mean Distance: <b>{mean_m:.2f} m</b><br>
            • RMSE: <b>{rmse_m:.2f} m</b><br>
            • 95th Percentile: <b>{p95_m:.2f} m</b>
        </div>
        <div style="display: flex; align-items: center; margin-bottom: 5px;">
            <div style="width: 20px; height: 3px; background-color: #00d2d3; margin-right: 8px;"></div>
            <span><b>Sentinel-1 SAR Shoreline (50 Trees)</b></span>
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
    
    # Save outputs
    out_html = os.path.join(season_dir, f"reach{reach_num}_interactive_map_{year}_{season}.html")
    others_map_dir = os.path.join(PROJECT_ROOT, "outputs", "others", "map")
    os.makedirs(others_map_dir, exist_ok=True)
    others_html = os.path.join(others_map_dir, f"reach{reach_num}_interactive_map_{year}_{season}.html")
    
    m.save(out_html)
    m.save(others_html)
    print(f"  [Saved] {out_html}")

def main():
    print("=============================================================")
    print(" GENERATING 50-TREE INTERACTIVE MAPS FOR REACH 1, 2, AND 3")
    print("=============================================================")
    for r in [1, 2, 3]:
        build_reach_map(r, 2024, 'dry')
    print("\n[Complete] All 3 reach interactive maps generated successfully!")

if __name__ == "__main__":
    main()
