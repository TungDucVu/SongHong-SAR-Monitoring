"""
Preprocessing module for Sentinel-1 SAR imagery.
Implements border noise removal, the edge-preserving Refined Lee speckle filter,
and derived feature extraction (Ratio, Difference).
"""

import ee
from src.config import S1_BANDS, S1_IW_ANGLE_MIN, S1_IW_ANGLE_MAX

def db_to_power(img):
    """Convert backscatter intensity from decibels (dB) to power (linear scale)."""
    return ee.Image(10.0).pow(img.divide(10.0))

def power_to_db(img):
    """Convert backscatter intensity from power (linear scale) to decibels (dB)."""
    return img.log10().multiply(10.0)

def remove_border_noise(image, use_intensity_mask=False):
    """
    Removes border noise and low-intensity edge anomalies from Sentinel-1 images.
    Uses incidence angle thresholds and optional minimum intensity masking.
    
    CRITICAL CONSTRAINT: Native Sentinel-1 projection and scale are strictly preserved.
    No .reproject() or .setDefaultProjection() is called.
    """
    # 1. Mask by incidence angle (valid range for IW mode from config.py)
    angle = image.select('angle')
    angle_mask = angle.gt(S1_IW_ANGLE_MIN).And(angle.lt(S1_IW_ANGLE_MAX))
    
    clean_mask = angle_mask
    
    # 2. Mask out extreme low-intensity backscatter values (only if explicitly enabled)
    # This is a secondary constraint to prevent removing valid deep water areas.
    if use_intensity_mask:
        vv = image.select('VV')
        vh = image.select('VH')
        vv_mask = vv.gt(-30.0)
        vh_mask = vh.gt(-35.0)
        clean_mask = clean_mask.And(vv_mask).And(vh_mask)
        
    return image.updateMask(clean_mask)

