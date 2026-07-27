# SongHong Shoreline Run Stats (2020 DRY)

- **Execution Date**: 2026-07-27 02:38:27
- **Execution Runtime**: 26m 28s (1588.20 seconds)
- **Year / Season**: 2020 / DRY

## 1. Technical Parameters
- **Reach 1 Model (Local RF)**: smileRandomForest (numberOfTrees=200, variablesPerSplit=None, bagFraction=1.0)
- **Reach 2 & 3 Model (Global RF)**: smileRandomForest (numberOfTrees=300, variablesPerSplit=3, bagFraction=0.5)
- **Features (Reach 1)**: VV, VH, VV_ratio, VV_sum, VV_mean, GLCM (VV+VH textures), HAND, Slope
- **Features (Reach 2 & 3)**: VV, VH, VV_ratio, VV_sum, VV_mean, VV_contrast, VV_variance
- **Smoothing / Simplification**: Douglas-Peucker (1.0m tolerance), Chaikin (30m spacing, 3 iterations)
- **Active Channel Constraint**: 150m buffer around Sentinel-2 NDWI reference shoreline

## 2. Positional Accuracy Metrics
- **Mean Error**: 23.02 m
- **Median (P50) Error**: 8.58 m
- **RMSE**: 45.17 m
- **Hausdorff Distance**: 363.89 m
- **95th Percentile (P95)**: 131.69 m

### Reach-Wise Breakdown
- **Reach 1 (Upper)**:
  - Points: 11832
  - Mean Error: 35.65 m
  - Median Error: 14.42 m
  - RMSE: 59.67 m
  - Hausdorff: 188.69 m
  - P95: 149.93 m
- **Reach 2 (Middle)**:
  - Points: 22082
  - Mean Error: 25.26 m
  - Median Error: 11.17 m
  - RMSE: 48.02 m
  - Hausdorff: 363.89 m
  - P95: 124.65 m
- **Reach 3 (Lower)**:
  - Points: 13979
  - Mean Error: 8.82 m
  - Median Error: 3.97 m
  - RMSE: 18.27 m
  - Hausdorff: 152.55 m
  - P95: 23.13 m
