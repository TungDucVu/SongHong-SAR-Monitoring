"""
Preprocessing module for Sentinel-1 SAR imagery.
Implements border noise removal, the edge-preserving Refined Lee speckle filter,
and derived feature extraction (Ratio, Difference).
"""

import ee
from src.config import S1_BANDS

def db_to_power(img):
    """Convert backscatter intensity from decibels (dB) to power (linear scale)."""
    return ee.Image(10.0).pow(img.divide(10.0))

def power_to_db(img):
    """Convert backscatter intensity from power (linear scale) to decibels (dB)."""
    return img.log10().multiply(10.0)

def remove_border_noise(image):
    """
    Removes border noise and low-intensity edge anomalies from Sentinel-1 images.
    Uses incidence angle thresholds and minimum intensity masking.
    """
    # 1. Mask by incidence angle (valid range for IW mode is approx 30.6 to 45.9 degrees)
    angle = image.select('angle')
    angle_mask = angle.gt(30.6).And(angle.lt(45.9))
    
    # 2. Mask out extreme low-intensity backscatter values (usually noise at image borders)
    vv = image.select('VV')
    vh = image.select('VH')
    vv_mask = vv.gt(-30.0)
    vh_mask = vh.gt(-35.0)
    
    # Combined mask
    clean_mask = angle_mask.And(vv_mask).And(vh_mask)
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
