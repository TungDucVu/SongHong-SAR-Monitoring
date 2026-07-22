import os
import geopandas as gpd
import folium
from folium.plugins import MousePosition

def plot_hybrid_map(year, season, output_path):
    print(f"Generating unified Hybrid Map for {year} {season}...")
    m = folium.Map(location=[21.0, 105.8], zoom_start=11, control_scale=True)
    folium.TileLayer('openstreetmap', name='OpenStreetMap').add_to(m)
    folium.TileLayer(
        tiles='https://mt1.google.com/vt/lyrs=s&x={x}&y={y}&z={z}',
        attr='Google',
        name='Google Satellite',
        overlay=False,
        control=True
    ).add_to(m)
    
    OUTPUT_DIR = "outputs"
    
    # Load Reach 1 data
    reach1_s1_path = os.path.join(OUTPUT_DIR, f"reach1_s1_shoreline_{year}_{season}.geojson")
    reach1_s2_path = os.path.join(OUTPUT_DIR, f"reach1_s2_ref_{year}_{season}.geojson")
    
    # Load Reach 2&3 data
    reach23_s1_path = os.path.join(OUTPUT_DIR, f"shoreline_{year}_{season}_final.geojson")
    reach23_s2_path = os.path.join(OUTPUT_DIR, f"shoreline_{year}_{season}_s2_ref.geojson")
    
    def add_geojson(path, name, color, weight, dash_array=None):
        if os.path.exists(path):
            gdf = gpd.read_file(path).to_crs("EPSG:4326")
            style = {'color': color, 'weight': weight, 'fillColor': 'none'}
            if dash_array:
                style['dashArray'] = dash_array
            folium.GeoJson(
                gdf,
                name=name,
                style_function=lambda x, style=style: style
            ).add_to(m)
            print(f"Loaded {name} from {path}")
        else:
            print(f"[Warning] File not found: {path}")

    # Add S2 References (Red for Reach 1, Orange for Reach 2&3)
    add_geojson(reach1_s2_path, "Reach 1: S2 Reference", '#e74c3c', 2, '5, 5')
    add_geojson(reach23_s2_path, "Reach 2&3: S2 Reference", '#d35400', 2, '5, 5')
    
    # Add S1 Extracted Shorelines (Purple for Reach 1, Blue for Reach 2&3)
    add_geojson(reach1_s1_path, "Reach 1: Local RF (S1)", '#8e44ad', 3)
    add_geojson(reach23_s1_path, "Reach 2&3: Global RF (S1)", '#2980b9', 3)
    
    # Legend
    legend_html = f"""
    <div style="position: fixed; 
                bottom: 80px; left: 10px; width: 300px; height: 160px; 
                z-index:9999; font-size:13px; background-color:rgba(255, 255, 255, 0.95);
                border: 2px solid grey; border-radius: 6px; padding: 10px;
                box-shadow: 2px 2px 5px rgba(0,0,0,0.2); font-family: sans-serif;">
        <h4 style="margin: 0 0 8px 0; font-size: 14px; font-weight: bold; text-align: center;">Hybrid Shoreline Map - {year} {season.upper()}</h4>
        <div style="display: flex; align-items: center; margin-bottom: 5px;">
            <div style="width: 16px; height: 3px; background-color: #8e44ad; margin-right: 8px;"></div>
            <span>Reach 1: S1 (Local RF)</span>
        </div>
        <div style="display: flex; align-items: center; margin-bottom: 5px;">
            <div style="width: 16px; height: 3px; background-color: #e74c3c; margin-right: 8px; border-bottom: 2px dashed white;"></div>
            <span>Reach 1: S2 Reference</span>
        </div>
        <div style="display: flex; align-items: center; margin-bottom: 5px;">
            <div style="width: 16px; height: 3px; background-color: #2980b9; margin-right: 8px;"></div>
            <span>Reach 2&3: S1 (Global RF)</span>
        </div>
        <div style="display: flex; align-items: center; margin-bottom: 5px;">
            <div style="width: 16px; height: 3px; background-color: #d35400; margin-right: 8px; border-bottom: 2px dashed white;"></div>
            <span>Reach 2&3: S2 Reference</span>
        </div>
    </div>
    """
    m.get_root().html.add_child(folium.Element(legend_html))
    
    MousePosition().add_to(m)
    folium.LayerControl().add_to(m)
    
    m.save(output_path)
    print(f"Successfully generated map: {output_path}")

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--year", type=int, default=2024)
    args = parser.parse_args()
    
    os.makedirs("outputs", exist_ok=True)
    plot_hybrid_map(args.year, "dry", f"outputs/hybrid_shoreline_map_{args.year}_dry.html")
    plot_hybrid_map(args.year, "wet", f"outputs/hybrid_shoreline_map_{args.year}_wet.html")
