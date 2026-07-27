# SongHong Shoreline Run Stats (2026 WET)

- **Execution Date**: 2026-07-27 08:10:57
- **Execution Runtime**: 23m 52s (1432.98 seconds)
- **Year / Season**: 2026 / WET

## 1. Technical Parameters
- **Reach 1 Model (Local RF)**: smileRandomForest (numberOfTrees=200, variablesPerSplit=None, bagFraction=1.0)
- **Reach 2 & 3 Model (Global RF)**: smileRandomForest (numberOfTrees=300, variablesPerSplit=3, bagFraction=0.5)
- **Features (Reach 1)**: VV, VH, VV_ratio, VV_sum, VV_mean, GLCM (VV+VH textures), HAND, Slope
- **Features (Reach 2 & 3)**: VV, VH, VV_ratio, VV_sum, VV_mean, VV_contrast, VV_variance
- **Smoothing / Simplification**: Douglas-Peucker (1.0m tolerance), Chaikin (30m spacing, 3 iterations)
- **Active Channel Constraint**: 150m buffer around Sentinel-2 NDWI reference shoreline

## 2. Positional Accuracy Metrics
- **Mean Error**: 24.27 m
- **Median (P50) Error**: 9.00 m
- **RMSE**: 56.08 m
- **Hausdorff Distance**: 544.16 m
- **95th Percentile (P95)**: 128.16 m

### Reach-Wise Breakdown
- **Reach 1 (Upper)**:
  - Points: 12451
  - Mean Error: 29.56 m
  - Median Error: 9.58 m
  - RMSE: 71.03 m
  - Hausdorff: 544.16 m
  - P95: 148.58 m
- **Reach 2 (Middle)**:
  - Points: 21197
  - Mean Error: 31.36 m
  - Median Error: 13.56 m
  - RMSE: 62.72 m
  - Hausdorff: 367.17 m
  - P95: 150.99 m
- **Reach 3 (Lower)**:
  - Points: 13987
  - Mean Error: 8.81 m
  - Median Error: 3.81 m
  - RMSE: 16.02 m
  - Hausdorff: 152.60 m
  - P95: 29.80 m
