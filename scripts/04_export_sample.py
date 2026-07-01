"""
Script 04: Export ảnh composite mẫu ra Google Drive
====================================================
Mục đích:
  - Export composite tháng 1/2020 (mùa khô) ra Google Drive dạng GeoTIFF
  - Export composite tháng 8/2020 (mùa lũ) để so sánh
  - File dùng để kiểm tra ngoài GEE bằng QGIS/Python
  - Format: GeoTIFF, CRS: EPSG:32648 (UTM Zone 48N), Scale: 10m

Cách chạy:
  python scripts/04_export_sample.py

Output (Google Drive — thư mục SongHong_SAR/):
  SongHong_S1_Composite_2020_01_dry.tif
  SongHong_S1_Composite_2020_08_wet.tif
  SongHong_S1_Annual_2024.tif

Sau khi chạy:
  - Kiểm tra task đang chạy tại: https://code.earthengine.google.com/tasks
  - Download file từ Google Drive
  - Mở bằng QGIS, kiểm tra 3 band (VV, VH, VV_VH_ratio)
"""

import ee
import json
import os
from datetime import datetime

# ─────────────────────────────────────────────
# 1. Khởi tạo
# ─────────────────────────────────────────────
ee.Initialize(project='crested-library-500309-i2')
print("=" * 60)
print("SONG HONG SAR — 04: Export Sample Composites")
print("=" * 60)

# Load AOI
aoi_path = os.path.normpath(os.path.join(os.path.dirname(__file__), '..', 'aoi', 'song_hong_aoi.geojson'))
with open(aoi_path, 'r', encoding='utf-8') as f:
    aoi_geojson = json.load(f)

aoi_geometry = ee.FeatureCollection(aoi_geojson).geometry()

# ─────────────────────────────────────────────
# 2. Pipeline tiền xử lý (standalone)
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
    return compute_features(
        apply_speckle_filter(image.clip(aoi_geometry))
    ).copyProperties(image, ['system:time_start', 'system:index'])

def get_monthly_composite(year, month):
    """Trả về composite median của 1 tháng cụ thể."""
    start = f'{year}-{month:02d}-01'
    end_date = ee.Date.fromYMD(year, month, 1).advance(1, 'month')
    end = end_date.format('YYYY-MM-dd').getInfo()

    composite = (ee.ImageCollection('COPERNICUS/S1_GRD')
                   .filterBounds(aoi_geometry)
                   .filterDate(start, end)
                   .filter(ee.Filter.eq('instrumentMode', 'IW'))
                   .filter(ee.Filter.eq('orbitProperties_pass', 'DESCENDING'))
                   .filter(ee.Filter.listContains('transmitterReceiverPolarisation', 'VV'))
                   .filter(ee.Filter.listContains('transmitterReceiverPolarisation', 'VH'))
                   .select(['VV', 'VH'])
                   .map(preprocess_image)
                   .median()
                   .clip(aoi_geometry))
    return composite

def get_annual_composite(year):
    """Composite median toàn năm."""
    composite = (ee.ImageCollection('COPERNICUS/S1_GRD')
                   .filterBounds(aoi_geometry)
                   .filterDate(f'{year}-01-01', f'{year}-12-31')
                   .filter(ee.Filter.eq('instrumentMode', 'IW'))
                   .filter(ee.Filter.eq('orbitProperties_pass', 'DESCENDING'))
                   .filter(ee.Filter.listContains('transmitterReceiverPolarisation', 'VV'))
                   .filter(ee.Filter.listContains('transmitterReceiverPolarisation', 'VH'))
                   .select(['VV', 'VH'])
                   .map(preprocess_image)
                   .median()
                   .clip(aoi_geometry))
    return composite

# ─────────────────────────────────────────────
# 3. Tạo các ảnh cần export
# ─────────────────────────────────────────────
exports = [
    {
        'image': get_monthly_composite(2020, 1),
        'description': 'SongHong_S1_Composite_2020_01_dry',
        'label': 'Tháng 1/2020 — Mùa khô'
    },
    {
        'image': get_monthly_composite(2020, 8),
        'description': 'SongHong_S1_Composite_2020_08_wet',
        'label': 'Tháng 8/2020 — Mùa lũ'
    },
    {
        'image': get_annual_composite(2024),
        'description': 'SongHong_S1_Annual_2024',
        'label': 'Composite cả năm 2024'
    }
]

# ─────────────────────────────────────────────
# 4. Submit export tasks
# ─────────────────────────────────────────────
print(f"\n📤 Submitting {len(exports)} export tasks...\n")

task_ids = []
for exp in exports:
    task = ee.batch.Export.image.toDrive(
        image=exp['image'],
        description=exp['description'],
        folder='SongHong_SAR',             # Tạo thư mục này trên Google Drive
        fileNamePrefix=exp['description'],
        region=aoi_geometry,
        scale=10,                           # 10m resolution (Sentinel-1 native)
        crs='EPSG:32648',                   # UTM Zone 48N — phù hợp với Hà Nội
        maxPixels=1e10,
        fileFormat='GeoTIFF'
    )
    task.start()
    task_id = task.id
    task_ids.append({'label': exp['label'], 'id': task_id, 'description': exp['description']})
    print(f"  ✅ [{exp['label']}]")
    print(f"     Task ID: {task_id}")
    print(f"     File   : SongHong_SAR/{exp['description']}.tif\n")

# ─────────────────────────────────────────────
# 5. Lưu task IDs để theo dõi
# ─────────────────────────────────────────────
out_dir = os.path.normpath(os.path.join(os.path.dirname(__file__), '..', 'outputs'))
os.makedirs(out_dir, exist_ok=True)

tasks_log = {
    'submitted_at': datetime.utcnow().isoformat() + 'Z',
    'tasks': task_ids,
    'check_status': 'https://code.earthengine.google.com/tasks',
    'drive_folder': 'SongHong_SAR',
    'verification': {
        'open_with': 'QGIS hoặc Python (rasterio)',
        'expected_bands': ['VV', 'VH', 'VV_VH_ratio'],
        'expected_crs': 'EPSG:32648',
        'expected_scale_m': 10,
        'VV_water_expected': '< -15 dB',
        'VV_land_expected': '> -10 dB'
    }
}

log_path = os.path.join(out_dir, 'export_tasks.json')
with open(log_path, 'w', encoding='utf-8') as f:
    json.dump(tasks_log, f, indent=2, ensure_ascii=False)
print(f"✅ Task log lưu: {log_path}")

print("\n" + "=" * 60)
print("✅ EXPORT SUBMITTED")
print("   Theo dõi tại: https://code.earthengine.google.com/tasks")
print("   Thường hoàn thành trong 5–15 phút")
print("=" * 60)
