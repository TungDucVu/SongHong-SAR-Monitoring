"""
Script 01: Thu thập dữ liệu Sentinel-1 GRD
===========================================
Mục đích:
  - Lọc toàn bộ ảnh Sentinel-1 GRD trong AOI giai đoạn 2015-2024
  - Thống kê số lượng ảnh theo năm và theo tháng
  - Kiểm tra gap dữ liệu (năm/tháng bị thiếu)
  - Lưu báo cáo thống kê ra file CSV và JSON

Cách chạy:
  python scripts/01_data_collection.py

Output:
  outputs/s1_coverage_by_year.csv
  outputs/s1_coverage_by_month.csv
  outputs/s1_metadata.json
"""

import ee
import json
import os
import csv
from datetime import datetime

# ─────────────────────────────────────────────
# 1. Khởi tạo
# ─────────────────────────────────────────────
ee.Initialize(project='crested-library-500309-i2')
print("=" * 60)
print("SONG HONG SAR — 01: Data Collection (2015–2024)")
print("=" * 60)

# Load AOI
aoi_path = os.path.normpath(os.path.join(os.path.dirname(__file__), '..', 'aoi', 'song_hong_aoi.geojson'))
with open(aoi_path, 'r', encoding='utf-8') as f:
    aoi_geojson = json.load(f)

aoi_geometry = ee.FeatureCollection(aoi_geojson).geometry()
out_dir = os.path.normpath(os.path.join(os.path.dirname(__file__), '..', 'outputs'))
os.makedirs(out_dir, exist_ok=True)

# ─────────────────────────────────────────────
# 2. Truy vấn toàn bộ collection 2015–2024
# ─────────────────────────────────────────────
s1_all = (ee.ImageCollection('COPERNICUS/S1_GRD')
            .filterBounds(aoi_geometry)
            .filterDate('2015-01-01', '2024-12-31')
            .filter(ee.Filter.eq('instrumentMode', 'IW'))
            .filter(ee.Filter.eq('orbitProperties_pass', 'DESCENDING'))
            .filter(ee.Filter.listContains('transmitterReceiverPolarisation', 'VV'))
            .filter(ee.Filter.listContains('transmitterReceiverPolarisation', 'VH'))
            .select(['VV', 'VH']))

total = s1_all.size().getInfo()
print(f"\n📊 Tổng số ảnh (2015–2024): {total}")

if total < 500:
    print("⚠️  WARNING: Số ảnh < 500, kiểm tra lại AOI hoặc bộ lọc!")
else:
    print("✅ Đủ dữ liệu cho phân tích chuỗi thời gian 10 năm")

# ─────────────────────────────────────────────
# 3. Thống kê theo năm
# ─────────────────────────────────────────────
print("\n📅 Số ảnh theo năm:")
print(f"{'Năm':<8} {'Số ảnh':<10} {'Tình trạng'}")
print("-" * 35)

years = list(range(2015, 2025))
year_stats = []

for year in years:
    count = (s1_all
             .filter(ee.Filter.calendarRange(year, year, 'year'))
             .size()
             .getInfo())
    status = "✅ OK" if count >= 20 else "⚠️  Thiếu" if count > 0 else "❌ Không có"
    print(f"{year:<8} {count:<10} {status}")
    year_stats.append({'year': year, 'count': count, 'status': status.strip()})

# ─────────────────────────────────────────────
# 4. Thống kê theo tháng (giai đoạn 2020–2024)
# ─────────────────────────────────────────────
print("\n📅 Số ảnh theo tháng (2020–2024 — giai đoạn chính):")
month_names = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun',
               'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
month_stats = []

s1_recent = s1_all.filterDate('2020-01-01', '2024-12-31')

for month in range(1, 13):
    count = (s1_recent
             .filter(ee.Filter.calendarRange(month, month, 'month'))
             .size()
             .getInfo())
    bar = '█' * (count // 2)
    print(f"  {month_names[month-1]:<5} {count:>3}  {bar}")
    month_stats.append({'month': month, 'month_name': month_names[month-1], 'count': count})

# ─────────────────────────────────────────────
# 5. Lấy metadata chi tiết (10 ảnh đầu)
# ─────────────────────────────────────────────
print("\n📋 Metadata 5 ảnh đầu tiên:")
first_5 = s1_all.sort('system:time_start').limit(5)
first_5_info = first_5.getInfo()

metadata_list = []
for feat in first_5_info['features']:
    props = feat['properties']
    img_id = props.get('system:index', 'N/A')
    ts = props.get('system:time_start', 0)
    date_str = datetime.utcfromtimestamp(ts / 1000).strftime('%Y-%m-%d') if ts else 'N/A'
    rel_orbit = props.get('relativeOrbitNumber_start', 'N/A')
    print(f"  [{date_str}] ID={img_id} | Orbit={rel_orbit}")
    metadata_list.append({'id': img_id, 'date': date_str, 'relative_orbit': rel_orbit})

# ─────────────────────────────────────────────
# 6. Lưu kết quả
# ─────────────────────────────────────────────

# CSV theo năm
csv_year_path = os.path.join(out_dir, 's1_coverage_by_year.csv')
with open(csv_year_path, 'w', newline='', encoding='utf-8') as f:
    writer = csv.DictWriter(f, fieldnames=['year', 'count', 'status'])
    writer.writeheader()
    writer.writerows(year_stats)
print(f"\n✅ Lưu: {csv_year_path}")

# CSV theo tháng
csv_month_path = os.path.join(out_dir, 's1_coverage_by_month.csv')
with open(csv_month_path, 'w', newline='', encoding='utf-8') as f:
    writer = csv.DictWriter(f, fieldnames=['month', 'month_name', 'count'])
    writer.writeheader()
    writer.writerows(month_stats)
print(f"✅ Lưu: {csv_month_path}")

# JSON metadata
json_path = os.path.join(out_dir, 's1_metadata.json')
report = {
    'generated_at': datetime.utcnow().isoformat() + 'Z',
    'project': 'crested-library-500309-i2',
    'total_images_2015_2024': total,
    'filter_params': {
        'instrument_mode': 'IW',
        'orbit_direction': 'DESCENDING',
        'polarisation': ['VV', 'VH']
    },
    'year_stats': year_stats,
    'month_stats_2020_2024': month_stats,
    'sample_metadata': metadata_list
}
with open(json_path, 'w', encoding='utf-8') as f:
    json.dump(report, f, indent=2, ensure_ascii=False)
print(f"✅ Lưu: {json_path}")

print("\n" + "=" * 60)
print(f"✅ DATA COLLECTION DONE — {total} ảnh sẵn sàng")
print("=" * 60)
