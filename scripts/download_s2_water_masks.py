import os
import sys
import ee
import geopandas as gpd
from shapely.ops import unary_union
from shapely.validation import make_valid

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.aoi import get_aoi_geometry
from src.shoreline import (
    get_continuous_centerline, load_manual_bridges, 
    generate_validation_shoreline_s2
)

def main():
    print("Initializing Google Earth Engine...")
    try:
        ee.Initialize(project='songhong-sar-monitoring')
    except Exception:
        ee.Initialize()
        
    print("Loading AOI and river corridor centerline...")
    aoi_geom = get_aoi_geometry()
    
    cl_linestring = get_continuous_centerline()
    cl_gdf = gpd.GeoDataFrame(geometry=[cl_linestring], crs="EPSG:4326").to_crs("EPSG:32648")
    corridor_poly = cl_gdf.geometry.buffer(2000).union_all()
    
    print("Loading manual bridges...")
    bridges_path = "data/bridges.geojson"
    if os.path.exists(bridges_path):
        bridges_gdf = load_manual_bridges(bridges_path)
        river_bridge_mask = bridges_gdf.geometry.buffer(0).union_all().intersection(corridor_poly)
    else:
        print("[Warning] data/bridges.geojson not found. Running without bridge mask.")
        river_bridge_mask = None

    years = list(range(2017, 2027))
    seasons = ['dry', 'wet']
    
    print(f"Starting batch S2 NDWI reference download for years {years}...")
    
    for year in years:
        for season in seasons:
            ref_path = os.path.join("data", f"s2_ref_shoreline_{year}_{season}.geojson")
            poly_path = os.path.join("data", f"s2_water_poly_{year}_{season}.geojson")
            
            if os.path.exists(ref_path) and os.path.exists(poly_path):
                print(f"[Skip] Cache already exists for {year} {season}.")
                continue
                
            print(f"\n==================================================")
            print(f" Processing S2 reference for: {year} {season.upper()}...")
            print(f"==================================================")
            
            try:
                # Call generator with bypass_cache=True to force query & download
                generate_validation_shoreline_s2(
                    year=year,
                    season=season,
                    aoi_geometry=aoi_geom,
                    bridge_mask=river_bridge_mask,
                    bypass_cache=True
                )
                print(f"[Success] Completed and cached reference for {year} {season}.")
            except Exception as e:
                print(f"[Error] Failed to process {year} {season}: {e}")
                
    print("\nBatch S2 reference download complete.")

if __name__ == "__main__":
    main()
