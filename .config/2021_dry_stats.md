# SongHong Shoreline Run Stats (2021 DRY)

- **Execution Date**: 2026-07-27 03:30:42
- **Execution Runtime**: 25m 31s (1531.14 seconds)
- **Year / Season**: 2021 / DRY

## 1. Technical Parameters
- **Reach 1 Model (Local RF)**: smileRandomForest (numberOfTrees=200, variablesPerSplit=None, bagFraction=1.0)
- **Reach 2 & 3 Model (Global RF)**: smileRandomForest (numberOfTrees=300, variablesPerSplit=3, bagFraction=0.5)
- **Features (Reach 1)**: VV, VH, VV_ratio, VV_sum, VV_mean, GLCM (VV+VH textures), HAND, Slope
- **Features (Reach 2 & 3)**: VV, VH, VV_ratio, VV_sum, VV_mean, VV_contrast, VV_variance
- **Smoothing / Simplification**: Douglas-Peucker (1.0m tolerance), Chaikin (30m spacing, 3 iterations)
- **Active Channel Constraint**: 150m buffer around Sentinel-2 NDWI reference shoreline

## 2. Positional Accuracy Metrics
- **Mean Error**: 20.89 m
- **Median (P50) Error**: 8.41 m
- **RMSE**: 41.67 m
- **Hausdorff Distance**: 365.10 m
- **95th Percentile (P95)**: 111.17 m

### Reach-Wise Breakdown
- **Reach 1 (Upper)**:
  - Points: 12128
  - Mean Error: 29.76 m
  - Median Error: 12.81 m
  - RMSE: 52.28 m
  - Hausdorff: 187.86 m
  - P95: 149.39 m
- **Reach 2 (Middle)**:
  - Points: 22340
  - Mean Error: 22.66 m
  - Median Error: 10.63 m
  - RMSE: 44.07 m
  - Hausdorff: 365.10 m
  - P95: 99.58 m
- **Reach 3 (Lower)**:
  - Points: 14209
  - Mean Error: 10.55 m
  - Median Error: 4.44 m
  - RMSE: 23.73 m
  - Hausdorff: 153.14 m
  - P95: 33.59 m
