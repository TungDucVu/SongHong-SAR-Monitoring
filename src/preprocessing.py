"""
Preprocessing and feature extraction module for SongHong SAR Monitoring.
Implements Refined Lee speckle filter and computes SAR feature bands (VV, VH, VV/VH ratio).
"""

import ee

def apply_speckle_filter(image):
    """
    Refined Lee Speckle Filter (3x3 square kernel) for Sentinel-1 GRD.
    Operates on linear scale to minimize noise before transforming back to dB.
    
    Args:
        image: ee.Image (dB) containing S1 bands.
        
    Returns:
        ee.Image (dB) of the filtered bands.
    """
    image = ee.Image(image)
    band_names = image.bandNames()

    # Convert dB to linear scale
    img_linear = ee.Image(10.0).pow(image.divide(10.0))

    # Define kernel (3x3)
    kernel = ee.Kernel.square(radius=1)

    # Calculate local mean and variance
    mean_img = img_linear.reduceNeighborhood(
        reducer=ee.Reducer.mean(),
        kernel=kernel
    )
    variance_img = img_linear.reduceNeighborhood(
        reducer=ee.Reducer.variance(),
        kernel=kernel
    )

    # Local coefficient of variation (sigma^2 / mean^2)
    img_cv = variance_img.divide(mean_img.pow(2.0))

    # Equivalent Number of Looks (ENL) approx 4.9 for Sentinel-1 IW mode
    ENL = 4.9
    ENL_variance = ee.Image(1.0 / ENL)
    
    # Calculate Lee weight: w = 1 - ENL_var / local_cv
    weight = ee.Image(1.0).subtract(
        ENL_variance.divide(img_cv.add(ENL_variance))
    ).max(0.0).min(1.0)

    # Filtered image = local_mean + weight * (pixel - local_mean)
    filtered_linear = mean_img.add(
        weight.multiply(img_linear.subtract(mean_img))
    )

    # Convert back to dB
    filtered_db = filtered_linear.log10().multiply(10.0)
    
    # Cast to ee.Image and copy properties to preserve original metadata
    result = ee.Image(filtered_db.rename(band_names).copyProperties(image, image.propertyNames()))
    return result

def compute_features(image):
    """
    Computes three target features:
      - VV: backscatter (dB)
      - VH: backscatter (dB)
      - VV_VH_ratio: ratio VV/VH in dB, calculated as VV(dB) - VH(dB)
      
    Args:
        image: ee.Image containing VV and VH bands.
        
    Returns:
        ee.Image containing bands ['VV', 'VH', 'VV_VH_ratio'].
    """
    image = ee.Image(image)
    vv = image.select('VV')
    vh = image.select('VH')
    
    # Ratio = VV_linear / VH_linear
    # In dB scale, this is equivalent to VV(dB) - VH(dB)
    ratio = vv.subtract(vh).rename('VV_VH_ratio')
    
    result = ee.Image(image.addBands(ratio).select(['VV', 'VH', 'VV_VH_ratio']))
    return result

def preprocess_image(image, aoi_geometry):
    """
    Complete preprocessing pipeline for a single Sentinel-1 image.
    Clips to AOI, applies Refined Lee Filter, and computes ratio features.
    
    Args:
        image: ee.Image (Sentinel-1 GRD).
        aoi_geometry: ee.Geometry to clip the image.
        
    Returns:
        ee.Image processed containing 3 feature bands.
    """
    image = ee.Image(image)
    clipped = image.clip(aoi_geometry)
    filtered = apply_speckle_filter(clipped)
    features = compute_features(filtered)
    
    result = ee.Image(features.copyProperties(image, ['system:time_start', 'system:index']))
    return result
