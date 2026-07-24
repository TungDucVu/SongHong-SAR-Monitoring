# VH Textures Feature Selection Results (2024 Seasons)

This report compares three feature selection combinations on top of the 11 base features (VV textures + ratios).

## DRY Season

| Combination Config | Num Features | OA (%) | Kappa | Macro F1 | Water F1 | Sand F1 | Built-up F1 | Vegetation F1 |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| Combo 1: Base + VH_contrast | 12 | 61.47% | 0.4692 | 0.6561 | 0.8920 | 0.5984 | 0.6436 | 0.4906 |
| Combo 2: Base + VH_contrast + VH_homogeneity | 13 | 63.64% | 0.4989 | 0.6809 | 0.9171 | 0.6592 | 0.6275 | 0.5198 |
| Combo 3: Base + VH_contrast + VH_variance | 13 | 62.66% | 0.4855 | 0.6689 | 0.8980 | 0.6135 | 0.6503 | 0.5138 |

## WET Season

| Combination Config | Num Features | OA (%) | Kappa | Macro F1 | Water F1 | Sand F1 | Built-up F1 | Vegetation F1 |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| Combo 1: Base + VH_contrast | 12 | 59.98% | 0.4494 | 0.6320 | 0.8095 | 0.6526 | 0.5728 | 0.4929 |
| Combo 2: Base + VH_contrast + VH_homogeneity | 13 | 62.80% | 0.4889 | 0.6582 | 0.8327 | 0.6771 | 0.5993 | 0.5238 |
| Combo 3: Base + VH_contrast + VH_variance | 13 | 59.67% | 0.4453 | 0.6316 | 0.8244 | 0.6590 | 0.5585 | 0.4844 |

