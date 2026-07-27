# SongHong Shoreline Run Stats (2024 DRY)

- **Execution Date**: 2026-07-27 06:06:34
- **Execution Runtime**: 25m 9s (1509.28 seconds)
- **Year / Season**: 2024 / DRY

## 1. Technical Parameters
- **Reach 1 Model (Local RF)**: smileRandomForest (numberOfTrees=200, variablesPerSplit=None, bagFraction=1.0)
- **Reach 2 & 3 Model (Global RF)**: smileRandomForest (numberOfTrees=300, variablesPerSplit=3, bagFraction=0.5)
- **Features (Reach 1)**: VV, VH, VV_ratio, VV_sum, VV_mean, GLCM (VV+VH textures), HAND, Slope
- **Features (Reach 2 & 3)**: VV, VH, VV_ratio, VV_sum, VV_mean, VV_contrast, VV_variance
- **Smoothing / Simplification**: Douglas-Peucker (1.0m tolerance), Chaikin (30m spacing, 3 iterations)
- **Active Channel Constraint**: 150m buffer around Sentinel-2 NDWI reference shoreline

## 2. Positional Accuracy Metrics
- **Mean Error**: 24.30 m
- **Median (P50) Error**: 9.68 m
- **RMSE**: 46.57 m
- **Hausdorff Distance**: 354.44 m
- **95th Percentile (P95)**: 142.54 m

### Reach-Wise Breakdown
- **Reach 1 (Upper)**:
  - Points: 12162
  - Mean Error: 41.94 m
  - Median Error: 19.69 m
  - RMSE: 66.28 m
  - Hausdorff: 187.93 m
  - P95: 150.15 m
- **Reach 2 (Middle)**:
  - Points: 21390
  - Mean Error: 24.17 m
  - Median Error: 11.92 m
  - RMSE: 45.96 m
  - Hausdorff: 354.44 m
  - P95: 111.89 m
- **Reach 3 (Lower)**:
  - Points: 14002
  - Mean Error: 9.19 m
  - Median Error: 3.96 m
  - RMSE: 17.98 m
  - Hausdorff: 151.62 m
  - P95: 26.84 m
