# SongHong Shoreline Run Stats (2019 WET)

- **Execution Date**: 2026-07-27 02:11:59
- **Execution Runtime**: 26m 47s (1607.22 seconds)
- **Year / Season**: 2019 / WET

## 1. Technical Parameters
- **Reach 1 Model (Local RF)**: smileRandomForest (numberOfTrees=200, variablesPerSplit=None, bagFraction=1.0)
- **Reach 2 & 3 Model (Global RF)**: smileRandomForest (numberOfTrees=300, variablesPerSplit=3, bagFraction=0.5)
- **Features (Reach 1)**: VV, VH, VV_ratio, VV_sum, VV_mean, GLCM (VV+VH textures), HAND, Slope
- **Features (Reach 2 & 3)**: VV, VH, VV_ratio, VV_sum, VV_mean, VV_contrast, VV_variance
- **Smoothing / Simplification**: Douglas-Peucker (1.0m tolerance), Chaikin (30m spacing, 3 iterations)
- **Active Channel Constraint**: 150m buffer around Sentinel-2 NDWI reference shoreline

## 2. Positional Accuracy Metrics
- **Mean Error**: 21.02 m
- **Median (P50) Error**: 9.05 m
- **RMSE**: 42.04 m
- **Hausdorff Distance**: 369.96 m
- **95th Percentile (P95)**: 115.84 m

### Reach-Wise Breakdown
- **Reach 1 (Upper)**:
  - Points: 11814
  - Mean Error: 22.99 m
  - Median Error: 10.00 m
  - RMSE: 43.18 m
  - Hausdorff: 191.01 m
  - P95: 148.03 m
- **Reach 2 (Middle)**:
  - Points: 22354
  - Mean Error: 27.53 m
  - Median Error: 13.30 m
  - RMSE: 51.34 m
  - Hausdorff: 369.96 m
  - P95: 146.38 m
- **Reach 3 (Lower)**:
  - Points: 14014
  - Mean Error: 8.98 m
  - Median Error: 4.07 m
  - RMSE: 17.29 m
  - Hausdorff: 152.57 m
  - P95: 27.63 m
