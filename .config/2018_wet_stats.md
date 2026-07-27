# SongHong Shoreline Run Stats (2018 WET)

- **Execution Date**: 2026-07-27 01:17:04
- **Execution Runtime**: 27m 23s (1643.66 seconds)
- **Year / Season**: 2018 / WET

## 1. Technical Parameters
- **Reach 1 Model (Local RF)**: smileRandomForest (numberOfTrees=200, variablesPerSplit=None, bagFraction=1.0)
- **Reach 2 & 3 Model (Global RF)**: smileRandomForest (numberOfTrees=300, variablesPerSplit=3, bagFraction=0.5)
- **Features (Reach 1)**: VV, VH, VV_ratio, VV_sum, VV_mean, GLCM (VV+VH textures), HAND, Slope
- **Features (Reach 2 & 3)**: VV, VH, VV_ratio, VV_sum, VV_mean, VV_contrast, VV_variance
- **Smoothing / Simplification**: Douglas-Peucker (1.0m tolerance), Chaikin (30m spacing, 3 iterations)
- **Active Channel Constraint**: 150m buffer around Sentinel-2 NDWI reference shoreline

## 2. Positional Accuracy Metrics
- **Mean Error**: 30.00 m
- **Median (P50) Error**: 13.57 m
- **RMSE**: 53.52 m
- **Hausdorff Distance**: 374.56 m
- **95th Percentile (P95)**: 149.48 m

### Reach-Wise Breakdown
- **Reach 1 (Upper)**:
  - Points: 11960
  - Mean Error: 41.20 m
  - Median Error: 19.63 m
  - RMSE: 64.08 m
  - Hausdorff: 189.83 m
  - P95: 149.72 m
- **Reach 2 (Middle)**:
  - Points: 21705
  - Mean Error: 35.73 m
  - Median Error: 17.79 m
  - RMSE: 61.34 m
  - Hausdorff: 374.56 m
  - P95: 150.13 m
- **Reach 3 (Lower)**:
  - Points: 13878
  - Mean Error: 11.40 m
  - Median Error: 5.82 m
  - RMSE: 19.71 m
  - Hausdorff: 151.40 m
  - P95: 35.22 m
