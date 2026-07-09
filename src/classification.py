"""
Classification module for SongHong SAR Monitoring project.
Implements Phase 2: Feature Engineering (Arithmetic bands and GLCM Texture features)
and provides training and prediction helper functions.
"""

import ee
from src.config import CLASSIFIER_FEATURES, WATER_REF_POLYGON, SAND_REF_POLYGON, URBAN_REF_POLYGON

def calculate_derived_polarizations(image):
    """
    Calculates derived polarization bands:
    1. VV_ratio: Subtraction in dB scale, representing ratio in linear scale.
       Formula: VV_ratio = VV_dB - VH_dB
    2. VV_sum: Power summation converted back to dB scale.
       Formula: 10 * log10(10^(VV/10) + 10^(VH/10))
    3. VV_mean: Arithmetic mean in dB space.
       Formula: (VV_dB + VH_dB) / 2
    """
    vv = image.select('VV')
    vh = image.select('VH')
    
    # 1. Log-ratio (VV_dB - VH_dB)
    vv_ratio = vv.subtract(vh).rename('VV_ratio')
    
    # 2. Power sum back to dB
    vv_linear = ee.Image(10).pow(vv.divide(10))
    vh_linear = ee.Image(10).pow(vh.divide(10))
    vv_sum = vv_linear.add(vh_linear).log10().multiply(10).rename('VV_sum')
    
    # 3. Arithmetic mean of log-backscatter
    vv_mean = vv.add(vh).divide(2).rename('VV_mean')
    
    return ee.Image.cat([vv_ratio, vv_sum, vv_mean])

def calculate_glcm_textures(image, band_name='VV', window_size=7):
    """
    Calculates Gray-Level Co-occurrence Matrix (GLCM) texture features for the specified band.
    Stretches values to a robust byte range for server-side stability.
    
    CRITICAL CONSTRAINTS:
    1. Input scale: Clamps the backscatter to [-25, 5] dB, scales to [0, 255] integer range.
    2. Native projection preservation: No .reproject() calls.
    3. Consistency: Scaling must remain identical between train, test, and inference.
    """
    # 1. Clamp and scale to 0-255 range, cast to Int32
    scaled_int = (image.select(band_name)
                  .clamp(-25, 5)
                  .unitScale(-25, 5)
                  .multiply(255)
                  .toInt32())
    
    # 2. Run neighborhood GLCM reducer
    glcm = scaled_int.glcmTexture(size=window_size)
    
    # 3. Select 6 texture statistics and rename them to contract names
    # Note: GEE's output format is {band_name}_{suffix}
    glcm_selected = glcm.select([
        f'{band_name}_contrast',
        f'{band_name}_ent',
        f'{band_name}_idm',
        f'{band_name}_corr',
        f'{band_name}_asm',
        f'{band_name}_var'
    ]).rename([
        f'{band_name}_contrast',
        f'{band_name}_entropy',
        f'{band_name}_homogeneity',
        f'{band_name}_correlation',
        f'{band_name}_ASM',
        f'{band_name}_variance'
    ])
    
    return glcm_selected

def create_feature_stack(image):
    """
    Constructs the exact 11-band feature stack required by the contract.
    Ensures correct band sequence and prints band signatures.
    """
    # 1. Extract raw Sentinel-1 bands
    raw_s1 = image.select(['VV', 'VH'])
    
    # 2. Compute arithmetic and texture features
    derived = calculate_derived_polarizations(image)
    textures = calculate_glcm_textures(image, band_name='VV', window_size=7)
    
    # 3. Combine and select in strict contract order
    feature_stack = raw_s1.addBands(derived).addBands(textures)
    feature_stack = feature_stack.select(CLASSIFIER_FEATURES)
    
    # 4. Print band signatures to stdout for audit
    print("\n[Feature Engineering] Band Stack Signature:")
    try:
        band_names = feature_stack.bandNames().getInfo()
        band_types = feature_stack.bandTypes().getInfo()
        for i, b in enumerate(band_names):
            b_precision = band_types.get(b, {}).get('precision', 'unknown')
            print(f"  {i+1:2d}. {b:<15} ({b_precision})")
    except Exception as e:
        print(f"[Warning] Failed to query band signatures: {e}")
        
    return feature_stack

def verify_feature_correlation(image, aoi_geometry):
    """
    Samples 500 pixels within the AOI to check for high feature redundancy.
    Logs warning if Pearson correlation between distinct bands is > 0.98.
    """
    print("\n[QC] Starting Feature Correlation Analysis...")
    # Sample 500 points at 100m scale
    samples = image.sample(
        region=aoi_geometry,
        scale=100,
        numPixels=500,
        geometries=False
    )
    
    try:
        features = samples.getInfo().get('features', [])
        data = {b: [] for b in CLASSIFIER_FEATURES}
        for f in features:
            props = f.get('properties', {})
            for b in CLASSIFIER_FEATURES:
                val = props.get(b)
                if val is not None:
                     data[b].append(val)
                     
        n_samples = len(data['VV'])
        if n_samples > 10:
            import numpy as np
            # Compute correlation matrix
            matrix = np.corrcoef([data[b] for b in CLASSIFIER_FEATURES])
            
            print(f"\n[QC] Feature Correlation Matrix (n={n_samples}):")
            header = "     " + " ".join([f"{b[3:8] if len(b) > 3 else b:>6}" for b in CLASSIFIER_FEATURES])
            print(header)
            
            for i, b1 in enumerate(CLASSIFIER_FEATURES):
                row_str = f"{b1[:5]:<5}"
                for j, b2 in enumerate(CLASSIFIER_FEATURES):
                    corr = matrix[i, j]
                    row_str += f" {corr:6.2f}"
                    # Log warnings for redundant features
                    if i != j and abs(corr) > 0.98:
                        print(f"  [WARNING] Redundant features: {b1} and {b2} have correlation = {corr:.3f}")
                print(row_str)
        else:
            print("[Warning] Insufficient pixel samples for correlation calculation.")
    except Exception as e:
        print(f"[Warning] Failed feature correlation audit: {e}")

def verify_multiclass_textures(image):
    """
    Calculates spatial mean GLCM Contrast over reference Water, Sand, and Urban polygons.
    Verifies that texture increases land cover separability.
    """
    print("\n[QC] Starting Multi-Class Texture Separability Validation...")
    
    # Define reference geometries
    geoms = {
        'Water': ee.Geometry.Polygon(WATER_REF_POLYGON),
        'Sand': ee.Geometry.Polygon(SAND_REF_POLYGON),
        'Urban': ee.Geometry.Polygon(URBAN_REF_POLYGON)
    }
    
    for label, geom in geoms.items():
        try:
            mean_contrast = image.select('VV_contrast').reduceRegion(
                reducer=ee.Reducer.mean(),
                geometry=geom,
                scale=10
            ).get('VV_contrast').getInfo()
            
            print(f"  - {label:<6} Region VV_contrast mean: {mean_contrast:.2f}")
        except Exception as e:
            print(f"  [Warning] Failed to calculate contrast for {label}: {e}")