def apply_refined_lee_single_band(power_img, band_name):
    """
    Applies the Refined Lee filter to a single band (in power/linear units).
    """
    img = power_img.select(band_name)

    # 3x3 local mean and variance
    weights3 = ee.List.repeat(ee.List.repeat(1, 3), 3)
    kernel3 = ee.Kernel.fixed(3, 3, weights3, 1, 1, False)

    mean3 = img.reduceNeighborhood(ee.Reducer.mean(), kernel3)
    variance3 = img.reduceNeighborhood(ee.Reducer.variance(), kernel3)

    # 7x7 sample kernel to analyze directional gradients
    sample_weights = ee.List([
        [0, 0, 0, 0, 0, 0, 0],
        [0, 1, 0, 1, 0, 1, 0],
        [0, 0, 0, 0, 0, 0, 0],
        [0, 1, 0, 1, 0, 1, 0],
        [0, 0, 0, 0, 0, 0, 0],
        [0, 1, 0, 1, 0, 1, 0],
        [0, 0, 0, 0, 0, 0, 0]
    ])
    sample_kernel = ee.Kernel.fixed(7, 7, sample_weights, 3, 3, False)

    # Calculate mean and variance for the 9 sampled windows
    sample_mean = mean3.neighborhoodToBands(sample_kernel)
    sample_var = variance3.neighborhoodToBands(sample_kernel)

    # Calculate gradients across the 4 primary axes (0 vs 8, 1 vs 7, etc.)
    gradients = sample_mean.select(1).subtract(sample_mean.select(7)).abs()
    gradients = gradients.addBands(sample_mean.select(6).subtract(sample_mean.select(2)).abs())
    gradients = gradients.addBands(sample_mean.select(3).subtract(sample_mean.select(5)).abs())
    gradients = gradients.addBands(sample_mean.select(0).subtract(sample_mean.select(8)).abs())

    # Find the maximum gradient representing the edge
    max_gradient = gradients.reduce(ee.Reducer.max())

    # Mask pixels with maximum gradient
    gradmask = gradients.eq(max_gradient)
    # Duplicate to cover all 8 sub-directions
    gradmask = gradmask.addBands(gradmask)

    # Determine directional offsets
    directions = (
        sample_mean.select(1)
        .subtract(sample_mean.select(4))
        .gt(sample_mean.select(4).subtract(sample_mean.select(7)))
        .multiply(1)
    )
    directions = directions.addBands(
        sample_mean.select(6)
        .subtract(sample_mean.select(4))
        .gt(sample_mean.select(4).subtract(sample_mean.select(2)))
        .multiply(2)
    )
    directions = directions.addBands(
        sample_mean.select(3)
        .subtract(sample_mean.select(4))
        .gt(sample_mean.select(4).subtract(sample_mean.select(5)))
        .multiply(3)
    )
    directions = directions.addBands(
        sample_mean.select(0)
        .subtract(sample_mean.select(4))
        .gt(sample_mean.select(4).subtract(sample_mean.select(8)))
        .multiply(4)
    )
    # Add inverted directions (5-8)
    directions = directions.addBands(directions.select(0).Not().multiply(5))
    directions = directions.addBands(directions.select(1).Not().multiply(6))
    directions = directions.addBands(directions.select(2).Not().multiply(7))
    directions = directions.addBands(directions.select(3).Not().multiply(8))

    # Filter out directions that don't match the maximum gradient edge
    directions = directions.updateMask(gradmask)
    # Collapse stack to single direction band
    directions = directions.reduce(ee.Reducer.sum())

    # Calculate local noise variance
    sample_stats = sample_var.divide(sample_mean.multiply(sample_mean))
    sigmaV = (
        sample_stats.toArray()
        .arraySort()
        .arraySlice(0, 0, 5)
        .arrayReduce(ee.Reducer.mean(), [0])
    )

    # Define 7x7 directional sub-kernels
    rect_weights = ee.List.repeat(ee.List.repeat(0, 7), 3).cat(
        ee.List.repeat(ee.List.repeat(1, 7), 4)
    )
    diag_weights = ee.List([
        [1, 0, 0, 0, 0, 0, 0],
        [1, 1, 0, 0, 0, 0, 0],
        [1, 1, 1, 0, 0, 0, 0],
        [1, 1, 1, 1, 0, 0, 0],
        [1, 1, 1, 1, 1, 0, 0],
        [1, 1, 1, 1, 1, 1, 0],
        [1, 1, 1, 1, 1, 1, 1],
    ])

    rect_kernel = ee.Kernel.fixed(7, 7, rect_weights, 3, 3, False)
    diag_kernel = ee.Kernel.fixed(7, 7, diag_weights, 3, 3, False)

    # Create stacks for directional mean and variance
    dir_mean = img.reduceNeighborhood(ee.Reducer.mean(), rect_kernel).updateMask(directions.eq(1))
    dir_var = img.reduceNeighborhood(ee.Reducer.variance(), rect_kernel).updateMask(directions.eq(1))

    dir_mean = dir_mean.addBands(img.reduceNeighborhood(ee.Reducer.mean(), diag_kernel).updateMask(directions.eq(2)))
    dir_var = dir_var.addBands(img.reduceNeighborhood(ee.Reducer.variance(), diag_kernel).updateMask(directions.eq(2)))

    # Add rotated kernels for directions 3 to 8
    for i in range(1, 4):
        dir_mean = dir_mean.addBands(
            img.reduceNeighborhood(ee.Reducer.mean(), rect_kernel.rotate(i)).updateMask(directions.eq(2 * i + 1))
        )
        dir_var = dir_var.addBands(
            img.reduceNeighborhood(ee.Reducer.variance(), rect_kernel.rotate(i)).updateMask(directions.eq(2 * i + 1))
        )
        dir_mean = dir_mean.addBands(
            img.reduceNeighborhood(ee.Reducer.mean(), diag_kernel.rotate(i)).updateMask(directions.eq(2 * i + 2))
        )
        dir_var = dir_var.addBands(
            img.reduceNeighborhood(ee.Reducer.variance(), diag_kernel.rotate(i)).updateMask(directions.eq(2 * i + 2))
        )

    # Collapse directional stacks to single bands
    dir_mean = dir_mean.reduce(ee.Reducer.sum())
    dir_var = dir_var.reduce(ee.Reducer.sum())

    # Apply minimum mean square error (MMSE) filtering
    varX = dir_var.subtract(dir_mean.multiply(dir_mean).multiply(sigmaV)).divide(sigmaV.add(1.0))
    b_weight = varX.divide(dir_var)

    # Return the filtered value
    return (
        dir_mean.add(b_weight.multiply(img.subtract(dir_mean)))
        .arrayProject([0])
        .arrayFlatten([['sum']])
        .float()
        .rename(band_name)
    )

def refined_lee_filter(image):
    """
    Applies the edge-preserving Refined Lee Speckle Filter to a Sentinel-1 image.
    Uses static band lists to be fully compatible with server-side map operations in GEE.
    
    CRITICAL CONSTRAINTS:
    1. Terrain Correction: No additional manual Range-Doppler Terrain Correction (RDTC)
       is required because GEE's COPERNICUS/S1_GRD dataset has already been orthorectified
       and terrain-corrected by Google using the SRTM DEM (or equivalent). Do not duplicate or
       re-implement manual terrain correction.
    2. Projection: Native Sentinel-1 projection and scale must be strictly preserved.
       The function must not call .reproject() or .setDefaultProjection().
    """
    proc_bands = ['VV', 'VH']
    existing_keep_bands = ['angle']
    
    # 1. Convert to power (linear scale)
    proc_image = image.select(proc_bands)
    power = db_to_power(proc_image)
    
    # 2. Filter each band
    filtered_bands = []
    for band in proc_bands:
        filtered_band_power = apply_refined_lee_single_band(power, band)
        filtered_band_db = power_to_db(filtered_band_power)
        filtered_bands.append(filtered_band_db)
        
    # 3. Concatenate filtered bands
    output = ee.Image.cat(filtered_bands)
    
    # 4. Add back kept bands
    output = output.addBands(image.select(existing_keep_bands))
        
    return output

