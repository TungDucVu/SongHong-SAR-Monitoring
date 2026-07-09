"""
Script to generate training polygons from ESA WorldCover 2020 within the Red River AOI.
Saves the results to aoi/training_polygons.geojson and renders a check_training_polygons.html map.
"""

import ee
import os
import json
import folium
from src.config import GEE_PROJECT, AOI_GEOJSON_PATH, TRAINING_POLYGONS_PATH, OUTPUT_DIR
from src.aoi import get_aoi_geometry

def main():
    print("==================================================")
    print("       GENERATING TRAINING POLYGONS FROM ESA      ")
    print("==================================================")
    
    # 1. Initialize Earth Engine
    try:
        ee.Initialize(project=GEE_PROJECT)
        print(f"[GEE] Initialized successfully with project: {GEE_PROJECT}")
    except Exception as e:
        print(f"[GEE Error] Failed to initialize: {e}")
        return

    # 2. Get AOI Geometry
    aoi_geometry = get_aoi_geometry()
    
    # 3. Load ESA WorldCover 2021
    print("[Data] Loading ESA WorldCover 2021...")
    wc = ee.Image('ESA/WorldCover/v200/2021').clip(aoi_geometry)
    
    # 4. Remap to our 4 classes:
    # 1: Water (80)
    # 2: Sand (60 - Barren)
    # 3: Built-up (50)
    # 4: Others (10 - Trees, 20 - Shrub, 30 - Grass, 40 - Crop)
    remapped = wc.remap(
        [80, 60, 50, 10, 20, 30, 40],
        [1,  2,  3,  4,  4,  4,  4],
        0
    ).rename('class')
    
    # Mask out class 0 (unmapped/wetlands/etc)
    remapped = remapped.updateMask(remapped.gt(0))
    
    # 5. Convert raster to vector polygons
    print("[GEE] Converting raster to vector polygons (scale=30m)...")
    
    target_counts = {
        1: 60,  # Water
        2: 85,  # Sand
        3: 45,  # Built-up
        4: 60   # Others
    }
    
    class_names = {
        1: 'Water',
        2: 'Sand',
        3: 'Built-up',
        4: 'Others'
    }
    
    class_polygons = []
    
    # 5.1 Process Class 1 (Water) with 50m erosion and Upstream/Midstream/Downstream segment sampling
    print("[GEE] Sampling distributed Water polygons (100mx100m squares)...")
    water_mask = remapped.eq(1)
    # focalMin shrinks the Water pixels by 50m circle kernel to keep points deep in the river
    water_eroded = water_mask.focalMin(50, 'circle', 'meters')
    water_eroded_masked = water_eroded.updateMask(water_eroded.eq(1))
    
    upstream_geom = ee.Geometry.BBox(105.3, 21.098, 106.1, 21.35)
    midstream_geom = ee.Geometry.BBox(105.3, 20.891, 106.1, 21.098)
    downstream_geom = ee.Geometry.BBox(105.3, 20.65, 106.1, 20.891)
    
    # Intersect segments with AOI to keep them within boundaries
    upstream_region = upstream_geom.intersection(aoi_geometry, maxError=1)
    midstream_region = midstream_geom.intersection(aoi_geometry, maxError=1)
    downstream_region = downstream_geom.intersection(aoi_geometry, maxError=1)
    
    # Vectorize the eroded water mask per segment to get pure water geometries
    water_vectors_u = water_eroded_masked.reduceToVectors(
        reducer=ee.Reducer.countEvery(),
        geometry=upstream_region,
        scale=30,
        maxPixels=1e8,
        bestEffort=True
    )
    water_vectors_m = water_eroded_masked.reduceToVectors(
        reducer=ee.Reducer.countEvery(),
        geometry=midstream_region,
        scale=30,
        maxPixels=1e8,
        bestEffort=True
    )
    water_vectors_d = water_eroded_masked.reduceToVectors(
        reducer=ee.Reducer.countEvery(),
        geometry=downstream_region,
        scale=30,
        maxPixels=1e8,
        bestEffort=True
    )
    
    # Sample points on the eroded river surface using randomPoints
    pts_upstream = ee.FeatureCollection.randomPoints(water_vectors_u.geometry(), 20, seed=42)
    pts_midstream = ee.FeatureCollection.randomPoints(water_vectors_m.geometry(), 20, seed=42)
    pts_downstream = ee.FeatureCollection.randomPoints(water_vectors_d.geometry(), 20, seed=42)
    
    water_pts = ee.FeatureCollection([pts_upstream, pts_midstream, pts_downstream]).flatten()
    
    # Convert points to 100x100m squares (50m buffer bounds)
    def make_100m_squares_water(f):
        square_geom = f.geometry().buffer(50).bounds()
        f_id = ee.String('1_').cat(f.id())
        return ee.Feature(square_geom, {
            'id': f_id,
            'class': 1,
            'className': 'Water'
        })
        
    water_formatted = water_pts.map(make_100m_squares_water)
    print(f"  Class 1 (Water): Sampled 60 point-based 100x100m square polygons.")
    class_polygons.append(water_formatted)
    
    # 5.2 Process Class 2 (Sand), Class 3 (Built-up), Class 4 (Others) from remapped raster vectorization
    non_water_mask = remapped.updateMask(remapped.neq(1))
    print("[GEE] Converting non-water raster to vector polygons...")
    non_water_vectors = non_water_mask.reduceToVectors(
        reducer=ee.Reducer.countEvery(),
        geometry=aoi_geometry,
        scale=30,
        maxPixels=1e8,
        bestEffort=True
    )
    
    for c in [2, 3, 4]:
        print(f"[GEE] Sampling large {class_names[c]} polygons from ESA 2021...")
        class_fc = non_water_vectors.filter(ee.Filter.eq('label', c))
        
        # Apply class-specific size limits to select larger polygons (min 10-20 pixels ~ 0.9-1.8 ha)
        min_pixels = 10 if c == 2 else 20
        max_pixels = 300 if c == 2 else 500
        
        large_class_fc = class_fc.filter(ee.Filter.And(
            ee.Filter.gte('count', min_pixels),
            ee.Filter.lte('count', max_pixels)
        ))
        
        size = large_class_fc.size().getInfo()
        print(f"  Class {c} ({class_names[c]}): Found {size} candidate large polygons in AOI.")
        
        if size > 0:
            randomized = large_class_fc.randomColumn('rand', seed=42).sort('rand')
            sampled = randomized.limit(target_counts[c])
            
            def format_feature(f):
                f_id = ee.Number(f.get('label')).format('%d').cat('_').cat(f.id())
                return ee.Feature(f.geometry(), {
                    'id': f_id,
                    'class': f.get('label'),
                    'className': class_names[c]
                })
            
            formatted_sampled = sampled.map(format_feature)
            class_polygons.append(formatted_sampled)
            print(f"    -> Sampled {formatted_sampled.size().getInfo()} polygons.")
        else:
            print(f"    [Warning] No candidates found for Class {c} ({class_names[c]}) using size limits.")
        
    combined_fc = ee.FeatureCollection(class_polygons).flatten()
    total_sampled = combined_fc.size().getInfo()
    print(f"\n[GEE] Total training polygons sampled: {total_sampled}")
    
    # 7. Download and Save GeoJSON
    print(f"[Data] Saving polygons to local path: {TRAINING_POLYGONS_PATH}...")
    try:
        geojson_data = combined_fc.getInfo()
        
        # Ensure directories exist
        os.makedirs(os.path.dirname(TRAINING_POLYGONS_PATH), exist_ok=True)
        
        with open(TRAINING_POLYGONS_PATH, 'w', encoding='utf-8') as f:
            json.dump(geojson_data, f, indent=2)
        print("[Data] Saved training polygons GeoJSON successfully.")
    except Exception as e:
        print(f"[Error] Failed to save GeoJSON: {e}")
        return

    # 8. Render Checkpoint HTML Map for visual verification
    print("\n[QC] Rendering check_training_polygons.html map...")
    m = folium.Map(location=[21.04, 105.86], zoom_start=11, control_scale=True)
    
    # Base Layer: Google Satellite
    folium.TileLayer(
        tiles='https://mt1.google.com/vt/lyrs=s&x={x}&y={y}&z={z}',
        attr='Google',
        name='Google Satellite',
        overlay=False,
        control=True
    ).add_to(m)
    
    # Sentinel-2 RGB composite layer for validation reference
    s2_col = (ee.ImageCollection('COPERNICUS/S2_SR_HARMONIZED')
              .filterBounds(aoi_geometry)
              .filterDate('2024-01-01', '2024-12-31')
              .filter(ee.Filter.lt('CLOUDY_PIXEL_PERCENTAGE', 20))
              .filter(ee.Filter.calendarRange(1, 4, 'month'))) # Dry season composite for cloud-free reference
              
    def mask_s2_clouds(img):
        qa = img.select('QA60')
        cloud_bit = 1 << 10
        cirrus_bit = 1 << 11
        mask = qa.bitwiseAnd(cloud_bit).eq(0).And(qa.bitwiseAnd(cirrus_bit).eq(0))
        return img.updateMask(mask)
        
    s2_masked = s2_col.map(mask_s2_clouds)
    s2_img = s2_masked.median().clip(aoi_geometry)
    
    try:
        map_id_dict = s2_img.getMapId({'bands': ['B4', 'B3', 'B2'], 'min': 0, 'max': 3000})
        folium.raster_layers.TileLayer(
            tiles=map_id_dict['tile_fetcher'].url_format,
            attr='Google Earth Engine',
            name='Sentinel-2 RGB Reference',
            overlay=True,
            control=True,
            show=False
        ).add_to(m)
    except Exception as e:
        print(f"[QC Warning] Failed to add S2 RGB layer: {e}")
        
    # Add ESA WorldCover 2021 (4 Classes) Layer
    try:
        class_palette = ['1a73e8', 'd35400', 'e74c3c', '2ecc71']
        esa_vis = {
            'min': 1,
            'max': 4,
            'palette': class_palette
        }
        esa_map_id = remapped.getMapId(esa_vis)
        folium.raster_layers.TileLayer(
            tiles=esa_map_id['tile_fetcher'].url_format,
            attr='ESA WorldCover 2021 Remapped',
            name='ESA WorldCover 2021 (4 Classes)',
            overlay=True,
            control=True,
            opacity=0.6,
            show=False
        ).add_to(m)
    except Exception as e:
        print(f"[QC Warning] Failed to add ESA WorldCover remapped layer: {e}")

    # Add ESA WorldCover 2021 (Raw) Layer
    try:
        raw_map_id = wc.getMapId()
        folium.raster_layers.TileLayer(
            tiles=raw_map_id['tile_fetcher'].url_format,
            attr='ESA WorldCover 2021 Raw',
            name='ESA WorldCover 2021 (Raw)',
            overlay=True,
            control=True,
            opacity=0.6,
            show=False
        ).add_to(m)
    except Exception as e:
        print(f"[QC Warning] Failed to add raw ESA WorldCover layer: {e}")
        
    # Styles for each class polygon
    colors_map = {
        1: '#1a73e8', # Water: Blue
        2: '#d35400', # Sand: Orange
        3: '#e74c3c', # Built-up: Red
        4: '#2ecc71'  # Others: Green
    }
    
    def style_poly(feature):
        c_code = feature['properties']['class']
        fill_color = colors_map.get(c_code, '#808080')
        return {
            'fillColor': fill_color,
            'color': '#000000',
            'weight': 1.5,
            'fillOpacity': 0.5
        }
        
    # Add training polygons
    folium.GeoJson(
        geojson_data,
        name="Training Polygons (ESA Sourced)",
        style_function=style_poly,
        tooltip=folium.GeoJsonTooltip(
            fields=['id', 'className'],
            aliases=['ID:', 'Class:'],
            localize=True
        )
    ).add_to(m)
    
    # Add study area outline
    try:
        folium.GeoJson(
            aoi_geometry.getInfo(),
            name="Study Area AOI",
            style_function=lambda x: {'fillColor': 'none', 'color': '#ffffff', 'weight': 2.5, 'opacity': 0.8}
        ).add_to(m)
    except Exception as e:
        print(f"[QC Warning] Failed to add AOI boundary: {e}")
        
    # Add Legend
    legend_html = """
    <div style="position: fixed; 
                bottom: 50px; left: 10px; width: 220px; height: 180px; 
                z-index:9999; font-size:12px; background-color:rgba(255, 255, 255, 0.9);
                border: 2px solid grey; border-radius: 6px; padding: 10px;
                box-shadow: 2px 2px 5px rgba(0,0,0,0.2); font-family: sans-serif;">
        <h4 style="margin: 0 0 8px 0; font-size: 13px; font-weight: bold; text-align: center;">Training Polygons QC</h4>
        <div style="display: flex; align-items: center; margin-bottom: 5px;">
            <div style="width: 16px; height: 16px; background-color: #1a73e8; border: 1px solid #000; margin-right: 8px;"></div>
            <span>1. Water</span>
        </div>
        <div style="display: flex; align-items: center; margin-bottom: 5px;">
            <div style="width: 16px; height: 16px; background-color: #d35400; border: 1px solid #000; margin-right: 8px;"></div>
            <span>2. Sand</span>
        </div>
        <div style="display: flex; align-items: center; margin-bottom: 5px;">
            <div style="width: 16px; height: 16px; background-color: #e74c3c; border: 1px solid #000; margin-right: 8px;"></div>
            <span>3. Built-up (Urban)</span>
        </div>
        <div style="display: flex; align-items: center; margin-bottom: 8px;">
            <div style="width: 16px; height: 16px; background-color: #2ecc71; border: 1px solid #000; margin-right: 8px;"></div>
            <span>4. Others (Vegetation/Land)</span>
        </div>
    </div>
    """
    m.get_root().html.add_child(folium.Element(legend_html))
    
    folium.LayerControl().add_to(m)
    
    # Save checkpoint HTML
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    html_path = os.path.join(OUTPUT_DIR, 'check_training_polygons.html')
    m.save(html_path)
    print(f"\n[QC Success] Saved training polygon verification map to: {html_path}")
    print("==================================================")

if __name__ == '__main__':
    main()
