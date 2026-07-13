"""
Shoreline module for SongHong SAR Monitoring.
Implements post-classification raster refinement (Phase 4), boundary extraction (Phase 5),
shoreline graph cleaning (Phase 6), and Chaikin/Douglas-Peucker simplification (Phase 7).
"""

import os
import json
import ee
from src.config import CENTERLINE_GEOJSON_PATH

def load_centerline(project_id=None):
    """
    Loads local centerline GeoJSON and returns it as an ee.FeatureCollection.
    """
    if not ee.data.is_initialized():
        ee.Initialize(project=project_id)
        
    if not os.path.exists(CENTERLINE_GEOJSON_PATH):
        raise FileNotFoundError(f"Centerline GeoJSON not found at: {CENTERLINE_GEOJSON_PATH}")
        
    with open(CENTERLINE_GEOJSON_PATH, 'r', encoding='utf-8') as f:
        geojson_data = json.load(f)
        
    return ee.FeatureCollection(geojson_data)

def refine_classification(classified, aoi_geometry, centerline_fc=None, open_radius=2, close_radius=3):
    """
    Refines classified GEE image to produce cleaned binary Water and Sand masks.
    Applies:
      1. Majority filter (3x3)
      2. Morphological opening (disk)
      3. Morphological closing (disk)
      4. 2km centerline buffer clipping to restrict to Red River corridor.
      5. Focal connected pixel filtering to remove small noise components (< 50 pixels).
    
    Returns:
      water_mask_refined (ee.Image): Refined binary water mask (0 or 1).
      sand_mask_refined (ee.Image): Refined binary sand mask (0 or 1).
      qc_stats (dict): Earth Engine values containing count_before, count_after, and reduction_pct.
    """
    # 1. Base binary masks
    water_mask = classified.eq(1)
    sand_mask = classified.eq(2)
    
    # 2. Majority Filter (Focal Mode 3x3 square)
    water_maj = water_mask.focalMode(radius=1.5, kernelType='square', units='pixels')
    sand_maj = sand_mask.focalMode(radius=1.5, kernelType='square', units='pixels')
    
    # 3. Morphological Opening (Disk radius = open_radius)
    water_open = water_maj.focalMin(radius=open_radius, kernelType='circle', units='pixels')\
                          .focalMax(radius=open_radius, kernelType='circle', units='pixels')
    sand_open = sand_maj.focalMin(radius=open_radius, kernelType='circle', units='pixels')\
                        .focalMax(radius=open_radius, kernelType='circle', units='pixels')
                        
    # 4. Morphological Closing (Disk radius = close_radius)
    water_closed = water_open.focalMax(radius=close_radius, kernelType='circle', units='pixels')\
                            .focalMin(radius=close_radius, kernelType='circle', units='pixels')
    sand_closed = sand_open.focalMax(radius=close_radius, kernelType='circle', units='pixels')\
                          .focalMin(radius=close_radius, kernelType='circle', units='pixels')
                          
    # 5. Corridor Clipping (2km buffer around river centerline)
    if centerline_fc is None:
        centerline_fc = load_centerline()
        
    buffer_geom = centerline_fc.geometry().buffer(2000)
    
    water_buffered = water_closed.clip(buffer_geom)
    sand_buffered = sand_closed.clip(buffer_geom)
    
    # 6. Size-based filtering using connectedPixelCount to remove small noise components (< 50 pixels)
    water_self = water_buffered.selfMask()
    water_pixel_count = water_self.connectedPixelCount(100, True)
    water_mask_refined = water_self.updateMask(water_pixel_count.gte(50)).unmask(0).eq(1)
    
    sand_self = sand_buffered.selfMask()
    sand_pixel_count = sand_self.connectedPixelCount(100, True)
    sand_mask_refined = sand_self.updateMask(sand_pixel_count.gte(50)).unmask(0).eq(1)
    
    # 7. QC Statistics (Calculated at 200m WGS84 scale using countDistinct for complete stability)
    # We compare original unclipped water (water_closed) with refined water (water_mask_refined)
    water_200m = water_closed.reproject(crs='EPSG:4326', scale=200).gt(0.1).selfMask()
    water_200m_labeled = water_200m.connectedComponents(ee.Kernel.plus(1), 1024)
    count_before_val = water_200m_labeled.select('labels').reduceRegion(
        reducer=ee.Reducer.countDistinct(),
        geometry=aoi_geometry,
        scale=200,
        maxPixels=1e9
    ).get('labels')
    
    water_refined_200m = water_mask_refined.reproject(crs='EPSG:4326', scale=200).gt(0.1).selfMask()
    water_refined_200m_labeled = water_refined_200m.connectedComponents(ee.Kernel.plus(1), 1024)
    count_after_val = water_refined_200m_labeled.select('labels').reduceRegion(
        reducer=ee.Reducer.countDistinct(),
        geometry=aoi_geometry,
        scale=200,
        maxPixels=1e9
    ).get('labels')
    
    count_before = ee.Number(ee.Algorithms.If(count_before_val, count_before_val, 0))
    count_after = ee.Number(ee.Algorithms.If(count_after_val, count_after_val, 0))
    
    # Make sure we don't divide by zero or have unrealistic reduction percentages
    reduction_pct = ee.Number(ee.Algorithms.If(
        count_before.gt(0),
        count_before.subtract(count_after).divide(count_before).multiply(100.0),
        100.0
    ))
    
    qc_stats = {
        'count_before': count_before,
        'count_after': count_after,
        'reduction_pct': reduction_pct
    }
    
    return water_mask_refined, sand_mask_refined, qc_stats
