import os
import sys
import time
import ee
import geopandas as gpd
import pandas as pd
import folium
from folium.plugins import MousePosition
import shapely
from shapely.geometry import box, MultiLineString, LineString
from shapely.validation import make_valid

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.config import (
    GEE_PROJECT, CLASSIFIER_FEATURES,
    SHORELINE_RAW_DRY_PATH, OUTPUT_DIR
)
from src.aoi import get_aoi_geometry
from src.collection import create_seasonal_composite
from src.classification import load_training_polygons, train_classifier, classify_image
from src.shoreline import load_centerline, refine_classification

def main():
    print("=============================================================")
    # 1. Initialize GEE
    if not ee.data.is_initialized():
        ee.Initialize(project=GEE_PROJECT)
    print(f"[GEE] Initialized successfully with project: {GEE_PROJECT}")
    
    aoi_geometry = get_aoi_geometry()
    centerline_fc = load_centerline()
    training_fc = load_training_polygons()
    
    # 2. Run Classification for 2024 Dry Season
    print("[Run] Processing 2024 DRY...")
    composite = create_seasonal_composite(2024, 'dry', aoi_geometry)
    
    final_cf, _ = train_classifier(
        training_fc,
        composite,
        CLASSIFIER_FEATURES,
        best_params={'numberOfTrees': 300, 'variablesPerSplit': 3, 'bagFraction': 0.5}
    )
    
    # Clip composite to 2km centerline buffer to restrict feature engineering & classification area
    corridor_geom = centerline_fc.geometry().buffer(2000)
    composite_clipped = composite.clip(corridor_geom)
    
    # Classify entire composite
    classified, _ = classify_image(composite_clipped, final_cf, CLASSIFIER_FEATURES)
    
    # Download classification mask and polygonize locally to get raw water/sand polygons
    # (recreating the steps of extract_shared_boundary)
    import requests
    import io
    import rasterio
    from rasterio.features import shapes
    from shapely.geometry import shape
    
    scale = 30
    buffer_geom = centerline_fc.geometry().buffer(2000)
    water_mask = classified.clip(buffer_geom).eq(1).focalMode(radius=1.5, kernelType='square', units='pixels')
    sand_mask = classified.clip(buffer_geom).eq(2).focalMode(radius=1.5, kernelType='square', units='pixels')
    combined_mask = ee.Image(0).where(water_mask, 1).where(sand_mask, 2)
    bbox = buffer_geom.bounds()
    
    print("[Phase 5] Downloading classification mask GeoTIFF...")
    url = combined_mask.getDownloadURL({
        'scale': scale,
        'crs': 'EPSG:32648',
        'region': bbox.getInfo(),
        'format': 'GEO_TIFF'
    })
    r = requests.get(url, timeout=300)
    r.raise_for_status()
    
    print("[Phase 5] Polygonizing locally...")
    with rasterio.open(io.BytesIO(r.content)) as src:
        raster_data = src.read(1)
        transform = src.transform
        
    water_geoms = []
    sand_geoms = []
    for geom, val in shapes(raster_data, transform=transform):
        if val == 1:
            water_geoms.append(shape(geom))
        elif val == 2:
            sand_geoms.append(shape(geom))
            
    water_gdf = gpd.GeoDataFrame(geometry=water_geoms, crs="EPSG:32648")
    sand_gdf = gpd.GeoDataFrame(geometry=sand_geoms, crs="EPSG:32648")
    
    water_union = water_gdf.geometry.unary_union
    sand_union = sand_gdf.geometry.unary_union
    
    water_clean = make_valid(water_union.buffer(0))
    sand_clean = make_valid(sand_union.buffer(0))
    
    # Local morphological opening (co 20m, giãn 20m) and closing (giãn 30m, co 30m)
    print("[Phase 5] Applying local morphological operations...")
    water_refined = water_clean.buffer(-20).buffer(20).buffer(30).buffer(-30)
    sand_refined = sand_clean.buffer(-20).buffer(20).buffer(30).buffer(-30)
    
    # 3. Load the Extracted Shared Boundary (from shoreline_2024_dry_raw.geojson)
    if not os.path.exists(SHORELINE_RAW_DRY_PATH):
        raise FileNotFoundError(f"Shared boundary file not found: {SHORELINE_RAW_DRY_PATH}")
    
    shoreline_gdf = gpd.read_file(SHORELINE_RAW_DRY_PATH)
    
    # 4. Find the centroid of the 3rd longest segment to define our 500m x 500m AOI
    # (Ensure we are around another active sandbar where water and sand contact)
    shoreline_gdf['length'] = shoreline_gdf.geometry.length
    longest_segment = shoreline_gdf.sort_values(by='length', ascending=False).iloc[2]
    centroid = longest_segment.geometry.centroid
    cx, cy = centroid.x, centroid.y
    print(f"Selected centroid for 500m AOI (Index 2): Easting={cx:.2f}, Northing={cy:.2f} (UTM Zone 48N)")
    
    # 5. Create a 500m x 500m bounding box in EPSG:32648
    aoi_box = box(cx - 250, cy - 250, cx + 250, cy + 250)
    aoi_gdf = gpd.GeoDataFrame(geometry=[aoi_box], crs="EPSG:32648")
    
    # Crop geometries to the AOI box
    water_cropped = water_refined.intersection(aoi_box)
    sand_cropped = sand_refined.intersection(aoi_box)
    shoreline_cropped_gdf = gpd.clip(shoreline_gdf, aoi_gdf)
    
    # Extract boundaries
    water_boundary_cropped = water_cropped.boundary
    sand_boundary_cropped = sand_cropped.boundary
    
    # Convert cropped geometries to GeoDataFrames for exporting and styling in Folium
    water_poly_gdf = gpd.GeoDataFrame(geometry=[water_cropped], crs="EPSG:32648").to_crs("EPSG:4326")
    sand_poly_gdf = gpd.GeoDataFrame(geometry=[sand_cropped], crs="EPSG:32648").to_crs("EPSG:4326")
    
    water_bound_gdf = gpd.GeoDataFrame(geometry=[water_boundary_cropped], crs="EPSG:32648").to_crs("EPSG:4326")
    sand_bound_gdf = gpd.GeoDataFrame(geometry=[sand_boundary_cropped], crs="EPSG:32648").to_crs("EPSG:4326")
    
    shoreline_cropped_wgs84 = shoreline_cropped_gdf.to_crs("EPSG:4326")
    
    # Get center in WGS 84
    centroid_wgs84 = gpd.GeoDataFrame(geometry=[centroid], crs="EPSG:32648").to_crs("EPSG:4326").geometry.iloc[0]
    lat, lon = centroid_wgs84.y, centroid_wgs84.x
    print(f"Selected center in WGS 84: Lat={lat:.6f}, Lon={lon:.6f}")
    
    # 6. Quality Validation Check
    # Verify if the shared boundary lies exactly on the intersection of water and sand boundaries.
    # The mathematical definition of the contact zone:
    # Contact Zone = (water_refined.boundary) intersected with (sand_refined.buffer(1)) or similar,
    # or simply, the distance from shoreline points to both water and sand polygons should be very close to 0.
    
    # Let's sample points along the cropped shared boundary and compute distances
    distances_to_water = []
    distances_to_sand = []
    
    if not shoreline_cropped_gdf.empty:
        # Explode to simple lines if multi
        flat_lines = []
        for g in shoreline_cropped_gdf.geometry:
            if isinstance(g, MultiLineString):
                flat_lines.extend(g.geoms)
            elif isinstance(g, LineString):
                flat_lines.append(g)
                
        for line in flat_lines:
            # sample points at 10m intervals
            length = line.length
            num_points = max(2, int(length / 10))
            for i in range(num_points + 1):
                pt = line.interpolate(i * (length / num_points))
                distances_to_water.append(pt.distance(water_refined))
                distances_to_sand.append(pt.distance(sand_refined))
                
    avg_dist_water = pd.Series(distances_to_water).mean() if distances_to_water else 0
    avg_dist_sand = pd.Series(distances_to_sand).mean() if distances_to_sand else 0
    
    print("\n=============================================================")
    print("   QUALITY ASSURANCE (QA) CHECK RESULTS")
    print("=============================================================")
    print(f"Average Distance from Shared Boundary to Water Polygon: {avg_dist_water:.4f} meters")
    print(f"Average Distance from Shared Boundary to Sand Polygon:  {avg_dist_sand:.4f} meters")
    
    max_tolerated_distance = 0.5 # 50cm tolerance due to floating point precision of intersection
    
    if avg_dist_water <= max_tolerated_distance and avg_dist_sand <= max_tolerated_distance:
        print("[QA RESULT] SUCCESS! The shared boundary matches the contact zone of Water and Sand.")
        qa_status = "SUCCESS (Contact boundaries align perfectly)"
    else:
        print("[QA RESULT] WARNING: Shared boundary does not lie on the Water-Sand contact zone.")
        qa_status = "FAILED (Misalignment detected)"
        
    # Check fragmentation
    num_cropped_segments = len(shoreline_cropped_gdf)
    print(f"Number of shoreline segments in this 500m AOI: {num_cropped_segments}")
    if num_cropped_segments > 1:
        print("[QA NOTE] Shoreline is fragmented in this AOI. This is expected and will be handled by Phase 6 (Graph Cleaning).")
        fragmentation_note = "Fragmented (Expected - to be resolved in Phase 6)"
    else:
        print("[QA NOTE] Shoreline is a single contiguous segment in this AOI.")
        fragmentation_note = "Contiguous"
    print("=============================================================\n")
    
    # 7. Create Folium Map
    print("[Folium] Creating interactive quality check map...")
    m = folium.Map(location=[lat, lon], zoom_start=18, control_scale=True)
    folium.LatLngPopup().add_to(m)
    MousePosition().add_to(m)
    
    # Add Google Satellite
    folium.TileLayer(
        tiles='https://mt1.google.com/vt/lyrs=s&x={x}&y={y}&z={z}',
        attr='Google',
        name='Google Satellite',
        overlay=False,
        control=True
    ).add_to(m)
    
    # Style definitions
    water_poly_style = lambda x: {'fillColor': '#3498db', 'fillOpacity': 0.15, 'color': 'none'}
    water_bound_style = lambda x: {'color': '#2980b9', 'weight': 3.5, 'opacity': 0.8}
    
    sand_poly_style = lambda x: {'fillColor': '#e67e22', 'fillOpacity': 0.15, 'color': 'none'}
    sand_bound_style = lambda x: {'color': '#d35400', 'weight': 3.5, 'opacity': 0.8}
    
    shared_bound_style = lambda x: {'color': '#e74c3c', 'weight': 5.0, 'opacity': 1.0}
    aoi_box_style = lambda x: {'color': '#2ecc71', 'weight': 2.0, 'fill': False, 'dashArray': '4, 4'}
    
    # Add Layers
    folium.GeoJson(water_poly_gdf, name="Water Polygon (Fill)", style_function=water_poly_style).add_to(m)
    folium.GeoJson(water_bound_gdf, name="Water Polygon Boundary (Blue)", style_function=water_bound_style).add_to(m)
    
    folium.GeoJson(sand_poly_gdf, name="Sand Polygon (Fill)", style_function=sand_poly_style).add_to(m)
    folium.GeoJson(sand_bound_gdf, name="Sand Polygon Boundary (Orange)", style_function=sand_bound_style).add_to(m)
    
    folium.GeoJson(shoreline_cropped_wgs84, name="Extracted Shared Boundary (Red)", style_function=shared_bound_style).add_to(m)
    folium.GeoJson(gpd.GeoDataFrame(geometry=[aoi_box], crs="EPSG:32648").to_crs("EPSG:4326"), 
                   name="500m x 500m AOI Boundary", style_function=aoi_box_style).add_to(m)
    
    # Legend HTML
    legend_html = f"""
    <div style="position: fixed; 
                bottom: 100px; left: 10px; width: 320px; height: 260px; 
                z-index:9999; font-size:12px; background-color:rgba(255, 255, 255, 0.95);
                border: 2px solid grey; border-radius: 6px; padding: 10px;
                box-shadow: 2px 2px 5px rgba(0,0,0,0.2); font-family: sans-serif;">
        <h4 style="margin: 0 0 8px 0; font-size: 13px; font-weight: bold; text-align: center;">Phase 5 Quality Check (500m AOI)</h4>
        <div style="display: flex; align-items: center; margin-bottom: 5px;">
            <div style="width: 16px; height: 16px; background-color: #3498db; opacity: 0.15; border: 1px dashed #2980b9; margin-right: 8px;"></div>
            <span>Water Polygon (Blue Boundary)</span>
        </div>
        <div style="display: flex; align-items: center; margin-bottom: 5px;">
            <div style="width: 16px; height: 16px; background-color: #e67e22; opacity: 0.15; border: 1px dashed #d35400; margin-right: 8px;"></div>
            <span>Sand Polygon (Orange Boundary)</span>
        </div>
        <div style="display: flex; align-items: center; margin-bottom: 5px;">
            <div style="width: 16px; height: 5px; background-color: #e74c3c; margin-right: 8px;"></div>
            <span style="font-weight: bold; color: #e74c3c;">Shared Boundary (Red)</span>
        </div>
        <div style="display: flex; align-items: center; margin-bottom: 8px;">
            <div style="width: 16px; height: 5px; border-top: 2px dotted #2ecc71; margin-right: 8px;"></div>
            <span>500m × 500m AOI Box</span>
        </div>
        <hr style="margin: 4px 0 6px 0;">
        <div><b>Validation Metrics:</b></div>
        <div style="margin-top: 3px;">Distance to Water: <b>{avg_dist_water:.4f} m</b></div>
        <div>Distance to Sand: <b>{avg_dist_sand:.4f} m</b></div>
        <div>QA Status: <b style="color: green;">{qa_status}</b></div>
        <div>Contiguity: <b>{fragmentation_note}</b></div>
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
    
    output_path = os.path.join(OUTPUT_DIR, 'phase5_qc_overlay.html')
    m.save(output_path)
    print(f"[Success] Saved Phase 5 Quality Check map to: {output_path}")

if __name__ == '__main__':
    main()
