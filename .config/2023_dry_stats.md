# SongHong Shoreline Run Stats (2023 DRY)

- **Execution Date**: 2026-07-27 05:14:54
- **Execution Runtime**: 26m 40s (1600.46 seconds)
- **Year / Season**: 2023 / DRY

## 1. Technical Parameters
- **Reach 1 Model (Local RF)**: smileRandomForest (numberOfTrees=200, variablesPerSplit=None, bagFraction=1.0)
- **Reach 2 & 3 Model (Global RF)**: smileRandomForest (numberOfTrees=300, variablesPerSplit=3, bagFraction=0.5)
- **Features (Reach 1)**: VV, VH, VV_ratio, VV_sum, VV_mean, GLCM (VV+VH textures), HAND, Slope
- **Features (Reach 2 & 3)**: VV, VH, VV_ratio, VV_sum, VV_mean, VV_contrast, VV_variance
- **Smoothing / Simplification**: Douglas-Peucker (1.0m tolerance), Chaikin (30m spacing, 3 iterations)
- **Active Channel Constraint**: 150m buffer around Sentinel-2 NDWI reference shoreline

## 2. Positional Accuracy Metrics
- **Mean Error**: 24.64 m
- **Median (P50) Error**: 9.65 m
- **RMSE**: 47.41 m
- **Hausdorff Distance**: 348.74 m
- **95th Percentile (P95)**: 144.19 m

### Reach-Wise Breakdown
- **Reach 1 (Upper)**:
  - Points: 12820
  - Mean Error: 43.49 m
  - Median Error: 19.89 m
  - RMSE: 67.58 m
  - Hausdorff: 189.94 m
  - P95: 150.17 m
- **Reach 2 (Middle)**:
  - Points: 21826
  - Mean Error: 23.95 m
  - Median Error: 11.65 m
  - RMSE: 46.64 m
  - Hausdorff: 348.74 m
  - P95: 113.07 m
- **Reach 3 (Lower)**:
  - Points: 14074
  - Mean Error: 8.55 m
  - Median Error: 3.88 m
  - RMSE: 15.73 m
  - Hausdorff: 141.36 m
  - P95: 27.29 m
