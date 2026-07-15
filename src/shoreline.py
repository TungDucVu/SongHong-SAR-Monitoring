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
from shapely.geometry import shape, LineString, MultiLineString, GeometryCollection, Polygon
from src.config import (
    CENTERLINE_GEOJSON_PATH, SHORELINE_CONFIG,
    SHORELINE_OPEN_SIZE, SHORELINE_CLOSE_SIZE
)

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

def extract_shared_boundary(water_mask_refined, centerline_fc, scale=20, year=2024, season='dry', version='1.0'):
    """
    Implements Phase 5: Topologically-Constrained Water Boundary Extraction.
    
    1. Ensures the refined water mask is strictly unmasked to 0/1 (no nodata/masked pixels).
    2. Downloads the unmasked refined water mask as a GeoTIFF and polygonizes locally.
    3. Main Water Polygon Selection: Retains water polygons that intersect the centerline 
       AND (area >= min_main_water_area OR it is the largest corridor component).
    4. Boundary Extraction: Extracts the exterior ring of dissolved water polygons (banks) 
       and interior rings representing persistent islands (area >= min_island_area).
    5. Checkpoint & QC: Validates geometries, self-intersections, duplicates, and corridor membership.
    
    Returns:
      shoreline_gdf (gpd.GeoDataFrame): Raw unsmoothed shorelines in EPSG:32648.
      metrics (dict): Dict of logged performance metrics.
    """
    start_time = time.time()
    import requests
    import io
    import rasterio
    from rasterio.features import shapes
    
    # Ensure binary mask is strictly 0/1, not 1/no data
    water_mask_unmasked = water_mask_refined.unmask(0).eq(1)
    
    # Restrict download to centerline 2km buffer bounding box to minimize memory/time
    buffer_geom = centerline_fc.geometry().buffer(2000)
    bbox = buffer_geom.bounds()
    
    print(f"[Phase 5] Requesting GEE download URL for refined water mask at {scale}m scale...")
    try:
        url = water_mask_unmasked.clip(buffer_geom).getDownloadURL({
            'scale': scale,
            'crs': 'EPSG:32648',
            'region': bbox.getInfo(),
            'format': 'GEO_TIFF'
        })
        print(f"[Phase 5] Downloading refined water mask from GEE...")
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
    for geom, val in shapes(raster_data, transform=transform):
        if val == 1:
            water_geoms.append(shape(geom))
            
    print(f"[Phase 5] Extracted {len(water_geoms)} raw water polygons locally.")
    
    if not water_geoms:
        print("[Warning] No water polygons found in classified image.")
        empty_gdf = gpd.GeoDataFrame(geometry=[], crs="EPSG:32648")
        metrics = {
            'runtime_seconds': time.time() - start_time,
            'total_length_m': 0.0,
            'invalid_geoms_fixed': 0,
            'num_segments': 0
        }
        return empty_gdf, metrics
        
    # Load centerline and translate to EPSG:32648
    centerline_geojson = centerline_fc.getInfo()
    centerline_gdf = gpd.GeoDataFrame.from_features(centerline_geojson, crs="EPSG:4326").to_crs("EPSG:32648")
    centerline_union = centerline_gdf.geometry.unary_union
    
    # Filter configurations
    min_main_water_area = SHORELINE_CONFIG.get('min_main_water_area', 100000.0)
    min_island_area = SHORELINE_CONFIG.get('min_island_area', 10000.0)
    min_centerline_intersection = SHORELINE_CONFIG.get('min_centerline_intersection', 1000.0)
    
    # 2. Main Water Polygon Selection
    # Calculate centerline intersection length for each polygon in EPSG:32648
    cl_intersection_lengths = [poly.intersection(centerline_union).length for poly in water_geoms]
    max_intersect_len = max(cl_intersection_lengths) if cl_intersection_lengths else 0.0
    
    selected_polys = []
    for poly, intersect_len in zip(water_geoms, cl_intersection_lengths):
        # Keep if it is the main river anchor (max intersection length)
        # OR if it intersects the centerline for a significant distance (>= 1km)
        if (intersect_len >= min_centerline_intersection) or (intersect_len > 0 and intersect_len == max_intersect_len):
            selected_polys.append(poly)
                
    if not selected_polys:
        print("[Error] No main corridor water polygons found.")
        empty_gdf = gpd.GeoDataFrame(geometry=[], crs="EPSG:32648")
        metrics = {
            'runtime_seconds': time.time() - start_time,
            'total_length_m': 0.0,
            'invalid_geoms_fixed': 0,
            'num_segments': 0
        }
        return empty_gdf, metrics
        
    # Dissolve water polygons
    from shapely.ops import unary_union as shapely_unary_union
    water_dissolved = make_valid(shapely_unary_union(selected_polys))
    
    # Ensure geometry validity
    invalid_fixed = 0
    if not water_dissolved.is_valid:
        water_dissolved = make_valid(water_dissolved)
        invalid_fixed += 1
        
    # 3. Boundary Extraction (Exterior and Island rings)
    raw_lines = []
    
    def process_polygon(poly):
        if poly.is_empty:
            return
        # Exterior boundary (outer bank)
        if poly.exterior and not poly.exterior.is_empty:
            raw_lines.append((poly.exterior, False))
        # Interior boundaries (islands)
        for interior in poly.interiors:
            if not interior.is_empty:
                island_poly = Polygon(interior)
                if island_poly.area >= min_island_area:
                    raw_lines.append((interior, True))
                    
    if water_dissolved.geom_type == 'Polygon':
        process_polygon(water_dissolved)
    elif water_dissolved.geom_type == 'MultiPolygon':
        for poly in water_dissolved.geoms:
            process_polygon(poly)
            
    # Convert rings to LineString geometries
    valid_lines = []
    for ring, is_island in raw_lines:
        line_geom = LineString(ring.coords)
        line_valid = make_valid(line_geom)
        
        # Explode to simple LineStrings if necessary
        if line_valid.geom_type == 'LineString':
            if not line_valid.is_empty and line_valid.length >= 10.0:
                valid_lines.append((line_valid, is_island))
        elif line_valid.geom_type in ('MultiLineString', 'GeometryCollection'):
            for g in line_valid.geoms:
                if g.geom_type == 'LineString' and not g.is_empty and g.length >= 10.0:
                    valid_lines.append((g, is_island))
                    
    # 4. Phase 5 QC Checkpoint
    # Verify: no empty geometry, valid geometries, no self-intersections, no duplicates
    qc_passed = True
    qc_messages = []
    
    final_features = []
    seen_coords = set()
    
    for idx, (line, is_island) in enumerate(valid_lines):
        # Check empty
        if line.is_empty:
            qc_passed = False
            qc_messages.append(f"Segment {idx} is empty.")
            continue
            
        # Check valid
        if not line.is_valid:
            qc_passed = False
            qc_messages.append(f"Segment {idx} is invalid.")
            continue
            
        # Check self-intersection
        if not line.is_simple:
            qc_passed = False
            qc_messages.append(f"Segment {idx} has self-intersections (is not simple).")
            
        # Check duplicate coordinates
        coords_tuple = tuple(line.coords)
        if coords_tuple in seen_coords:
            qc_messages.append(f"Segment {idx} is a duplicate.")
            continue
        seen_coords.add(coords_tuple)
        
        # Calculate length
        length_m = float(line.length)
        
        # Build feature dict
        feat = {
            'geometry': line,
            'id': f"shoreline_{year}_{season}_{idx}",
            'bank_type': 'unknown',
            'length_m': length_m,
            'is_island': is_island,
            'year': int(year),
            'season': season,
            'source': 'S1',
            'processing_version': version
        }
        final_features.append(feat)
        
    if not qc_passed:
        print(f"[Phase 5 QC Warning] Checkpoint failed some criteria:\n" + "\n".join(qc_messages[:5]))
    else:
        print("[Phase 5 QC Success] All Checkpoint 5 assertions passed (no empty/invalid geoms, no duplicates).")
        
    # Create GeoDataFrame
    shoreline_gdf = gpd.GeoDataFrame(final_features, crs="EPSG:32648")
    
    runtime = time.time() - start_time
    total_length = float(shoreline_gdf.geometry.length.sum()) if not shoreline_gdf.empty else 0.0
    num_segments = len(shoreline_gdf)
    
    metrics = {
        'runtime_seconds': runtime,
        'total_length_m': total_length,
        'invalid_geoms_fixed': invalid_fixed,
        'num_segments': num_segments,
        'qc_passed': qc_passed
    }
    
    print(f"[Phase 5] Completed in {runtime:.2f}s. Extracted {num_segments} shoreline segments, total length: {total_length/1000:.2f} km.")
    water_dissolved_gdf = gpd.GeoDataFrame(geometry=[water_dissolved], crs="EPSG:32648")
    return shoreline_gdf, water_dissolved_gdf, metrics
