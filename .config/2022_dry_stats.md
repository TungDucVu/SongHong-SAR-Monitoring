# SongHong Shoreline Run Stats (2022 DRY)

- **Execution Date**: 2026-07-27 04:22:01
- **Execution Runtime**: 25m 24s (1524.35 seconds)
- **Year / Season**: 2022 / DRY

## 1. Technical Parameters
- **Reach 1 Model (Local RF)**: smileRandomForest (numberOfTrees=200, variablesPerSplit=None, bagFraction=1.0)
- **Reach 2 & 3 Model (Global RF)**: smileRandomForest (numberOfTrees=300, variablesPerSplit=3, bagFraction=0.5)
- **Features (Reach 1)**: VV, VH, VV_ratio, VV_sum, VV_mean, GLCM (VV+VH textures), HAND, Slope
- **Features (Reach 2 & 3)**: VV, VH, VV_ratio, VV_sum, VV_mean, VV_contrast, VV_variance
- **Smoothing / Simplification**: Douglas-Peucker (1.0m tolerance), Chaikin (30m spacing, 3 iterations)
- **Active Channel Constraint**: 150m buffer around Sentinel-2 NDWI reference shoreline

## 2. Positional Accuracy Metrics
- **Mean Error**: 22.85 m
- **Median (P50) Error**: 8.89 m
- **RMSE**: 45.66 m
- **Hausdorff Distance**: 348.17 m
- **95th Percentile (P95)**: 134.16 m

### Reach-Wise Breakdown
- **Reach 1 (Upper)**:
  - Points: 12825
  - Mean Error: 36.89 m
  - Median Error: 14.79 m
  - RMSE: 61.26 m
  - Hausdorff: 187.56 m
  - P95: 149.94 m
- **Reach 2 (Middle)**:
  - Points: 22161
  - Mean Error: 24.37 m
  - Median Error: 10.93 m
  - RMSE: 48.05 m
  - Hausdorff: 348.17 m
  - P95: 120.83 m
- **Reach 3 (Lower)**:
  - Points: 13961
  - Mean Error: 7.55 m
  - Median Error: 3.51 m
  - RMSE: 14.06 m
  - Hausdorff: 152.26 m
  - P95: 21.75 m