def add_derived_features(image):
    """
    Adds derived bands:
    - VV_VH_ratio (VV_dB - VH_dB, representing ratio in linear scale)
    - VV_VH_diff (linear VV - linear VH, converted back to dB)
    """
    vv = image.select('VV')
    vh = image.select('VH')
    
    # 1. Ratio in linear scale: VV / VH -> VV_dB - VH_dB
    ratio = vv.subtract(vh).rename('VV_VH_ratio')
    
    # 2. Difference in linear scale: VV_linear - VH_linear
    vv_linear = db_to_power(vv)
    vh_linear = db_to_power(vh)
    
    diff_linear = vv_linear.subtract(vh_linear)
    # Clamp to a tiny positive value to prevent log10 of negative or zero values
    diff_linear_clamped = diff_linear.max(0.0001)
    
    diff_db = power_to_db(diff_linear_clamped).rename('VV_VH_diff')
    
    return image.addBands([ratio, diff_db])

def check_preprocessing_quality(image):
    """
    Performs Quality Control checks on the preprocessed Sentinel-1 image.
    Calculates spatial mean backscatter over reference water/land polygons.
    Logs warnings if values fall outside expected ranges.
    Raises a ValueError (stops execution) if NaN/Infinity/None pixels are detected.
    
    CRITICAL CONSTRAINT: Original projection and scale are preserved.
    """
    from src.config import (
        WATER_REF_POLYGON, LAND_REF_POLYGON,
        EXPECTED_WATER_VV_MAX, EXPECTED_WATER_VH_MAX, EXPECTED_LAND_VV_MIN
    )
    import logging
    import math
    
    logger = logging.getLogger(__name__)
    
    # Create GEE geometry objects
    water_geom = ee.Geometry.Polygon(WATER_REF_POLYGON)
    land_geom = ee.Geometry.Polygon(LAND_REF_POLYGON)
    
    # Calculate mean backscatter values (must specify native scale=10 and projection)
    water_stats = image.select(['VV', 'VH']).reduceRegion(
        reducer=ee.Reducer.mean(),
        geometry=water_geom,
        scale=10,
        bestEffort=True
    )
    
    land_stats = image.select(['VV']).reduceRegion(
        reducer=ee.Reducer.mean(),
        geometry=land_geom,
        scale=10,
        bestEffort=True
    )
    
    # Get values from server side
    # (Since this is QC validation at the end of the phase, it is allowed to call .getInfo() to inspect)
    try:
        water_vv = water_stats.get('VV').getInfo()
        water_vh = water_stats.get('VH').getInfo()
        land_vv = land_stats.get('VV').getInfo()
    except Exception as e:
        logger.error(f"Failed to fetch QC statistics from GEE: {e}")
        raise ValueError(f"GEE QC Fetch Failure: {e}")
        
    # Check for NaN/Inf/None
    for val, name in [(water_vv, "Water VV"), (water_vh, "Water VH"), (land_vv, "Land VV")]:
        if val is None or math.isnan(val) or math.isinf(val):
            logger.error(f"QC FAILED: {name} mean value is invalid (NaN, Inf, or None).")
            raise ValueError(f"QC FAILED: Invalid pixel value {val} detected in {name} reference polygon.")
            
    # Soft range validation
    logger.info(f"QC: Preprocessing verification statistics computed:")
    logger.info(f" - Water Polygon Mean: VV={water_vv:.2f} dB (expected <= {EXPECTED_WATER_VV_MAX:.2f} dB)")
    logger.info(f" - Water Polygon Mean: VH={water_vh:.2f} dB (expected <= {EXPECTED_WATER_VH_MAX:.2f} dB)")
    logger.info(f" - Land Polygon Mean:  VV={land_vv:.2f} dB (expected >= {EXPECTED_LAND_VV_MIN:.2f} dB)")
    
    if water_vv > EXPECTED_WATER_VV_MAX:
        logger.warning(f"QC WARNING: Water VV mean ({water_vv:.2f} dB) exceeds expected max threshold ({EXPECTED_WATER_VV_MAX:.2f} dB).")
    if water_vh > EXPECTED_WATER_VH_MAX:
        logger.warning(f"QC WARNING: Water VH mean ({water_vh:.2f} dB) exceeds expected max threshold ({EXPECTED_WATER_VH_MAX:.2f} dB).")
    if land_vv < EXPECTED_LAND_VV_MIN:
        logger.warning(f"QC WARNING: Land VV mean ({land_vv:.2f} dB) is below expected min threshold ({EXPECTED_LAND_VV_MIN:.2f} dB).")
        
    return {
        'water_vv': water_vv,
        'water_vh': water_vh,
        'land_vv': land_vv,
        'status': 'PASS'
    }
