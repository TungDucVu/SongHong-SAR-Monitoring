# SongHong Shoreline Run Stats (2024 WET)

- **Execution Date**: 2026-07-22 22:30:02
- **Execution Runtime**: 17m 3s (1023.48 seconds)
- **Year / Season**: 2024 / WET

## 1. Technical Parameters
- **Reach 1 Model (Local RF)**: smileRandomForest (numberOfTrees=200, variablesPerSplit=None, bagFraction=1.0)
- **Reach 2 & 3 Model (Global RF)**: smileRandomForest (numberOfTrees=300, variablesPerSplit=3, bagFraction=0.5)
- **Features (Reach 1)**: VV, VH, VV_ratio, VV_sum, VV_mean, GLCM (VV+VH textures), HAND, Slope
- **Features (Reach 2 & 3)**: VV, VH, VV_ratio, VV_sum, VV_mean, VV_contrast, VV_variance
- **Smoothing / Simplification**: Douglas-Peucker (1.0m tolerance), Chaikin (30m spacing, 3 iterations)
- **Active Channel Constraint**: 150m buffer around Sentinel-2 NDWI reference shoreline

## 2. Positional Accuracy Metrics
- **Mean Error**: 33.26 m
- **Median (P50) Error**: 20.45 m
- **RMSE**: 54.47 m
- **Hausdorff Distance**: 376.48 m
- **95th Percentile (P95)**: 122.91 m

### Reach-Wise Breakdown
- **Reach 1 (Upper)**:
  - Points: 11830
  - Mean Error: 37.95 m
  - Median Error: 23.62 m
  - RMSE: 57.78 m
  - Hausdorff: 266.19 m
  - P95: 128.60 m
- **Reach 2 (Middle)**:
  - Points: 21714
  - Mean Error: 40.88 m
  - Median Error: 26.32 m
  - RMSE: 64.12 m
  - Hausdorff: 376.48 m
  - P95: 147.24 m
- **Reach 3 (Lower)**:
  - Points: 14011
  - Mean Error: 17.49 m
  - Median Error: 7.25 m
  - RMSE: 29.68 m
  - Hausdorff: 193.10 m
  - P95: 54.50 m
