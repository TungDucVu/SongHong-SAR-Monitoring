"""
Script 02: Tiền xử lý Sentinel-1 & Tính toán đặc trưng
========================================================
Mục đích:
  - Định nghĩa pipeline tiền xử lý SAR:
      [1] Lọc speckle (Refined Lee Filter)
      [2] Clip theo AOI
      [3] Tính đặc trưng: VV, VH, VV/VH ratio
  - Tạo composite tháng (median) cho toàn bộ 2015–2024
  - Kiểm tra giá trị đặc trưng trên các lớp đất: nước, bãi cát, đất

Pipeline:
  Sentinel-1 GRD (dB)
    → Clip AOI
    → Lọc Speckle (Lee Filter 3×3)
    → Tính VV/VH ratio (linear scale)
    → Composite tháng (median)
    → Output: 3-band image (VV, VH, VV_VH_ratio)

Cách chạy:
  python scripts/02_preprocessing.py

Output:
  outputs/preprocessing_stats.json
  outputs/feature_sample_<YYYY_MM>.tif  (qua script 04)
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
print("SONG HONG SAR — 02: Preprocessing & Feature Extraction")
print("=" * 60)

# Load AOI
aoi_path = os.path.normpath(os.path.join(os.path.dirname(__file__), '..', 'aoi', 'song_hong_aoi.geojson'))
with open(aoi_path, 'r', encoding='utf-8') as f:
    aoi_geojson = json.load(f)

aoi_geometry = ee.FeatureCollection(aoi_geojson).geometry()
out_dir = os.path.normpath(os.path.join(os.path.dirname(__file__), '..', 'outputs'))
os.makedirs(out_dir, exist_ok=True)

# ─────────────────────────────────────────────
# 2. Hàm tiền xử lý
# ─────────────────────────────────────────────

def apply_speckle_filter(image):
    """
    Refined Lee Speckle Filter (3×3 kernel).
    Hoạt động trên linear scale, chuyển đổi qua lại từ dB.
    """
    band_names = image.bandNames()

    # Convert từ dB → linear
    img_linear = ee.Image(10.0).pow(image.divide(10.0))

    kernel = ee.Kernel.square(radius=1)  # 3×3

    # Tính mean và variance cục bộ
    mean_img = img_linear.reduceNeighborhood(
        reducer=ee.Reducer.mean(),
        kernel=kernel
    )
    variance_img = img_linear.reduceNeighborhood(
        reducer=ee.Reducer.variance(),
        kernel=kernel
    )

    # Hệ số biến động (coefficient of variation)
    img_cv = variance_img.divide(mean_img.pow(2))

    # Trọng số Lee: w = 1 - ENL_variance / img_cv
    # ENL (Equivalent Number of Looks) ≈ 4.9 cho Sentinel-1 IW
    ENL = 4.9
    ENL_variance = ee.Image(1.0 / ENL)
    weight = ee.Image(1.0).subtract(
        ENL_variance.divide(img_cv.add(ENL_variance))
    ).max(0).min(1)

    # Filtered = mean + weight * (pixel - mean)
    filtered_linear = mean_img.add(
        weight.multiply(img_linear.subtract(mean_img))
    )

    # Convert lại → dB
    filtered_db = filtered_linear.log10().multiply(10.0)
    return filtered_db.rename(band_names).copyProperties(image, image.propertyNames())


def compute_features(image):
    """
    Tính 3 đặc trưng SAR:
      - VV  : backscatter dB (sau lọc speckle)
      - VH  : backscatter dB (sau lọc speckle)
      - VV_VH_ratio : tỉ số VV/VH (linear → dB) = VV - VH
    """
    vv = image.select('VV')
    vh = image.select('VH')

    # Ratio (dB) = VV(dB) - VH(dB)  [= log10(VV_linear/VH_linear) * 10]
    ratio = vv.subtract(vh).rename('VV_VH_ratio')

    return image.addBands(ratio).select(['VV', 'VH', 'VV_VH_ratio'])


def preprocess_image(image):
    """Pipeline đầy đủ cho 1 ảnh."""
    clipped = image.clip(aoi_geometry)
    filtered = apply_speckle_filter(clipped)
    features = compute_features(filtered)
    return features.copyProperties(image, ['system:time_start', 'system:index'])


# ─────────────────────────────────────────────
# 3. Áp dụng pipeline lên collection 2015–2024
# ─────────────────────────────────────────────
s1_raw = (ee.ImageCollection('COPERNICUS/S1_GRD')
            .filterBounds(aoi_geometry)
            .filterDate('2015-01-01', '2024-12-31')
            .filter(ee.Filter.eq('instrumentMode', 'IW'))
            .filter(ee.Filter.eq('orbitProperties_pass', 'DESCENDING'))
            .filter(ee.Filter.listContains('transmitterReceiverPolarisation', 'VV'))
            .filter(ee.Filter.listContains('transmitterReceiverPolarisation', 'VH'))
            .select(['VV', 'VH']))

s1_processed = s1_raw.map(preprocess_image)
print(f"\n✅ Pipeline áp dụng: {s1_processed.size().getInfo()} ảnh đã xử lý")

# ─────────────────────────────────────────────
# 4. Hàm tạo composite tháng
# ─────────────────────────────────────────────

def monthly_composite(year, month):
    """Tạo composite median cho 1 tháng, clip theo AOI."""
    start = ee.Date.fromYMD(year, month, 1)
    end = start.advance(1, 'month')
    composite = (s1_processed
                 .filterDate(start, end)
                 .median()
                 .clip(aoi_geometry))
    return composite.set({
        'year': year,
        'month': month,
        'system:time_start': start.millis(),
        'system:index': ee.String(ee.Number(year).format('%04d'))
                          .cat('_')
                          .cat(ee.String(ee.Number(month).format('%02d')))
    })


# ─────────────────────────────────────────────
# 5. Kiểm tra giá trị đặc trưng (mẫu tháng 1/2024 vs 8/2024)
# ─────────────────────────────────────────────
print("\n📊 Kiểm tra đặc trưng — Tháng 1/2024 (mùa khô) vs 8/2024 (mùa lũ):")

# Điểm kiểm tra: mặt nước sông (Long Bien)
water_point = ee.Geometry.Point([105.8650, 21.0420])
# Điểm kiểm tra: đất / bờ sông
land_point = ee.Geometry.Point([105.8700, 21.0500])

for year, month, label in [(2024, 1, 'Mùa khô (T1/2024)'), (2024, 8, 'Mùa lũ  (T8/2024)')]:
    comp = monthly_composite(year, month)
    scale = 10  # Sentinel-1 resolution 10m

    water_val = comp.reduceRegion(
        reducer=ee.Reducer.mean(),
        geometry=water_point.buffer(100),
        scale=scale
    ).getInfo()

    land_val = comp.reduceRegion(
        reducer=ee.Reducer.mean(),
        geometry=land_point.buffer(100),
        scale=scale
    ).getInfo()

    print(f"\n  [{label}]")
    if water_val.get('VV') is not None:
        print(f"    Điểm NƯỚC  → VV={water_val.get('VV', 'N/A'):.2f} dB | "
              f"VH={water_val.get('VH', 'N/A'):.2f} dB | "
              f"Ratio={water_val.get('VV_VH_ratio', 'N/A'):.2f} dB")
        print(f"    Điểm ĐẤT   → VV={land_val.get('VV', 'N/A'):.2f} dB | "
              f"VH={land_val.get('VH', 'N/A'):.2f} dB | "
              f"Ratio={land_val.get('VV_VH_ratio', 'N/A'):.2f} dB")

        # Kiểm tra ngưỡng
        vv_water = water_val.get('VV', 0)
        if vv_water < -15:
            print(f"    ✅ VV mặt nước = {vv_water:.2f} dB < -15 dB (đạt tiêu chí)")
        else:
            print(f"    ⚠️  VV mặt nước = {vv_water:.2f} dB — kiểm tra lại điểm tham chiếu")
    else:
        print(f"    ⚠️  Không có dữ liệu cho tháng này tại điểm kiểm tra")

# ─────────────────────────────────────────────
# 6. Lưu thông tin pipeline
# ─────────────────────────────────────────────
pipeline_info = {
    'generated_at': datetime.utcnow().isoformat() + 'Z',
    'pipeline_steps': [
        '1. Filter: IW mode, DESCENDING, VV+VH bands',
        '2. Clip to AOI',
        '3. Refined Lee Speckle Filter (3×3, ENL=4.9)',
        '4. Feature: VV_VH_ratio = VV(dB) - VH(dB)',
        '5. Monthly median composite'
    ],
    'output_bands': ['VV', 'VH', 'VV_VH_ratio'],
    'expected_values': {
        'water_VV_dB': '< -15',
        'land_VV_dB': '> -10',
        'sandbars_VV_dB': '-15 to -10 (intermediate)'
    }
}

stats_path = os.path.join(out_dir, 'preprocessing_stats.json')
with open(stats_path, 'w', encoding='utf-8') as f:
    json.dump(pipeline_info, f, indent=2, ensure_ascii=False)

print(f"\n✅ Pipeline info lưu: {stats_path}")
print("\n" + "=" * 60)
print("✅ PREPROCESSING PIPELINE READY")
print("   Dùng monthly_composite(year, month) để tạo ảnh bất kỳ")
print("=" * 60)
