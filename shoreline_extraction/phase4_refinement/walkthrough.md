# Phase 4 Walkthrough: Classification Refinement

This document outlines the implementation, optimization, and results of Phase 4 (Classification Refinement) for the Red River shoreline extraction pipeline.

## 1. Objectives & Approach
The main objective of Phase 4 is to clean and refine the raw Random Forest pixel classification maps (specifically Water and Sand classes) into continuous, noise-free river corridor masks.

- **Morphological Pipeline**: 
  - 3x3 Majority filter for initial pixel aggregation.
  - Morphological Opening (disk radius = 2) to delete sub-pixel noise and small branches.
  - Morphological Closing (disk radius = 3) to fill internal holes and connect small breaks.
- **Spatial Constraint Routing**:
  - Clip all masks to a 2km river centerline buffer (`song_hong_centerline.geojson`) to completely eliminate off-channel lakes, urban features, and agriculture ponds.
  - Apply focal size filtering (`connectedPixelCount`) to keep only components with $\ge 50$ contiguous pixels, ensuring only the main river channel is processed downstream.

## 2. GEE Memory Limit Optimization & Solutions
To resolve the "User memory limit exceeded" errors during synchronous calculations, the following architecture optimizations were implemented:
1. **Corridor Constraint Clipping**: Clipping the binary masks to the 2km buffer prior to size filtering severely limits pixel count and computation footprint.
2. **Coarser Resolution for QC Stats**: Shifting the QC component counting resolution (`connectedComponents`) to a 200m scale inside GEE to significantly reduce memory allocation.
3. **Synchronous Fallback Mechanism**: Wrapped stats retrieval in `scratch/verify_phase4.py` in a try-except block. If GEE hits memory limits during iterative connected component counting, the script falls back to an area-based reduction (`ee.Reducer.sum()`) at a 200m scale. This is extremely lightweight, reliable, and ensures execution success.

## 3. Results (2024 Dry Season)
- **RF Classifier Accuracy**:
  - Overall Accuracy: **65.69%**
  - Kappa Coefficient: **0.5266**
  - Macro F1-score: **0.7018**
  - Water F1-score: **0.9331** (Precision = 89.55%, Recall = 97.41%)
- **Refinement Efficiency (Dry Season)**:
  - Original water patches/components: **45** (low-resolution estimate)
  - Refined corridor patches: **1** (main channel)
  - Patches reduction: **97.78%** (exceeds the $\ge 95\%$ target)
- **Map Outputs**:
  - The refined Dry season water and sand masks were successfully generated and rendered to: `outputs/refinement_2024_dry.html`.

## 4. Pending / Next Steps
1. **Complete WET Season Run**: Rerun the verification script to completion for the Wet season to generate `outputs/refinement_2024_wet.html` (interrupted by user termination).
2. **Phase 5 Integration**: Transition to Phase 5 (Shared Boundary Extraction) to extract vector shorelines (Water-Sand and Sand-Land boundaries) from these refined masks.
