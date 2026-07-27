import os
import sys
import geopandas as gpd
import folium
from folium.plugins import MousePosition

# Add project root to sys.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from src.shoreline import validate_shoreline

def find_file(filename, year, season):
    search_paths = [
        os.path.join("outputs", str(year), f"{year}_{season.lower()}", filename),
        os.path.join("outputs", "others", filename),
        os.path.join("outputs", filename),
    ]
    for p in search_paths:
        if os.path.exists(p):
            return p
    return None

def plot_hybrid_map(year, season, output_path=None):
    season_lower = season.lower()
    print(f"Generating unified Hybrid 3-Reach Map for {year} {season_lower.upper()}...")
    
    # Target default output paths if not provided
    season_dir = os.path.join("outputs", str(year), f"{year}_{season_lower}")
    os.makedirs(season_dir, exist_ok=True)
    
    map_dir = os.path.join("outputs", "map")
    os.makedirs(map_dir, exist_ok=True)

    if output_path is None:
        output_path = os.path.join(season_dir, f"hybrid_shoreline_map_{year}_{season_lower}.html")
        
    m = folium.Map(location=[21.0, 105.8], zoom_start=11, control_scale=True)
    folium.TileLayer('openstreetmap', name='OpenStreetMap').add_to(m)
    folium.TileLayer(
        tiles='https://mt1.google.com/vt/lyrs=s&x={x}&y={y}&z={z}',
        attr='Google Satellite',
        name='Google Satellite',
        overlay=False,
        control=True
    ).add_to(m)
    
    # File discovery with fallbacks
    reach1_s1_path = find_file(f"reach1_s1_shoreline_{year}_{season_lower}.geojson", year, season_lower)
    reach1_s2_path = find_file(f"reach1_s2_ref_{year}_{season_lower}.geojson", year, season_lower)
    
    reach2_s1_path = find_file(f"reach2_s1_shoreline_{year}_{season_lower}.geojson", year, season_lower)
    reach2_s2_path = find_file(f"reach2_s2_ref_{year}_{season_lower}.geojson", year, season_lower)
    
    reach3_s1_path = find_file(f"reach3_s1_shoreline_{year}_{season_lower}.geojson", year, season_lower)
    if not reach3_s1_path:
        reach3_s1_path = find_file(f"shoreline_{year}_{season_lower}_final.geojson", year, season_lower)
        
    reach3_s2_path = find_file(f"reach3_s2_ref_{year}_{season_lower}.geojson", year, season_lower)
    if not reach3_s2_path:
        reach3_s2_path = find_file(f"shoreline_{year}_{season_lower}_s2_ref.geojson", year, season_lower)
        
    reach_gdfs = {}
    
    def add_geojson_layer(path, name, color, weight, dash_array=None):
        if path and os.path.exists(path):
            try:
                gdf = gpd.read_file(path).to_crs("EPSG:4326")
                style = {'color': color, 'weight': weight, 'fillColor': 'none'}
                if dash_array:
                    style['dashArray'] = dash_array
                folium.GeoJson(
                    gdf,
                    name=name,
                    style_function=lambda x, style=style: style
                ).add_to(m)
                print(f"[Loaded] {name} from {path}")
                return gdf
            except Exception as e:
                print(f"[Error] Failed to load {name} from {path}: {e}")
        else:
            print(f"[Warning] File not found for {name} (tried: {path})")
        return gpd.GeoDataFrame()

    # Load S2 References (Dashed)
    r1_s2_gdf = add_geojson_layer(reach1_s2_path, "Reach 1: S2 Reference", '#e74c3c', 2, '5, 5')
    r2_s2_gdf = add_geojson_layer(reach2_s2_path, "Reach 2: S2 Reference", '#d35400', 2, '5, 5')
    r3_s2_gdf = add_geojson_layer(reach3_s2_path, "Reach 3: S2 Reference", '#e67e22', 2, '5, 5')
    
    # Load S1 Shorelines
    r1_s1_gdf = add_geojson_layer(reach1_s1_path, "Reach 1: Local RF (S1)", '#8e44ad', 3)
    r2_s1_gdf = add_geojson_layer(reach2_s1_path, "Reach 2: Local RF (S1)", '#2980b9', 3)
    r3_s1_gdf = add_geojson_layer(reach3_s1_path, "Reach 3: Local RF (S1)", '#16a085', 3)
    
    # Validation Error Points Layer
    val_group = folium.FeatureGroup(name='Validation Error Mask (All 3 Reaches)', show=True)
    reach_stats_summary = {}

    reach_configs = [
        ('Reach 1', r1_s1_gdf, r1_s2_gdf, '#8e44ad'),
        ('Reach 2', r2_s1_gdf, r2_s2_gdf, '#2980b9'),
        ('Reach 3', r3_s1_gdf, r3_s2_gdf, '#16a085')
    ]

    for r_title, s1_gdf, s2_gdf, r_color in reach_configs:
        if not s1_gdf.empty and not s2_gdf.empty:
            s1_utm = s1_gdf.to_crs("EPSG:32648")
            s2_utm = s2_gdf.to_crs("EPSG:32648")
            val_res = validate_shoreline(s1_utm, s2_utm, spacing=25.0)
            reach_stats_summary[r_title] = val_res
            
            ext_pts = val_res.get('ext_points_info', [])
            visual_pts = ext_pts[::2]  # 50m spacing from 25m resampled dataset
            
            for info in visual_pts:
                pt = info['point']
                pt_wgs = gpd.GeoSeries([pt], crs="EPSG:32648").to_crs("EPSG:4326").iloc[0]
                dist = info['distance']
                
                if dist <= 30.0:
                    color = '#2ecc71'
                    rating_str = 'Tốt (Good)'
                    radius = 3.5
                elif dist <= 70.0:
                    color = '#ffb300'
                    rating_str = 'Trung bình (Moderate)'
                    radius = 5.0
                else:
                    color = '#e74c3c'
                    rating_str = 'Kém (Poor)'
                    radius = 6.5
                    
                popup_html = f"""
                <div style="font-family: sans-serif; font-size: 11px; width: 220px;">
                    <h4 style="margin: 0 0 5px 0; font-size: 12px; color: {r_color};">{r_title} Point Validation</h4>
                    <b>Distance Error:</b> {dist:.2f} m<br>
                    <b>Rating:</b> {rating_str}<br>
                    <b>Segment ID:</b> {info.get('segment_id', 'N/A')}<br>
                    <b>Bank Type:</b> {info.get('bank_type', 'N/A')}
                </div>
                """
                folium.CircleMarker(
                    location=[pt_wgs.y, pt_wgs.x],
                    radius=radius,
                    color=color,
                    fill=True,
                    fill_color=color,
                    fill_opacity=0.85,
                    popup=folium.Popup(popup_html, max_width=250),
                    tooltip=f"{r_title}: {dist:.1f} m"
                ).add_to(val_group)

    val_group.add_to(m)

    # Format reach summary metrics for legend
    def format_r_stat(r_title):
        st = reach_stats_summary.get(r_title)
        if st:
            return f"RMSE: {st.get('rmse_dist_m', 0.0):.1f}m | Mean: {st.get('mean_dist_m', 0.0):.1f}m"
        return "Loaded"

    r1_stat_str = format_r_stat('Reach 1')
    r2_stat_str = format_r_stat('Reach 2')
    r3_stat_str = format_r_stat('Reach 3')

    # Legend
    legend_html = f"""
    <div style="position: fixed; 
                bottom: 25px; left: 25px; width: 360px; z-index:9999; font-size:12px; 
                background-color:rgba(18, 22, 28, 0.92); color: #ecf0f1;
                border: 2px solid #34495e; border-radius: 10px; padding: 12px;
                box-shadow: 0 4px 15px rgba(0,0,0,0.5); font-family: 'Segoe UI', Arial, sans-serif;">
        <h4 style="margin: 0 0 8px 0; font-size: 14px; font-weight: bold; text-align: center; color: #00ffff; border-bottom: 1px solid #34495e; padding-bottom: 5px;">
            📌 Master 3-Reach Validation Map ({year} {season_lower.upper()})
        </h4>
        <div style="display: flex; align-items: center; margin-bottom: 5px;">
            <div style="width: 16px; height: 3px; background-color: #8e44ad; margin-right: 8px;"></div>
            <span><b>Reach 1: Upper (Ba Vi)</b> - <span style="color:#00ffff;">{r1_stat_str}</span></span>
        </div>
        <div style="display: flex; align-items: center; margin-bottom: 5px;">
            <div style="width: 16px; height: 3px; background-color: #2980b9; margin-right: 8px;"></div>
            <span><b>Reach 2: Middle (Hanoi Urban)</b> - <span style="color:#00ffff;">{r2_stat_str}</span></span>
        </div>
        <div style="display: flex; align-items: center; margin-bottom: 5px;">
            <div style="width: 16px; height: 3px; background-color: #16a085; margin-right: 8px;"></div>
            <span><b>Reach 3: Lower (Delta)</b> - <span style="color:#00ffff;">{r3_stat_str}</span></span>
        </div>
        <hr style="border-color: #34495e; margin: 8px 0;">
        <div style="display: flex; align-items: center; margin-bottom: 4px;">
            <div style="width: 12px; height: 12px; border-radius: 50%; background-color: #2ecc71; margin-right: 8px;"></div>
            <span>Good Error (&le; 30 m)</span>
        </div>
        <div style="display: flex; align-items: center; margin-bottom: 4px;">
            <div style="width: 12px; height: 12px; border-radius: 50%; background-color: #ffb300; margin-right: 8px;"></div>
            <span>Moderate Error (30 m - 70 m)</span>
        </div>
        <div style="display: flex; align-items: center; margin-bottom: 4px;">
            <div style="width: 12px; height: 12px; border-radius: 50%; background-color: #e74c3c; margin-right: 8px;"></div>
            <span>High Error (&gt; 70 m)</span>
        </div>
    </div>
    """
    m.get_root().html.add_child(folium.Element(legend_html))
    
    MousePosition().add_to(m)
    folium.LayerControl().add_to(m)
    
    # Save to requested path
    m.save(output_path)
    print(f"Successfully generated master validation map: {output_path}")
    
    # Also save copy to outputs/map/ and season directory if applicable
    map_fallback_path = os.path.join(map_dir, f"hybrid_shoreline_map_{year}_{season_lower}.html")
    if output_path != map_fallback_path:
        m.save(map_fallback_path)
        print(f"Saved copy to map directory: {map_fallback_path}")

    season_fallback_path = os.path.join(season_dir, f"hybrid_shoreline_map_{year}_{season_lower}.html")
    if output_path != season_fallback_path:
        m.save(season_fallback_path)

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--year", type=int, default=2024)
    args = parser.parse_args()
    
    for s in ["dry", "wet"]:
        target_path = os.path.join("outputs", str(args.year), f"{args.year}_{s}", f"hybrid_shoreline_map_{args.year}_{s}.html")
        plot_hybrid_map(args.year, s, target_path)

