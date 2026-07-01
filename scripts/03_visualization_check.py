"""
Script 03: Kiểm tra trực quan kết quả tiền xử lý
=================================================
Mục đích:
  - Tạo bản đồ tương tác so sánh ảnh mùa khô vs mùa lũ
  - Hiển thị 3 band: VV, VH, VV/VH ratio
  - Thêm layer Sentinel-2 RGB để đối chiếu trực quan
  - Lưu bản đồ HTML ra thư mục outputs/

Cách chạy:
  python scripts/03_visualization_check.py

Output:
  outputs/visualization_dry_wet.html   (mở bằng trình duyệt)
  outputs/visualization_features.html  (3-panel: VV, VH, ratio)
"""

import ee
import geemap
import json
import os
import sys

# Import preprocessing pipeline từ script 02
sys.path.insert(0, os.path.dirname(__file__))

# ─────────────────────────────────────────────
# 1. Khởi tạo
# ─────────────────────────────────────────────
ee.Initialize(project='crested-library-500309-i2')
print("=" * 60)
print("SONG HONG SAR — 03: Visualization Check")
print("=" * 60)

# Load AOI
aoi_path = os.path.normpath(os.path.join(os.path.dirname(__file__), '..', 'aoi', 'song_hong_aoi.geojson'))
with open(aoi_path, 'r', encoding='utf-8') as f:
    aoi_geojson = json.load(f)

aoi_geometry = ee.FeatureCollection(aoi_geojson).geometry()
out_dir = os.path.normpath(os.path.join(os.path.dirname(__file__), '..', 'outputs'))
os.makedirs(out_dir, exist_ok=True)

# ─────────────────────────────────────────────
# 2. Copy pipeline từ script 02 (standalone)
# ─────────────────────────────────────────────

def apply_speckle_filter(image):
    band_names = image.bandNames()
    img_linear = ee.Image(10.0).pow(image.divide(10.0))
    kernel = ee.Kernel.square(radius=1)
    mean_img = img_linear.reduceNeighborhood(ee.Reducer.mean(), kernel)
    variance_img = img_linear.reduceNeighborhood(ee.Reducer.variance(), kernel)
    img_cv = variance_img.divide(mean_img.pow(2))
    ENL_variance = ee.Image(1.0 / 4.9)
    weight = ee.Image(1.0).subtract(ENL_variance.divide(img_cv.add(ENL_variance))).max(0).min(1)
    filtered_linear = mean_img.add(weight.multiply(img_linear.subtract(mean_img)))
    filtered_db = filtered_linear.log10().multiply(10.0)
    return filtered_db.rename(band_names).copyProperties(image, image.propertyNames())

def compute_features(image):
    vv = image.select('VV')
    vh = image.select('VH')
    ratio = vv.subtract(vh).rename('VV_VH_ratio')
    return image.addBands(ratio).select(['VV', 'VH', 'VV_VH_ratio'])

def preprocess_image(image):
    clipped = image.clip(aoi_geometry)
    filtered = apply_speckle_filter(clipped)
    return compute_features(filtered).copyProperties(image, ['system:time_start', 'system:index'])

s1_processed = (ee.ImageCollection('COPERNICUS/S1_GRD')
                  .filterBounds(aoi_geometry)
                  .filterDate('2020-01-01', '2024-12-31')
                  .filter(ee.Filter.eq('instrumentMode', 'IW'))
                  .filter(ee.Filter.eq('orbitProperties_pass', 'DESCENDING'))
                  .filter(ee.Filter.listContains('transmitterReceiverPolarisation', 'VV'))
                  .filter(ee.Filter.listContains('transmitterReceiverPolarisation', 'VH'))
                  .select(['VV', 'VH'])
                  .map(preprocess_image))

# ─────────────────────────────────────────────
# 3. Tạo composite mùa khô và mùa lũ
# ─────────────────────────────────────────────
def season_composite(months, years=(2020, 2024)):
    """Composite median cho nhiều năm, chọn theo tháng."""
    month_filter = ee.Filter.calendarRange(months[0], months[-1], 'month')
    return (s1_processed
            .filterDate(f'{years[0]}-01-01', f'{years[1]}-12-31')
            .filter(month_filter)
            .median()
            .clip(aoi_geometry))

# Mùa khô: tháng 11–4 (ít mưa, mực nước thấp)
dry_composite   = season_composite([11, 4])  # Nov–Apr (sẽ dùng calendarRange riêng)
# Cách đơn giản hơn:
dry_composite = (s1_processed
                 .filterDate('2020-01-01', '2024-12-31')
                 .filter(ee.Filter.Or(
                     ee.Filter.calendarRange(11, 12, 'month'),
                     ee.Filter.calendarRange(1, 4, 'month')
                 ))
                 .median()
                 .clip(aoi_geometry))

