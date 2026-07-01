"""
Script 00: Kiểm tra môi trường Google Earth Engine
===================================================
Mục đích:
  - Khởi tạo kết nối GEE với project crested-library-500309-i2
  - Load AOI từ file GeoJSON local
  - Kiểm tra kết nối dataset COPERNICUS/S1_GRD
  - In metadata ảnh Sentinel-1 đầu tiên trong AOI
  - Hiển thị bản đồ tương tác với geemap

Cách chạy:
  python scripts/00_environment_check.py

Yêu cầu:
  pip install earthengine-api geemap
  earthengine authenticate  (chạy 1 lần)
"""

import ee
import geemap
import json
import os

# ─────────────────────────────────────────────
# 1. Khởi tạo GEE
# ─────────────────────────────────────────────
print("=" * 50)
print("SONG HONG SAR MONITORING — Environment Check")
print("=" * 50)

ee.Initialize(project='crested-library-500309-i2')
print("✅ GEE initialized: project = crested-library-500309-i2\n")

# ─────────────────────────────────────────────
# 2. Load AOI từ GeoJSON local
# ─────────────────────────────────────────────
aoi_path = os.path.join(os.path.dirname(__file__), '..', 'aoi', 'song_hong_aoi.geojson')
aoi_path = os.path.normpath(aoi_path)

with open(aoi_path, 'r', encoding='utf-8') as f:
    aoi_geojson = json.load(f)

aoi = ee.FeatureCollection(aoi_geojson)
aoi_geometry = aoi.geometry()

print(f"✅ AOI loaded from: {aoi_path}")

# In thông tin AOI
aoi_info = aoi.first().getInfo()
props = aoi_info['properties']
print(f"   Name       : {props.get('name', 'N/A')}")
print(f"   Description: {props.get('description', 'N/A')}")
print(f"   Area ~     : {props.get('area_km2_approx', 'N/A')} km²\n")

# ─────────────────────────────────────────────
# 3. Kiểm tra dataset Sentinel-1
# ─────────────────────────────────────────────
s1 = (ee.ImageCollection('COPERNICUS/S1_GRD')
        .filterBounds(aoi_geometry)
        .filterDate('2024-01-01', '2024-12-31')
        .filter(ee.Filter.eq('instrumentMode', 'IW'))
        .filter(ee.Filter.eq('orbitProperties_pass', 'DESCENDING'))
        .filter(ee.Filter.listContains('transmitterReceiverPolarisation', 'VV'))
        .filter(ee.Filter.listContains('transmitterReceiverPolarisation', 'VH'))
        .select(['VV', 'VH']))

count_2024 = s1.size().getInfo()
print(f"✅ Sentinel-1 GRD (IW, DESCENDING, 2024): {count_2024} ảnh\n")

# Metadata ảnh đầu tiên
first_img = s1.first()
first_info = first_img.getInfo()
print("📋 Metadata ảnh đầu tiên:")
print(f"   ID         : {first_info['id']}")
print(f"   Date       : {first_info['properties'].get('system:index', 'N/A')}")
print(f"   Bands      : {[b['id'] for b in first_info['bands']]}")
print(f"   Resolution : {first_info['bands'][0].get('crs_transform', 'N/A')}\n")

# ─────────────────────────────────────────────
# 4. Hiển thị bản đồ tương tác
# ─────────────────────────────────────────────
print("🗺️  Đang khởi tạo bản đồ tương tác (geemap)...")

Map = geemap.Map(center=[21.0, 105.75], zoom=10)
Map.add_basemap('SATELLITE')

# Thêm AOI
Map.addLayer(aoi_geometry, {'color': 'red', 'width': 2}, 'AOI - Song Hong')

# Thêm ảnh VV composite (median tháng 6/2024 - mùa lũ)
s1_june = (ee.ImageCollection('COPERNICUS/S1_GRD')
             .filterBounds(aoi_geometry)
             .filterDate('2024-06-01', '2024-06-30')
             .filter(ee.Filter.eq('instrumentMode', 'IW'))
             .filter(ee.Filter.eq('orbitProperties_pass', 'DESCENDING'))
             .filter(ee.Filter.listContains('transmitterReceiverPolarisation', 'VV'))
             .filter(ee.Filter.listContains('transmitterReceiverPolarisation', 'VH'))
             .select(['VV', 'VH'])
             .median()
             .clip(aoi_geometry))

vv_vis = {'bands': ['VV'], 'min': -25, 'max': 0, 'palette': ['black', 'white']}
Map.addLayer(s1_june, vv_vis, 'Sentinel-1 VV (Jun 2024)')
Map.centerObject(aoi_geometry, 10)

# Lưu bản đồ ra HTML
out_html = os.path.normpath(os.path.join(os.path.dirname(__file__), '..', 'outputs', 'map_check.html'))
os.makedirs(os.path.dirname(out_html), exist_ok=True)
Map.to_html(out_html)

print(f"✅ Bản đồ đã lưu: {out_html}")
print("\n" + "=" * 50)
print("✅ ENVIRONMENT CHECK PASSED")
print("=" * 50)
