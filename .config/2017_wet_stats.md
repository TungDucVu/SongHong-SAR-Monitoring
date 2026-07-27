# SongHong Shoreline Run Stats (2017 WET)

- **Execution Date**: 2026-07-27 00:24:16
- **Execution Runtime**: 27m 36s (1656.06 seconds)
- **Year / Season**: 2017 / WET

## 1. Technical Parameters
- **Reach 1 Model (Local RF)**: smileRandomForest (numberOfTrees=200, variablesPerSplit=None, bagFraction=1.0)
- **Reach 2 & 3 Model (Global RF)**: smileRandomForest (numberOfTrees=300, variablesPerSplit=3, bagFraction=0.5)
- **Features (Reach 1)**: VV, VH, VV_ratio, VV_sum, VV_mean, GLCM (VV+VH textures), HAND, Slope
- **Features (Reach 2 & 3)**: VV, VH, VV_ratio, VV_sum, VV_mean, VV_contrast, VV_variance
- **Smoothing / Simplification**: Douglas-Peucker (1.0m tolerance), Chaikin (30m spacing, 3 iterations)
- **Active Channel Constraint**: 150m buffer around Sentinel-2 NDWI reference shoreline

## 2. Positional Accuracy Metrics
- **Mean Error**: 23.29 m
- **Median (P50) Error**: 11.04 m
- **RMSE**: 44.12 m
- **Hausdorff Distance**: 388.06 m
- **95th Percentile (P95)**: 101.23 m

### Reach-Wise Breakdown
- **Reach 1 (Upper)**:
  - Points: 12766
  - Mean Error: 32.24 m
  - Median Error: 17.66 m
  - RMSE: 52.45 m
  - Hausdorff: 199.95 m
  - P95: 149.27 m
- **Reach 2 (Middle)**:
  - Points: 23697
  - Mean Error: 25.88 m
  - Median Error: 15.13 m
  - RMSE: 48.92 m
  - Hausdorff: 388.06 m
  - P95: 94.97 m
- **Reach 3 (Lower)**:
  - Points: 14293
  - Mean Error: 11.01 m
  - Median Error: 4.43 m
  - RMSE: 22.10 m
  - Hausdorff: 152.85 m
  - P95: 39.75 m