# Mùa lũ: tháng 6–9 (mực nước cao, bãi bồi ngập)
wet_composite = (s1_processed
                 .filterDate('2020-01-01', '2024-12-31')
                 .filter(ee.Filter.calendarRange(6, 9, 'month'))
                 .median()
                 .clip(aoi_geometry))

print("\n✅ Composite mùa khô và mùa lũ đã sẵn sàng")

# ─────────────────────────────────────────────
# 4. Cài đặt hiển thị màu
# ─────────────────────────────────────────────
vis_vv = {
    'bands': ['VV'], 'min': -25, 'max': 0,
    'palette': ['#000033', '#003399', '#0099FF', '#FFFFFF']
}
vis_vh = {
    'bands': ['VH'], 'min': -30, 'max': -5,
    'palette': ['#000033', '#003399', '#0099FF', '#FFFFFF']
}
vis_ratio = {
    'bands': ['VV_VH_ratio'], 'min': 2, 'max': 15,
    'palette': ['#440154', '#31688E', '#35B779', '#FDE725']  # Viridis
}

# ─────────────────────────────────────────────
# 5. Bản đồ 1: So sánh mùa khô vs mùa lũ (VV band)
# ─────────────────────────────────────────────
print("\n🗺️  Tạo bản đồ 1: So sánh mùa khô vs mùa lũ...")

Map1 = geemap.Map(center=[21.0, 105.75], zoom=10)
Map1.add_basemap('SATELLITE')
Map1.addLayer(aoi_geometry, {'color': 'yellow', 'width': 1}, 'AOI')
Map1.addLayer(dry_composite,  vis_vv, 'VV — Mùa khô (Nov–Apr)')
Map1.addLayer(wet_composite,  vis_vv, 'VV — Mùa lũ (Jun–Sep)')

# Điểm tham chiếu
key_points = ee.FeatureCollection([
    ee.Feature(ee.Geometry.Point([105.8650, 21.0420]), {'name': 'Long Bien - Song'}),
    ee.Feature(ee.Geometry.Point([105.8500, 21.0800]), {'name': 'Nhat Tan - Song'}),
    ee.Feature(ee.Geometry.Point([105.8800, 20.9900]), {'name': 'Vinh Tuy - Song'}),
])
Map1.addLayer(key_points, {'color': 'red'}, 'Khu vực trọng điểm')

html1 = os.path.join(out_dir, 'visualization_dry_wet.html')
Map1.to_html(html1)
print(f"   ✅ Lưu: {html1}")

# ─────────────────────────────────────────────
# 6. Bản đồ 2: 3 đặc trưng (VV, VH, Ratio) — tháng 1/2024
# ─────────────────────────────────────────────
print("\n🗺️  Tạo bản đồ 2: Ba đặc trưng SAR (tháng 1/2024)...")

jan2024 = (s1_processed
           .filterDate('2024-01-01', '2024-01-31')
           .median()
           .clip(aoi_geometry))

Map2 = geemap.Map(center=[21.0, 105.75], zoom=10)
Map2.add_basemap('SATELLITE')
Map2.addLayer(aoi_geometry, {'color': 'yellow', 'width': 1}, 'AOI')
Map2.addLayer(jan2024, vis_vv,    'VV band (dB)')
Map2.addLayer(jan2024, vis_vh,    'VH band (dB)')
Map2.addLayer(jan2024, vis_ratio, 'VV/VH Ratio (dB)')

html2 = os.path.join(out_dir, 'visualization_features.html')
Map2.to_html(html2)
print(f"   ✅ Lưu: {html2}")

# ─────────────────────────────────────────────
# 7. Thêm Sentinel-2 RGB để đối chiếu
# ─────────────────────────────────────────────
print("\n🛰️  Thêm Sentinel-2 RGB để đối chiếu...")

s2 = (ee.ImageCollection('COPERNICUS/S2_SR_HARMONIZED')
        .filterBounds(aoi_geometry)
        .filterDate('2024-01-01', '2024-01-31')
        .filter(ee.Filter.lt('CLOUDY_PIXEL_PERCENTAGE', 20))
        .select(['B4', 'B3', 'B2'])  # RGB
        .median()
        .clip(aoi_geometry))

Map2.addLayer(s2, {'bands': ['B4', 'B3', 'B2'], 'min': 0, 'max': 3000}, 'Sentinel-2 RGB (Jan 2024)')
Map2.to_html(html2)  # Ghi đè để cập nhật
print(f"   ✅ Cập nhật: {html2}")

print("\n" + "=" * 60)
print("✅ VISUALIZATION DONE")
print(f"   Mở bằng trình duyệt:")
print(f"   - {html1}")
print(f"   - {html2}")
print("=" * 60)
