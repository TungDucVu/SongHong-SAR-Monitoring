# SongHong Shoreline Run Stats (2023 WET)

- **Execution Date**: 2026-07-27 05:41:24
- **Execution Runtime**: 26m 30s (1590.67 seconds)
- **Year / Season**: 2023 / WET

## 1. Technical Parameters
- **Reach 1 Model (Local RF)**: smileRandomForest (numberOfTrees=200, variablesPerSplit=None, bagFraction=1.0)
- **Reach 2 & 3 Model (Global RF)**: smileRandomForest (numberOfTrees=300, variablesPerSplit=3, bagFraction=0.5)
- **Features (Reach 1)**: VV, VH, VV_ratio, VV_sum, VV_mean, GLCM (VV+VH textures), HAND, Slope
- **Features (Reach 2 & 3)**: VV, VH, VV_ratio, VV_sum, VV_mean, VV_contrast, VV_variance
- **Smoothing / Simplification**: Douglas-Peucker (1.0m tolerance), Chaikin (30m spacing, 3 iterations)
- **Active Channel Constraint**: 150m buffer around Sentinel-2 NDWI reference shoreline

## 2. Positional Accuracy Metrics
- **Mean Error**: 17.09 m
- **Median (P50) Error**: 7.58 m
- **RMSE**: 35.58 m
- **Hausdorff Distance**: 353.70 m
- **95th Percentile (P95)**: 74.87 m

### Reach-Wise Breakdown
- **Reach 1 (Upper)**:
  - Points: 12288
  - Mean Error: 21.94 m
  - Median Error: 9.94 m
  - RMSE: 40.63 m
  - Hausdorff: 188.07 m
  - P95: 116.39 m
- **Reach 2 (Middle)**:
  - Points: 21973
  - Mean Error: 20.45 m
  - Median Error: 9.42 m
  - RMSE: 41.65 m
  - Hausdorff: 353.70 m
  - P95: 94.13 m
- **Reach 3 (Lower)**:
  - Points: 14058
  - Mean Error: 7.61 m
  - Median Error: 3.46 m
  - RMSE: 14.04 m
  - Hausdorff: 148.21 m
  - P95: 20.97 m
