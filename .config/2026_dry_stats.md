# SongHong Shoreline Run Stats (2026 DRY)

- **Execution Date**: 2026-07-27 07:47:04
- **Execution Runtime**: 24m 54s (1494.14 seconds)
- **Year / Season**: 2026 / DRY

## 1. Technical Parameters
- **Reach 1 Model (Local RF)**: smileRandomForest (numberOfTrees=200, variablesPerSplit=None, bagFraction=1.0)
- **Reach 2 & 3 Model (Global RF)**: smileRandomForest (numberOfTrees=300, variablesPerSplit=3, bagFraction=0.5)
- **Features (Reach 1)**: VV, VH, VV_ratio, VV_sum, VV_mean, GLCM (VV+VH textures), HAND, Slope
- **Features (Reach 2 & 3)**: VV, VH, VV_ratio, VV_sum, VV_mean, VV_contrast, VV_variance
- **Smoothing / Simplification**: Douglas-Peucker (1.0m tolerance), Chaikin (30m spacing, 3 iterations)
- **Active Channel Constraint**: 150m buffer around Sentinel-2 NDWI reference shoreline

## 2. Positional Accuracy Metrics
- **Mean Error**: 24.85 m
- **Median (P50) Error**: 10.53 m
- **RMSE**: 53.01 m
- **Hausdorff Distance**: 545.11 m
- **95th Percentile (P95)**: 120.00 m

### Reach-Wise Breakdown
- **Reach 1 (Upper)**:
  - Points: 12312
  - Mean Error: 40.30 m
  - Median Error: 16.21 m
  - RMSE: 80.53 m
  - Hausdorff: 545.11 m
  - P95: 150.32 m
- **Reach 2 (Middle)**:
  - Points: 20974
  - Mean Error: 25.00 m
  - Median Error: 14.27 m
  - RMSE: 46.93 m
  - Hausdorff: 364.67 m
  - P95: 95.62 m
- **Reach 3 (Lower)**:
  - Points: 14183
  - Mean Error: 11.22 m
  - Median Error: 4.62 m
  - RMSE: 22.74 m
  - Hausdorff: 153.21 m
  - P95: 35.23 m
