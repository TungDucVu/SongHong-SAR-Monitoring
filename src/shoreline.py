"""
Shoreline module for SongHong SAR Monitoring.
Implements post-classification raster refinement (Phase 4), boundary extraction (Phase 5),
shoreline graph cleaning (Phase 6), and Chaikin/Douglas-Peucker simplification (Phase 7).
"""

import os
import json
import time
import ee
import geopandas as gpd
from shapely.validation import make_valid
from shapely.geometry import shape, LineString, MultiLineString, GeometryCollection
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

def extract_shared_boundary(classified, aoi_geometry, centerline_fc, scale=20):
    """
    Implements Phase 5: Shared Boundary Extraction.
    
    Performs GEE polygonization on raw majority-filtered masks, and then
    runs all morphological operations, corridor clipping, and topological intersection
    locally in Python using Shapely/GeoPandas to completely avoid GEE memory limits.
    
    Returns:
      shoreline_gdf (gpd.GeoDataFrame): Raw unsmoothed shorelines in EPSG:32648.
      metrics (dict): Dict of logged performance metrics.
    """
    start_time = time.time()
    import requests
    import io
    import rasterio
    from rasterio.features import shapes
    
    # Restrict to 2km centerline corridor box to minimize size and memory usage
    buffer_geom = centerline_fc.geometry().buffer(2000)
    classified_clipped = classified.clip(buffer_geom)
    
    # 1. Prepare raw masks in GEE with simple 3x3 majority filter (very light)
    water_mask = classified_clipped.eq(1).focalMode(radius=1.5, kernelType='square', units='pixels')
    sand_mask = classified_clipped.eq(2).focalMode(radius=1.5, kernelType='square', units='pixels')
    
    combined_mask = ee.Image(0).where(water_mask, 1).where(sand_mask, 2)
    
    # Get bounding box of centerline buffer to download
    bbox = buffer_geom.bounds()
    
    print(f"[Phase 5] Requesting GEE download URL for classified mask at {scale}m scale...")
    try:
        url = combined_mask.getDownloadURL({
            'scale': scale,
            'crs': 'EPSG:32648',
            'region': bbox.getInfo(),
            'format': 'GEO_TIFF'
        })
        print(f"[Phase 5] Downloading classification mask from GEE...")
        r = requests.get(url, timeout=300)
        r.raise_for_status()
    except Exception as e:
        print(f"[Error] GEE download failed: {e}")
        raise e
        
    print(f"[Phase 5] Parsing GeoTIFF and polygonizing locally...")
    with rasterio.open(io.BytesIO(r.content)) as src:
        raster_data = src.read(1)
        transform = src.transform
        
    water_geoms = []
    sand_geoms = []
    for geom, val in shapes(raster_data, transform=transform):
        if val == 1:
            water_geoms.append(shape(geom))
        elif val == 2:
            sand_geoms.append(shape(geom))
            
    print(f"[Phase 5] Extracted {len(water_geoms)} water and {len(sand_geoms)} sand polygons locally.")
    
    # If no features, return empty GDF
    if not water_geoms or not sand_geoms:
        empty_gdf = gpd.GeoDataFrame(geometry=[], crs="EPSG:32648")
        metrics = {
            'runtime_seconds': time.time() - start_time,
            'total_length_m': 0.0,
            'invalid_geoms_fixed': 0,
            'removed_loops': 0,
            'num_segments': 0
        }
        return empty_gdf, metrics
        
    water_gdf = gpd.GeoDataFrame(geometry=water_geoms, crs="EPSG:32648")
    sand_gdf = gpd.GeoDataFrame(geometry=sand_geoms, crs="EPSG:32648")
    
    # 4. Load Centerline
    centerline_geojson = centerline_fc.getInfo()
    centerline_gdf = gpd.GeoDataFrame.from_features(centerline_geojson, crs="EPSG:4326").to_crs("EPSG:32648")
    centerline_union = centerline_gdf.geometry.unary_union
    centerline_buffer = centerline_union.buffer(2000)
    
    # 5. Dissolve & Validate raw geometries
    print("[Phase 5] Dissolving water and sand polygons...")
    water_union = water_gdf.geometry.unary_union
    sand_union = sand_gdf.geometry.unary_union
    
    water_clean = make_valid(water_union.buffer(0))
    sand_clean = make_valid(sand_union.buffer(0))
    
    invalid_fixed = 0
    if not water_clean.is_valid:
        water_clean = make_valid(water_clean)
        invalid_fixed += 1
    if not sand_clean.is_valid:
        sand_clean = make_valid(sand_clean)
        invalid_fixed += 1
        
    # 6. Morphological Refinement locally in Python
    # Open: buffer(-20).buffer(20) to remove thin noise/channels
    # Close: buffer(30).buffer(-30) to fill internal holes
    print("[Phase 5] Running local morphological opening/closing and corridor clipping...")
    water_refined = water_clean.buffer(-20).buffer(20).buffer(30).buffer(-30)
    sand_refined = sand_clean.buffer(-20).buffer(20).buffer(30).buffer(-30)
    
    # Clip to centerline buffer corridor
    water_corridor = make_valid(water_refined.intersection(centerline_buffer))
    sand_corridor = make_valid(sand_refined.intersection(centerline_buffer))
    
    # Separate the main water corridor that intersects the centerline
    water_polys = []
    if water_corridor.geom_type == 'Polygon':
        water_polys.append(water_corridor)
    elif water_corridor.geom_type == 'MultiPolygon':
        water_polys.extend(list(water_corridor.geoms))
        
    main_water_polys = []
    for poly in water_polys:
        if poly.intersects(centerline_union.buffer(10.0)):
            main_water_polys.append(poly)
            
    if not main_water_polys:
        # fallback
        if water_polys:
            main_water_polys = [max(water_polys, key=lambda p: p.area)]
            
    if not main_water_polys:
        print("[Error] No valid water polygons found.")
        empty_gdf = gpd.GeoDataFrame(geometry=[], crs="EPSG:32648")
        metrics = {
            'runtime_seconds': time.time() - start_time,
            'total_length_m': 0.0,
            'invalid_geoms_fixed': invalid_fixed,
            'removed_loops': 0,
            'num_segments': 0
        }
        return empty_gdf, metrics
        
    from shapely.ops import unary_union as shapely_unary_union
    water_main = make_valid(shapely_unary_union(main_water_polys).buffer(0))
    
    # Filter out sandbar components smaller than 50 pixels (5000 sq meters)
    sand_polys = []
    if sand_corridor.geom_type == 'Polygon':
        sand_polys.append(sand_corridor)
    elif sand_corridor.geom_type == 'MultiPolygon':
        sand_polys.extend(list(sand_corridor.geoms))
        
    filtered_sand_polys = [p for p in sand_polys if p.area >= 5000.0]
    if filtered_sand_polys:
        sand_main = make_valid(shapely_unary_union(filtered_sand_polys).buffer(0))
    else:
        sand_main = gpd.GeoDataFrame(geometry=[], crs="EPSG:32648").geometry.unary_union
        
    # 7. Shared Boundary Extraction
    print("[Phase 5] Extracting water-sand shared boundary...")
    raw_boundary = water_main.boundary.intersection(sand_main.buffer(0.1))
    
    # 8. Explode into individual LineStrings
    raw_lines = []
    def extract_linestrings(geom):
        if geom.is_empty:
            return
        if geom.geom_type == 'LineString':
            raw_lines.append(geom)
        elif geom.geom_type in ('MultiLineString', 'GeometryCollection'):
            for g in geom.geoms:
                extract_linestrings(g)
                
    extract_linestrings(raw_boundary)
    raw_lines = [line for line in raw_lines if line.length >= 5.0]
    
    # 9. Closed Loop Filtering
    valid_lines = []
    removed_loops = 0
    
    for line in raw_lines:
        if line.is_closed:
            if line.length < 50.0:
                removed_loops += 1
                continue
            else:
                valid_lines.append(line)
        else:
            valid_lines.append(line)
            
    shoreline_gdf = gpd.GeoDataFrame(geometry=valid_lines, crs="EPSG:32648")
    
    runtime = time.time() - start_time
    total_length = float(shoreline_gdf.geometry.length.sum())
    num_segments = len(shoreline_gdf)
    
    metrics = {
        'runtime_seconds': runtime,
        'total_length_m': total_length,
        'invalid_geoms_fixed': invalid_fixed,
        'removed_loops': removed_loops,
        'num_segments': num_segments
    }
    
    print(f"[Phase 5] Completed in {runtime:.2f}s. Extracted {num_segments} segments, total length: {total_length/1000:.2f} km. Removed {removed_loops} loops.")
    return shoreline_gdf, metrics
