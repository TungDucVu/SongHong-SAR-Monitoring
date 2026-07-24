# Random Forest Ablation Study Results (2024 Seasons)

This report compares the performance of 4 model configurations (varying feature sets) trained on the same training set using class-level global sampling limits (Water=1000, others=1800).

## DRY Season

| Model Config | Num Features | OA (%) | Kappa | Macro F1 | Water F1 | Sand F1 | Built-up F1 | Vegetation F1 |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| Model 1: VV + VH | 2 | 58.26% | 0.4255 | 0.6257 | 0.8602 | 0.6586 | 0.4999 | 0.4841 |
| Model 2: VV + VH + Ratio | 3 | 58.61% | 0.4305 | 0.6292 | 0.8677 | 0.6510 | 0.5074 | 0.4906 |
| Model 3: VV + VH + Ratio + Textures | 9 | 61.85% | 0.4748 | 0.6586 | 0.8891 | 0.5915 | 0.6422 | 0.5115 |
| Model 4: Full Feature Set | 11 | 61.88% | 0.4746 | 0.6613 | 0.9052 | 0.5886 | 0.6529 | 0.4984 |

## WET Season

| Model Config | Num Features | OA (%) | Kappa | Macro F1 | Water F1 | Sand F1 | Built-up F1 | Vegetation F1 |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| Model 1: VV + VH | 2 | 52.54% | 0.3489 | 0.5521 | 0.6981 | 0.5790 | 0.4648 | 0.4667 |
| Model 2: VV + VH + Ratio | 3 | 51.33% | 0.3310 | 0.5372 | 0.6663 | 0.5539 | 0.4869 | 0.4417 |
| Model 3: VV + VH + Ratio + Textures | 9 | 61.04% | 0.4645 | 0.6445 | 0.8423 | 0.6524 | 0.5861 | 0.4972 |
| Model 4: Full Feature Set | 11 | 64.06% | 0.5056 | 0.6715 | 0.8392 | 0.6811 | 0.6179 | 0.5480 |

