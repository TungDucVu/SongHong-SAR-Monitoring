# SongHong Shoreline Run Stats (2025 DRY)

- **Execution Date**: 2026-07-27 06:57:22
- **Execution Runtime**: 24m 44s (1484.54 seconds)
- **Year / Season**: 2025 / DRY

## 1. Technical Parameters
- **Reach 1 Model (Local RF)**: smileRandomForest (numberOfTrees=200, variablesPerSplit=None, bagFraction=1.0)
- **Reach 2 & 3 Model (Global RF)**: smileRandomForest (numberOfTrees=300, variablesPerSplit=3, bagFraction=0.5)
- **Features (Reach 1)**: VV, VH, VV_ratio, VV_sum, VV_mean, GLCM (VV+VH textures), HAND, Slope
- **Features (Reach 2 & 3)**: VV, VH, VV_ratio, VV_sum, VV_mean, VV_contrast, VV_variance
- **Smoothing / Simplification**: Douglas-Peucker (1.0m tolerance), Chaikin (30m spacing, 3 iterations)
- **Active Channel Constraint**: 150m buffer around Sentinel-2 NDWI reference shoreline

## 2. Positional Accuracy Metrics
- **Mean Error**: 24.97 m
- **Median (P50) Error**: 9.32 m
- **RMSE**: 47.89 m
- **Hausdorff Distance**: 359.40 m
- **95th Percentile (P95)**: 144.53 m

### Reach-Wise Breakdown
- **Reach 1 (Upper)**:
  - Points: 11868
  - Mean Error: 40.26 m
  - Median Error: 17.04 m
  - RMSE: 65.29 m
  - Hausdorff: 187.59 m
  - P95: 150.04 m
- **Reach 2 (Middle)**:
  - Points: 21419
  - Mean Error: 24.92 m
  - Median Error: 11.98 m
  - RMSE: 47.21 m
  - Hausdorff: 359.40 m
  - P95: 115.99 m
- **Reach 3 (Lower)**:
  - Points: 14379
  - Mean Error: 12.43 m
  - Median Error: 4.46 m
  - RMSE: 27.67 m
  - Hausdorff: 153.64 m
  - P95: 45.87 m
