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

# 2. Define representative polygons for Water and Land/Mudflat (Bãi giữa Sông Hồng)
# Water channel near Long Bien Bridge
water_polygon = ee.Geometry.Polygon([
    [[105.858, 21.038], [105.862, 21.038], [105.862, 21.042], [105.858, 21.042]]
])

# Land/Mudflat island (Bãi Giữa)
land_polygon = ee.Geometry.Polygon([
    [[105.862, 21.044], [105.868, 21.044], [105.868, 21.050], [105.862, 21.050]]
])

print("Sampling pixels at full 10m scale...")
# Sample up to 1000 pixels for each class
water_samples = composite.select(['VV', 'VH']).sample(
    region=water_polygon,
    scale=10,
    numPixels=1000,
    geometries=False
)

land_samples = composite.select(['VV', 'VH']).sample(
    region=land_polygon,
    scale=10,
    numPixels=1000,
    geometries=False
)

try:
    water_features = water_samples.getInfo().get('features', [])
    land_features = land_samples.getInfo().get('features', [])
    
    water_vv = [f['properties']['VV'] for f in water_features if 'VV' in f['properties'] and f['properties']['VV'] is not None]
    water_vh = [f['properties']['VH'] for f in water_features if 'VH' in f['properties'] and f['properties']['VH'] is not None]
    
    land_vv = [f['properties']['VV'] for f in land_features if 'VV' in f['properties'] and f['properties']['VV'] is not None]
    land_vh = [f['properties']['VH'] for f in land_features if 'VH' in f['properties'] and f['properties']['VH'] is not None]
    
    print(f"Sampled {len(water_vv)} water pixels, {len(land_vv)} land pixels.")
    
    # 3. Plotting Histograms
    fig, axes = plt.subplots(1, 2, figsize=(14, 6))
    
    # Curated colors: Sleek deep blue for water, earthy orange-brown for land/mudflat
    water_color = '#1f77b4'
    land_color = '#d95f02'
    
    # Subplot 1: VV Band
    axes[0].hist(water_vv, bins=25, range=(-25, -2), color=water_color, alpha=0.6, label='Vùng nước (Water)', edgecolor='black', density=True)
    axes[0].hist(land_vv, bins=25, range=(-25, -2), color=land_color, alpha=0.6, label='Bãi bồi / Đất (Land)', edgecolor='black', density=True)
    axes[0].set_title('Phân bố phản xạ VV (VV Backscatter)', fontsize=13, fontweight='bold')
    axes[0].set_xlabel('Giá trị Backscatter (dB)', fontsize=11)
    axes[0].set_ylabel('Mật độ phân bố (Density)', fontsize=11)
    axes[0].grid(True, linestyle='--', alpha=0.5)
    axes[0].legend(fontsize=10)
    
    # Subplot 2: VH Band
    axes[1].hist(water_vh, bins=25, range=(-30, -5), color=water_color, alpha=0.6, label='Vùng nước (Water)', edgecolor='black', density=True)
    axes[1].hist(land_vh, bins=25, range=(-30, -5), color=land_color, alpha=0.6, label='Bãi bồi / Đất (Land)', edgecolor='black', density=True)
    axes[1].set_title('Phân bố phản xạ VH (VH Backscatter)', fontsize=13, fontweight='bold')
    axes[1].set_xlabel('Giá trị Backscatter (dB)', fontsize=11)
    axes[1].set_ylabel('Mật độ phân bố (Density)', fontsize=11)
    axes[1].grid(True, linestyle='--', alpha=0.5)
    axes[1].legend(fontsize=10)
    
    plt.suptitle('So sánh phân bố tín hiệu radar Sentinel-1: Vùng Nước vs. Bãi Bồi/Đất (2024 Dry)', fontsize=15, fontweight='bold', y=0.98)
    plt.tight_layout()
    
    os.makedirs('outputs', exist_ok=True)
    output_plot_path = 'outputs/histogram_classes_2024_dry.png'
    plt.savefig(output_plot_path, dpi=200)
    plt.close()
    
    print(f"Plot saved successfully to: {output_plot_path}")
    
except Exception as e:
    print(f"Failed to query GEE samples or plot: {e}")
