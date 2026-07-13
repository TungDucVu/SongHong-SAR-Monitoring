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
        
    # Add Draw control for manual polygon digitizing
    from folium.plugins import Draw
    draw = Draw(
        export=True,
        filename='manual_training_polygons.geojson',
        position='topleft',
        draw_options={
            'polyline': False,
            'circle': False,
            'marker': False,
            'circlemarker': False,
            'polygon': True,
            'rectangle': True
        }
    )
    draw.add_to(m)

    # Add Floating panel with training stats and instructions
    stats_panel_html = """
    <div style="position: fixed; 
                bottom: 20px; right: 20px; width: 340px; max-height: 85vh; overflow-y: auto;
                z-index: 9999; background-color: rgba(33, 37, 41, 0.95); color: #f8f9fa;
                border: 1px solid rgba(255,255,255,0.15); border-radius: 12px; padding: 20px;
                box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.4); font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                backdrop-filter: blur(8px); line-height: 1.4;">
        <h3 style="margin-top: 0; margin-bottom: 12px; font-size: 15px; font-weight: 600; text-align: center; border-bottom: 1px solid rgba(255,255,255,0.1); padding-bottom: 8px;">
            📊 THỐNG KÊ TẬP MẪU HUẤN LUYỆN
        </h3>
        
        <!-- ESA 2021 Stats (Static) -->
        <h4 style="margin-top: 0; margin-bottom: 6px; font-size: 12px; font-weight: 600; color: #ffc107;">
            📁 Mẫu Gốc ESA WorldCover 2021
        </h4>
        <table style="width: 100%; border-collapse: collapse; font-size: 11px; margin-bottom: 12px;">
            <thead>
                <tr style="border-bottom: 1px solid rgba(255,255,255,0.2); text-align: left; color: #ced4da;">
                    <th style="padding: 4px 2px;">Lớp phủ</th>
                    <th style="padding: 4px 2px; text-align: center;">Số lượng</th>
                    <th style="padding: 4px 2px; text-align: right;">Diện tích (ha)</th>
                </tr>
            </thead>
            <tbody>
                <tr style="border-bottom: 1px solid rgba(255,255,255,0.05);">
                    <td style="padding: 4px 2px; display: flex; align-items: center;"><span style="display:inline-block; width:8px; height:8px; background:#1a73e8; margin-right:6px; border-radius:2px;"></span>1. Water</td>
                    <td style="padding: 4px 2px; text-align: center; font-weight: 600;">60</td>
                    <td style="padding: 4px 2px; text-align: right;">59.47</td>
                </tr>
                <tr style="border-bottom: 1px solid rgba(255,255,255,0.05);">
                    <td style="padding: 4px 2px; display: flex; align-items: center;"><span style="display:inline-block; width:8px; height:8px; background:#d35400; margin-right:6px; border-radius:2px;"></span>2. Sand</td>
                    <td style="padding: 4px 2px; text-align: center; font-weight: 600;">85</td>
                    <td style="padding: 4px 2px; text-align: right;">188.72</td>
                </tr>
                <tr style="border-bottom: 1px solid rgba(255,255,255,0.05);">
                    <td style="padding: 4px 2px; display: flex; align-items: center;"><span style="display:inline-block; width:8px; height:8px; background:#e74c3c; margin-right:6px; border-radius:2px;"></span>3. Built-up</td>
                    <td style="padding: 4px 2px; text-align: center; font-weight: 600;">45</td>
                    <td style="padding: 4px 2px; text-align: right;">342.61</td>
                </tr>
                <tr style="border-bottom: 1px solid rgba(255,255,255,0.05);">
                    <td style="padding: 4px 2px; display: flex; align-items: center;"><span style="display:inline-block; width:8px; height:8px; background:#2ecc71; margin-right:6px; border-radius:2px;"></span>4. Others</td>
                    <td style="padding: 4px 2px; text-align: center; font-weight: 600;">60</td>
                    <td style="padding: 4px 2px; text-align: right;">487.56</td>
                </tr>
                <tr style="font-weight: 600; color: #ced4da;">
                    <td style="padding: 6px 2px 2px 2px;">Tổng gốc</td>
                    <td style="padding: 6px 2px 2px 2px; text-align: center;">250</td>
                    <td style="padding: 6px 2px 2px 2px; text-align: right;">1,078.36</td>
                </tr>
            </tbody>
        </table>

        <!-- Manual Stats (Real-time) -->
        <h4 style="margin-top: 12px; margin-bottom: 6px; font-size: 12px; font-weight: 600; color: #00ecff;">
            ✏️ Mẫu Vẽ Tay (Real-time)
        </h4>
        <table style="width: 100%; border-collapse: collapse; font-size: 11px; margin-bottom: 12px;">
            <thead>
                <tr style="border-bottom: 1px solid rgba(255,255,255,0.2); text-align: left; color: #ced4da;">
                    <th style="padding: 4px 2px;">Lớp phủ</th>
                    <th style="padding: 4px 2px; text-align: center;">Số lượng mẫu vẽ tay</th>
                </tr>
            </thead>
            <tbody>
                <tr style="border-bottom: 1px solid rgba(255,255,255,0.05);">
                    <td style="padding: 4px 2px; display: flex; align-items: center;"><span style="display:inline-block; width:8px; height:8px; background:#1a73e8; margin-right:6px; border-radius:2px;"></span>1. Water</td>
                    <td id="man-val-1" style="padding: 4px 2px; text-align: center; font-weight: 600; color: #00ecff;">0</td>
                </tr>
                <tr style="border-bottom: 1px solid rgba(255,255,255,0.05);">
                    <td style="padding: 4px 2px; display: flex; align-items: center;"><span style="display:inline-block; width:8px; height:8px; background:#d35400; margin-right:6px; border-radius:2px;"></span>2. Sand</td>
                    <td id="man-val-2" style="padding: 4px 2px; text-align: center; font-weight: 600; color: #00ecff;">0</td>
                </tr>
                <tr style="border-bottom: 1px solid rgba(255,255,255,0.05);">
                    <td style="padding: 4px 2px; display: flex; align-items: center;"><span style="display:inline-block; width:8px; height:8px; background:#e74c3c; margin-right:6px; border-radius:2px;"></span>3. Built-up</td>
                    <td id="man-val-3" style="padding: 4px 2px; text-align: center; font-weight: 600; color: #00ecff;">0</td>
                </tr>
                <tr style="border-bottom: 1px solid rgba(255,255,255,0.05);">
                    <td style="padding: 4px 2px; display: flex; align-items: center;"><span style="display:inline-block; width:8px; height:8px; background:#2ecc71; margin-right:6px; border-radius:2px;"></span>4. Others</td>
                    <td id="man-val-4" style="padding: 4px 2px; text-align: center; font-weight: 600; color: #00ecff;">0</td>
                </tr>
                <tr style="font-weight: 600; color: #00ecff;">
                    <td style="padding: 6px 2px 2px 2px;">Tổng vẽ tay</td>
                    <td id="man-val-total" style="padding: 6px 2px 2px 2px; text-align: center;">0</td>
                </tr>
            </tbody>
        </table>

        <h4 style="margin-top: 12px; margin-bottom: 6px; font-size: 12px; font-weight: 600; color: #ffc107;">
            ✍️ HƯỚNG DẪN TỰ VẼ MẪU HUẤN LUYỆN
        </h4>
        <ol style="font-size: 10px; padding-left: 14px; margin: 0; line-height: 1.4; color: #ced4da;">
            <li style="margin-bottom: 4px;">Sử dụng công cụ **vẽ đa giác (Polygon)** hoặc **hình chữ nhật (Rectangle)** ở góc trên bên trái.</li>
            <li style="margin-bottom: 4px;">Vẽ mẫu trực tiếp trên nền ảnh vệ tinh Google Satellite hoặc Sentinel-2.</li>
            <li style="margin-bottom: 4px;">Nhập **Class ID** (1, 2, 3 hoặc 4) vào hộp thoại prompt khi vẽ xong.</li>
            <li style="margin-bottom: 4px;">Bấm vào biểu tượng **Tải xuống (Export)** ở thanh công cụ vẽ để tải file GeoJSON chứa các mẫu mới đã gán thuộc tính.</li>
        </ol>
    </div>
    """
    m.get_root().html.add_child(folium.Element(stats_panel_html))

    # Add custom JS listener to prompt for Class ID on polygon creation and update real-time statistics
    prompt_js = """
    <script>
    document.addEventListener("DOMContentLoaded", function() {
        // Find Leaflet map object
        var map_objs = Object.keys(window).filter(key => key.startsWith('map_') && window[key] instanceof L.Map);
        if (map_objs.length > 0) {
            var map = window[map_objs[0]];
            
            // Track manual polygon counts
            var manual_counts = {1: 0, 2: 0, 3: 0, 4: 0};
            
            function updateManualCountsUI() {
                var total = 0;
                for (var c = 1; c <= 4; c++) {
                    var val = manual_counts[c];
                    var el = document.getElementById('man-val-' + c);
                    if (el) el.innerText = val;
                    total += val;
                }
                var tot_el = document.getElementById('man-val-total');
                if (tot_el) tot_el.innerText = total;
            }
            
            map.on(L.Draw.Event.CREATED, function (e) {
                var layer = e.layer;
                var cls = prompt("Nhập Class ID cho polygon này:\\n1: Water (Nước)\\n2: Sand (Cát)\\n3: Built-up (Khu dân cư)\\n4: Others (Khác)");
                if (cls) {
                    var class_names = {1: 'Water', 2: 'Sand', 3: 'Built-up', 4: 'Others'};
                    var c_id = parseInt(cls);
                    if ([1, 2, 3, 4].includes(c_id)) {
                        layer.feature = layer.feature || {};
                        layer.feature.type = "Feature";
                        layer.feature.properties = layer.feature.properties || {};
                        layer.feature.properties.class = c_id;
                        layer.feature.properties.className = class_names[c_id];
                        layer.feature.properties.id = c_id + "_" + Math.random().toString(36).substr(2, 9);
                        layer.bindTooltip("Class: " + class_names[c_id] + " (ID: " + c_id + ")", {permanent: true, direction: 'center'}).openTooltip();
                        
                        // Track class on layer and increment
                        layer.manual_class = c_id;
                        manual_counts[c_id]++;
                        updateManualCountsUI();
                    } else {
                        alert("Class ID không hợp lệ! Vui lòng chỉ nhập 1, 2, 3 hoặc 4.");
                    }
                }
            });
            
            map.on(L.Draw.Event.DELETED, function (e) {
                var layers = e.layers;
                layers.eachLayer(function (layer) {
                    if (layer.manual_class) {
                        manual_counts[layer.manual_class] = Math.max(0, manual_counts[layer.manual_class] - 1);
                    }
                });
                updateManualCountsUI();
            });
        }
    });
    </script>
    """
    m.get_root().html.add_child(folium.Element(prompt_js))

    folium.LayerControl().add_to(m)
    
    # Save checkpoint HTML
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    html_path = os.path.join(OUTPUT_DIR, 'check_training_polygons.html')
    m.save(html_path)
    print(f"\n[QC Success] Saved training polygon verification map to: {html_path}")
    print("==================================================")

if __name__ == '__main__':
    main()
