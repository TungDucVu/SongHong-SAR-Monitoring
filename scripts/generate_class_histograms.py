import sys
import os
import matplotlib.pyplot as plt
import numpy as np

sys.path.insert(0, os.getcwd())

import ee
from src.config import GEE_PROJECT
from src.aoi import get_aoi_geometry
from src.collection import create_seasonal_composite

print("Initializing GEE...")
ee.Initialize(project=GEE_PROJECT)

# 1. Load 2024 Dry Composite
print("Loading AOI and generating 2024 Dry composite on-the-fly...")
aoi_geometry = get_aoi_geometry()
composite = create_seasonal_composite(2024, 'dry', aoi_geometry)

# 2. Define 3 representative Water center points (Upstream, Middle, Downstream)
water_centers = [
    [105.8600, 21.0400],  # Middle (Near Long Bien Bridge)
    [105.8377, 21.0860],  # Upstream (Near Nhat Tan Bridge)
    [105.8905, 20.9291]   # Downstream (Near Thanh Tri Bridge)
]

# Define 3 representative Land/Mudflat center points (Upstream, Middle, Downstream)
land_centers = [
    [105.8650, 21.0460],  # Middle (Bãi Giữa island)
    [105.8450, 21.0880],  # Upstream (Alluvial island near Nhat Tan)
    [105.8960, 20.9330]   # Downstream (Alluvial bank near Thanh Tri)
]

def make_100m_box(center):
    cx, cy = center
    # 100m is approx 0.0009 degrees
    half_size = 0.00045
    return ee.Geometry.Rectangle([cx - half_size, cy - half_size, cx + half_size, cy + half_size])

water_geoms = [make_100m_box(pt) for pt in water_centers]
land_geoms = [make_100m_box(pt) for pt in land_centers]

print("Sampling pixels at full 10m scale for each sub-polygon...")
water_vv = []
water_vh = []
land_vv = []
land_vh = []

# Sample Water sub-polygons
for i, geom in enumerate(water_geoms):
    print(f"  Sampling Water Zone {i+1}...")
    samples = composite.select(['VV', 'VH']).sample(
        region=geom,
        scale=10,
        numPixels=200,
        geometries=False
    )
    features = samples.getInfo().get('features', [])
    for f in features:
        props = f.get('properties', {})
        if props.get('VV') is not None:
            water_vv.append(props['VV'])
        if props.get('VH') is not None:
            water_vh.append(props['VH'])

# Sample Land sub-polygons
for i, geom in enumerate(land_geoms):
    print(f"  Sampling Land Zone {i+1}...")
    samples = composite.select(['VV', 'VH']).sample(
        region=geom,
        scale=10,
        numPixels=200,
        geometries=False
    )
    features = samples.getInfo().get('features', [])
    for f in features:
        props = f.get('properties', {})
        if props.get('VV') is not None:
            land_vv.append(props['VV'])
        if props.get('VH') is not None:
            land_vh.append(props['VH'])

print(f"Total samples collected:")
print(f"  - Water pixels: {len(water_vv)}")
print(f"  - Land pixels: {len(land_vv)}")

# Calculate and print stats
print("\n--- STATISTICS ---")
print('WATER VV: Mean={:.2f}, Std={:.2f}, Min={:.2f}, Max={:.2f}'.format(np.mean(water_vv), np.std(water_vv), np.min(water_vv), np.max(water_vv)))
print('WATER VH: Mean={:.2f}, Std={:.2f}, Min={:.2f}, Max={:.2f}'.format(np.mean(water_vh), np.std(water_vh), np.min(water_vh), np.max(water_vh)))
print('LAND VV: Mean={:.2f}, Std={:.2f}, Min={:.2f}, Max={:.2f}'.format(np.mean(land_vv), np.std(land_vv), np.min(land_vv), np.max(land_vv)))
print('LAND VH: Mean={:.2f}, Std={:.2f}, Min={:.2f}, Max={:.2f}'.format(np.mean(land_vh), np.std(land_vh), np.min(land_vh), np.max(land_vh)))

# 3. Plotting Histograms
fig, axes = plt.subplots(1, 2, figsize=(14, 6))

water_color = '#1f77b4'
land_color = '#d95f02'

# Subplot 1: VV Band
axes[0].hist(water_vv, bins=20, range=(-25, -2), color=water_color, alpha=0.6, label='Vùng nước (Water)', edgecolor='black', density=True)
axes[0].hist(land_vv, bins=20, range=(-25, -2), color=land_color, alpha=0.6, label='Bãi bồi / Đất (Land)', edgecolor='black', density=True)
axes[0].set_title('Phân bố phản xạ VV (VV Backscatter)', fontsize=13, fontweight='bold')
axes[0].set_xlabel('Giá trị Backscatter (dB)', fontsize=11)
axes[0].set_ylabel('Mật độ phân bố (Density)', fontsize=11)
axes[0].grid(True, linestyle='--', alpha=0.5)
axes[0].legend(fontsize=10)

# Subplot 2: VH Band
axes[1].hist(water_vh, bins=20, range=(-30, -5), color=water_color, alpha=0.6, label='Vùng nước (Water)', edgecolor='black', density=True)
axes[1].hist(land_vh, bins=20, range=(-30, -5), color=land_color, alpha=0.6, label='Bãi bồi / Đất (Land)', edgecolor='black', density=True)
axes[1].set_title('Phân bố phản xạ VH (VH Backscatter)', fontsize=13, fontweight='bold')
axes[1].set_xlabel('Giá trị Backscatter (dB)', fontsize=11)
axes[1].set_ylabel('Mật độ phân bố (Density)', fontsize=11)
axes[1].grid(True, linestyle='--', alpha=0.5)
axes[1].legend(fontsize=10)

plt.suptitle('So sánh phân bố tín hiệu radar Sentinel-1: Vùng Nước vs. Bãi Bồi/Đất (2024 Dry)\n(Gộp từ 3 vùng lấy mẫu 100x100m đại diện)', fontsize=15, fontweight='bold', y=0.98)
plt.tight_layout()

os.makedirs('outputs', exist_ok=True)
output_plot_path = 'outputs/histogram_classes_2024_dry.png'
plt.savefig(output_plot_path, dpi=200)
plt.close()

print(f"Plot saved successfully to: {output_plot_path}")
