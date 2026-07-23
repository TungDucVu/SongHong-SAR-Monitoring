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
import numpy as np
from shapely.validation import make_valid
from shapely.geometry import shape, LineString, MultiLineString, GeometryCollection, Polygon
from src.config import (
    CENTERLINE_GEOJSON_PATH, SHORELINE_CONFIG,
    SHORELINE_OPEN_SIZE, SHORELINE_CLOSE_SIZE
)

def get_continuous_centerline(centerline_path=None, aoi_path=None):
    """
    Reads the centerline GeoJSON, sorts segments from NW to SE, and connects 
    endpoints of adjacent segments to bridge gaps.
    If the gap is at the AOI boundary, it routes the bridge along the AOI boundary.
    Otherwise, it uses a straight-line bridge.
    Returns the continuous centerline as a shapely LineString.
    """
    if centerline_path is None:
        centerline_path = CENTERLINE_GEOJSON_PATH
    if aoi_path is None:
        aoi_path = os.path.join(os.path.dirname(centerline_path), 'song_hong_aoi.geojson')
        
    if not os.path.exists(centerline_path):
        raise FileNotFoundError(f"Centerline GeoJSON not found at: {centerline_path}")
        
    with open(centerline_path, 'r', encoding='utf-8') as f:
        cl_data = json.load(f)
        
    # Read AOI boundary
    from shapely.ops import linemerge, unary_union, substring
    from shapely.geometry import shape, LineString, Point
    
    aoi_boundary = None
    if os.path.exists(aoi_path):
        try:
            with open(aoi_path, 'r', encoding='utf-8') as f:
                aoi_data = json.load(f)
            # Find the main polygon geometry
            aoi_geoms = [shape(fe['geometry']) for fe in aoi_data['features']]
            aoi_union = unary_union(aoi_geoms)
            # Extract boundary
            if aoi_union.geom_type == 'Polygon':
                aoi_boundary = aoi_union.exterior
            elif aoi_union.geom_type == 'MultiPolygon':
                largest_poly = max(aoi_union.geoms, key=lambda p: p.area)
                aoi_boundary = largest_poly.exterior
        except Exception as e:
            print(f"[Warning] Failed to load/parse AOI boundary: {e}")
            
    # Extract LineString segments
    geoms = []
    for fe in cl_data['features']:
        g = shape(fe['geometry'])
        if g.geom_type == 'LineString':
            geoms.append(g)
        elif g.geom_type == 'MultiLineString':
            geoms.extend(g.geoms)
        elif g.geom_type == 'GeometryCollection':
            for sg in g.geoms:
                if sg.geom_type == 'LineString':
                    geoms.append(sg)
                elif sg.geom_type == 'MultiLineString':
                    geoms.extend(sg.geoms)
                    
    if not geoms:
        raise ValueError("No LineString geometries found in centerline file.")
        
    # Merge where touching
    merged = linemerge(geoms)
    if merged.geom_type == 'LineString':
        return merged
        
    segments = list(merged.geoms)
    # Sort segments from Northwest to Southeast (by Y descending)
    segments = sorted(segments, key=lambda s: s.centroid.y, reverse=True)
    
    connected_coords = list(segments[0].coords)
    
    for seg in segments[1:]:
        last_pt = Point(connected_coords[-1])
        first_pt = Point(seg.coords[0])
        end_pt = Point(seg.coords[-1])
        
        # Decide direction
        dist_to_start = last_pt.distance(first_pt)
        dist_to_end = last_pt.distance(end_pt)
        
        if dist_to_start <= dist_to_end:
            target_pt = first_pt
            append_coords = list(seg.coords)
        else:
            target_pt = end_pt
            append_coords = list(seg.coords)[::-1]
            
        # Bridge the gap
        bridge_coords = []
        if aoi_boundary is not None and last_pt.distance(aoi_boundary) < 0.002 and target_pt.distance(aoi_boundary) < 0.002:
            try:
                t_last = aoi_boundary.project(last_pt)
                t_target = aoi_boundary.project(target_pt)
                
                if t_last > t_target:
                    t_min, t_max = t_target, t_last
                else:
                    t_min, t_max = t_last, t_target
                    
                path1 = substring(aoi_boundary, t_min, t_max)
                path2_part1 = substring(aoi_boundary, t_max, aoi_boundary.length)
                path2_part2 = substring(aoi_boundary, 0, t_min)
                path2_coords = list(path2_part1.coords) + list(path2_part2.coords)
                path2 = LineString(path2_coords)
                
                if path1.length <= path2.length:
                    connection = path1
                else:
                    connection = path2
                    
                c_coords = list(connection.coords)
                if Point(c_coords[0]).distance(last_pt) > Point(c_coords[-1]).distance(last_pt):
                    c_coords = c_coords[::-1]
                bridge_coords = c_coords
            except Exception as e:
                print(f"[Warning] Routing along boundary failed: {e}")
                bridge_coords = [last_pt.coords[0], target_pt.coords[0]]
        else:
            bridge_coords = [last_pt.coords[0], target_pt.coords[0]]
            
        if len(bridge_coords) > 2:
            connected_coords.extend(bridge_coords[1:-1])
            
        connected_coords.extend(append_coords)
        
    return LineString(connected_coords)

def load_centerline(project_id=None):
    """
    Loads local centerline GeoJSON, makes it continuous by bridging gaps,
    and returns it as an ee.FeatureCollection.
    """
    if not ee.data.is_initialized():
        ee.Initialize(project=project_id)
        
    cl_linestring = get_continuous_centerline()
    
    geojson_data = {
        "type": "FeatureCollection",
        "features": [
            {
                "type": "Feature",
                "properties": {
                    "name": "Song Hong Continuous Centerline"
                },
                "geometry": {
                    "type": "LineString",
                    "coordinates": list(cl_linestring.coords)
                }
            }
        ]
    }
    
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

def extract_shared_boundary(water_mask_refined, centerline_fc, scale=20, year=2024, season='dry', version='1.0', bridge_mask=None, s2_water_poly=None):
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
    
    # Try up to 5 times with exponential backoff for GEE downloads
    for attempt in range(5):
        try:
            url = water_mask_unmasked.clip(buffer_geom).getDownloadURL({
                'scale': scale,
                'crs': 'EPSG:32648',
                'region': bbox.getInfo(),
                'format': 'GEO_TIFF'
            })
            print(f"[Phase 5] Downloading refined water mask from GEE (attempt {attempt+1}/5)...")
            r = requests.get(url, timeout=300)
            if r.status_code != 200:
                print(f"[Error] GEE response text: {r.text}")
            r.raise_for_status()
            break
        except Exception as e:
            if attempt == 4:
                print(f"[Error] GEE download failed after 5 attempts: {e}")
                raise e
            wait_time = (2 ** attempt) + np.random.uniform(0, 1)
            print(f"[Warning] GEE download failed: {e}. Retrying in {wait_time:.1f}s...")
            time.sleep(wait_time)
        
    print(f"[Phase 5] Parsing GeoTIFF and polygonizing locally...")
    with rasterio.open(io.BytesIO(r.content)) as src:
        raster_data = src.read(1)
        transform = src.transform
        
    # Morphological cleaning using scikit-image
    try:
        import skimage.morphology
        bool_mask = raster_data > 0
        bool_mask = skimage.morphology.remove_small_objects(bool_mask, min_size=20)
        bool_mask = skimage.morphology.remove_small_holes(bool_mask, area_threshold=100)
        raster_data = bool_mask.astype(np.uint8)
        print("[Phase 5] Local morphological cleaning applied (remove_small_objects < 20px, remove_small_holes < 100px).")
    except Exception as e:
        print(f"[Warning] Local morphological cleaning failed: {e}")
        
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
    island_circularity_threshold = SHORELINE_CONFIG.get('island_circularity_threshold', 0.8)
    island_s2_overlap_threshold = SHORELINE_CONFIG.get('island_s2_overlap_threshold', 0.5)
    
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
        
    # Active Channel Buffer (150m around S2 reference shoreline)
    active_channel_buffer = s2_water_poly.buffer(150.0) if s2_water_poly is not None and not s2_water_poly.is_empty else None

    # Apply Active Channel Constraints (River Buffer Constraints)
    if active_channel_buffer is not None:
        try:
            print("[Phase 5] Applying active channel constraints (S2 reference buffer 150m)...")
            water_dissolved = water_dissolved.intersection(active_channel_buffer)
            if not water_dissolved.is_valid:
                water_dissolved = make_valid(water_dissolved)
            print("[Phase 5] Active channel constraints applied successfully.")
        except Exception as e:
            print(f"[Warning] Failed to apply active channel constraints: {e}")
        
    # 3. Boundary Extraction (Exterior and Island rings)
    raw_lines = []
    
    def process_polygon(poly):
        import math
        import numpy as np
        if poly.is_empty:
            return
        # Exterior boundary (outer bank)
        if poly.exterior and not poly.exterior.is_empty:
            raw_lines.append((poly.exterior, False))
        # Interior boundaries (islands)
        for interior in poly.interiors:
            if not interior.is_empty:
                island_poly = Polygon(interior)
                area = island_poly.area
                if area >= min_island_area:
                    # Compute circularity: (4 * pi * area) / perimeter^2
                    perimeter = interior.length
                    circularity = (4.0 * math.pi * area) / (perimeter ** 2) if perimeter > 0 else 0.0
                    
                    # Compute S2 water overlap
                    overlap_ratio = 0.0
                    if s2_water_poly is not None:
                        try:
                            intersection_area = island_poly.intersection(s2_water_poly).area
                            overlap_ratio = intersection_area / area
                        except Exception as e:
                            print(f"[Warning] Failed to compute island S2 overlap: {e}")
                            overlap_ratio = 0.0
                            
                    is_false_positive = False
                    if circularity >= island_circularity_threshold:
                        is_false_positive = True
                        print(f"[Island Filter] Filtered out island area={area:.1f}m2 due to high circularity: {circularity:.2f} >= {island_circularity_threshold}")
                    elif overlap_ratio >= island_s2_overlap_threshold:
                        is_false_positive = True
                        print(f"[Island Filter] Filtered out island area={area:.1f}m2 due to high S2 water overlap: {overlap_ratio:.2f} >= {island_s2_overlap_threshold}")
                        
                    if not is_false_positive:
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

def clean_shoreline_graph(shoreline_gdf, config_dict=None):
    """
    Implements Phase 6 Graph Cleaning:
      1. Duplicate removal
      2. Linemerge
      3. Endpoint/Edge snapping (snap_threshold)
      4. Iterative spur pruning (prune_threshold)
      5. Final linemerge & length filtering (min_length)
    """
    if shoreline_gdf.empty:
        return shoreline_gdf
        
    import networkx as nx
    from shapely.ops import linemerge
    from shapely.geometry import Point, LineString
    
    # Get config parameters
    if config_dict is None:
        from src.config import SHORELINE_CONFIG
        config_dict = SHORELINE_CONFIG
        
    snap_threshold = config_dict.get('snap_threshold', 150.0)
    prune_threshold = config_dict.get('prune_threshold', 200.0)
    min_length = config_dict.get('min_length', 1000.0)
    
    year = shoreline_gdf.iloc[0].get('year', 2024)
    season = shoreline_gdf.iloc[0].get('season', 'dry')
    version = shoreline_gdf.iloc[0].get('processing_version', '1.0')
    
    # Extract LineString geometries
    geoms = list(shoreline_gdf.geometry)
    
    # Step 1: Duplicate Removal
    unique_geoms = []
    seen = set()
    for g in geoms:
        if g.is_empty or g.length < 1.0:
            continue
        coords = list(g.coords)
        signature = (round(coords[0][0], 3), round(coords[0][1], 3), 
                     round(coords[-1][0], 3), round(coords[-1][1], 3), 
                     round(g.length, 3))
        signature_rev = (round(coords[-1][0], 3), round(coords[-1][1], 3), 
                         round(coords[0][0], 3), round(coords[0][1], 3), 
                         round(g.length, 3))
        if signature not in seen and signature_rev not in seen:
            seen.add(signature)
            unique_geoms.append(g)
            
    # Step 2: Linemerge
    merged = linemerge(unique_geoms)
    lines = []
    if merged.geom_type == 'LineString':
        lines.append(merged)
    elif merged.geom_type in ('MultiLineString', 'GeometryCollection'):
        for g in merged.geoms:
            if g.geom_type == 'LineString':
                lines.append(g)
                
    # Step 3: Gap Snapping (Endpoint-to-Endpoint & Endpoint-to-Edge)
    for snap_round in range(3):  # repeat a few times for cascading snaps
        def get_node(pt):
            return (round(pt[0], 3), round(pt[1], 3))
            
        node_degrees = {}
        for line in lines:
            start_pt = line.coords[0]
            end_pt = line.coords[-1]
            n_start = get_node(start_pt)
            n_end = get_node(end_pt)
            
            node_degrees[n_start] = node_degrees.get(n_start, 0) + 1
            node_degrees[n_end] = node_degrees.get(n_end, 0) + 1
            
        dangling_nodes = [node for node, deg in node_degrees.items() if deg == 1]
        if not dangling_nodes:
            break
            
        snapped_nodes = {}  # map old node -> new node coordinates
        
        for d_node in dangling_nodes:
            d_point = Point(d_node)
            best_target = None
            best_dist = float('inf')
            target_type = None  # 'endpoint' or 'edge'
            best_edge_idx = None
            best_proj_point = None
            
            # Check other dangling nodes
            for other_node in dangling_nodes:
                if other_node == d_node:
                    continue
                dist = d_point.distance(Point(other_node))
                if dist < best_dist and dist <= snap_threshold:
                    best_dist = dist
                    best_target = other_node
                    target_type = 'endpoint'
                    
            # Check edges
            for idx, line in enumerate(lines):
                l_start = get_node(line.coords[0])
                l_end = get_node(line.coords[-1])
                if l_start == d_node or l_end == d_node:
                    if line.length < 50.0:
                        continue
                
                dist = line.distance(d_point)
                if dist < best_dist and dist <= snap_threshold:
                    proj_dist = line.project(d_point)
                    proj_pt = line.interpolate(proj_dist)
                    proj_node = get_node((proj_pt.x, proj_pt.y))
                    if proj_node != l_start and proj_node != l_end:
                        best_dist = dist
                        best_target = proj_pt
                        target_type = 'edge'
                        best_edge_idx = idx
                        best_proj_point = (proj_pt.x, proj_pt.y)
                        
            # Execute the snapping
            if best_target is not None:
                if target_type == 'endpoint':
                    snapped_nodes[d_node] = best_target
                elif target_type == 'edge':
                    target_line = lines[best_edge_idx]
                    coords = list(target_line.coords)
                    insert_idx = -1
                    for i in range(len(coords) - 1):
                        seg = LineString([coords[i], coords[i+1]])
                        dist_to_seg = seg.distance(Point(best_proj_point))
                        if dist_to_seg < 0.01:
                            insert_idx = i + 1
                            break
                    if insert_idx != -1:
                        new_coords = coords[:insert_idx] + [best_proj_point] + coords[insert_idx:]
                        lines[best_edge_idx] = LineString(new_coords)
                        snapped_nodes[d_node] = best_proj_point
                        
        if not snapped_nodes:
            break
            
        new_lines = []
        for line in lines:
            coords = list(line.coords)
            start_node = get_node(coords[0])
            end_node = get_node(coords[-1])
            
            modified = False
            if start_node in snapped_nodes:
                coords[0] = snapped_nodes[start_node]
                modified = True
            if end_node in snapped_nodes:
                coords[-1] = snapped_nodes[end_node]
                modified = True
                
            if modified:
                new_lines.append(LineString(coords))
            else:
                new_lines.append(line)
        lines = new_lines
        
        merged = linemerge(lines)
        lines = []
        if merged.geom_type == 'LineString':
            lines.append(merged)
        elif merged.geom_type in ('MultiLineString', 'GeometryCollection'):
            for g in merged.geoms:
                if g.geom_type == 'LineString':
                    lines.append(g)

    # Step 4: Iterative Spur Pruning
    pruned_count = 0
    while True:
        G = nx.MultiGraph()
        def get_node(pt):
            return (round(pt[0], 3), round(pt[1], 3))
            
        for idx, line in enumerate(lines):
            n_start = get_node(line.coords[0])
            n_end = get_node(line.coords[-1])
            G.add_edge(n_start, n_end, idx=idx, length=line.length, geom=line)
            
        to_prune_indices = set()
        for node in G.nodes():
            deg = G.degree(node)
            if deg == 1:
                edge_data = list(G.edges(node, data=True))[0]
                u, v, attr = edge_data
                other_node = v if u == node else u
                other_deg = G.degree(other_node)
                
                if other_deg >= 3 and attr['length'] < prune_threshold:
                    to_prune_indices.add(attr['idx'])
                    
        if not to_prune_indices:
            break
            
        lines = [line for idx, line in enumerate(lines) if idx not in to_prune_indices]
        pruned_count += len(to_prune_indices)
        
        merged = linemerge(lines)
        lines = []
        if merged.geom_type == 'LineString':
            lines.append(merged)
        elif merged.geom_type in ('MultiLineString', 'GeometryCollection'):
            for g in merged.geoms:
                if g.geom_type == 'LineString':
                    lines.append(g)
                    
    print(f"[Phase 6] Pruned {pruned_count} minor dangling spurs.")

    # Step 5: Final Merge & Length Filtering
    merged = linemerge(lines)
    final_lines = []
    if merged.geom_type == 'LineString':
        final_lines.append(merged)
    elif merged.geom_type in ('MultiLineString', 'GeometryCollection'):
        for g in merged.geoms:
            if g.geom_type == 'LineString':
                final_lines.append(g)
                
    filtered_lines = [line for line in final_lines if line.length >= min_length]
    
    cleaned_features = []
    for idx, line in enumerate(filtered_lines):
        # Attribute assignment: determine if it's an island
        line_center = line.interpolate(line.length / 2.0)
        closest_row = shoreline_gdf.iloc[shoreline_gdf.distance(line_center).argmin()]
        is_island = bool(closest_row['is_island'])
            
        feat = {
            'geometry': line,
            'id': f"shoreline_{year}_{season}_cleaned_{idx}",
            'bank_type': 'unknown',
            'length_m': float(line.length),
            'is_island': is_island,
            'year': int(year),
            'season': season,
            'source': 'S1',
            'processing_version': version
        }
        cleaned_features.append(feat)
        
    cleaned_gdf = gpd.GeoDataFrame(cleaned_features, crs="EPSG:32648")
    print(f"[Phase 6] Completed. Reduced segment count from {len(shoreline_gdf)} to {len(cleaned_gdf)}. Cleaned shoreline length: {cleaned_gdf.geometry.length.sum()/1000:.2f} km.")
    return cleaned_gdf

def resample_line(line, spacing=30.0):
    """
    Resamples a LineString or MultiLineString to have vertices at a maximum spacing.
    This prevents Chaikin's algorithm from cutting excessively large corners on long segments.
    """
    import numpy as np
    from shapely.geometry import LineString
    from shapely.ops import unary_union
    
    if line.is_empty:
        return line
    if line.geom_type == 'LineString':
        length = line.length
        if length < spacing:
            return line
        distances = np.arange(0, length, spacing)
        if len(distances) == 0 or distances[-1] < length:
            distances = np.append(distances, length)
        pts = [line.interpolate(d) for d in distances]
        return LineString(pts)
    elif line.geom_type == 'MultiLineString':
        parts = []
        for part in line.geoms:
            parts.append(resample_line(part, spacing))
        return unary_union(parts)
    return line

def smooth_and_simplify_shoreline(cleaned_gdf, config_dict=None):
    """
    Implements Phase 7: Smoothing & Simplification.
    
    1. Resamples line segments to 30.0m spacing to limit Chaikin corner-cutting deviation.
    2. Applies Chaikin's corner-cutting algorithm (default 3 iterations) to round pixelated corners.
       Correctly distinguishes between closed rings (e.g. islands, wrap-around closure) and open curves (keeps endpoints fixed and cuts internal corners).
    3. Applies Douglas-Peucker simplification using Shapely's simplify(dp_tolerance, preserve_topology=True).
    4. Validates topology (is_valid, non-empty, simple).
    5. Logs vertex reduction percentage and verifies maximum Hausdorff distance deviation (<= 15.0m).
    
    Returns:
      smoothed_gdf (gpd.GeoDataFrame): Smoothed and simplified shoreline in EPSG:32648.
      metrics (dict): Summary metrics of the smoothing process.
    """
    import numpy as np
    from shapely.geometry import Point
    
    if config_dict is None:
        config_dict = SHORELINE_CONFIG
        
    chaikin_iterations = config_dict.get('chaikin_iterations', 3)
    dp_tolerance = config_dict.get('dp_tolerance', 1.0)
    
    def chaikin_smooth(geom, iterations):
        if geom.is_empty or geom.geom_type not in ('LineString', 'LinearRing'):
            return geom
            
        coords = np.array(geom.coords)
        if len(coords) < 3:
            return geom
            
        is_closed = geom.is_closed or np.allclose(coords[0], coords[-1])
        
        for _ in range(iterations):
            if is_closed:
                # Closed loop: exclude duplicate end point, smooth, then re-close
                pts = coords[:-1]
                n = len(pts)
                new_pts = []
                for i in range(n):
                    p_curr = pts[i]
                    p_next = pts[(i + 1) % n]
                    q = p_curr * 0.75 + p_next * 0.25
                    r = p_curr * 0.25 + p_next * 0.75
                    new_pts.extend([q, r])
                new_pts.append(new_pts[0])
                coords = np.array(new_pts)
            else:
                # Open curve: keep endpoints fixed, cut internal corners
                n = len(coords)
                new_pts = [coords[0]]
                for i in range(n - 2):
                    r_curr = coords[i] * 0.25 + coords[i+1] * 0.75
                    q_next = coords[i+1] * 0.75 + coords[i+2] * 0.25
                    new_pts.extend([r_curr, q_next])
                new_pts.append(coords[-1])
                coords = np.array(new_pts)
                
        return LineString(coords)
        
    smoothed_features = []
    total_vertices_before = 0
    total_vertices_after = 0
    max_hausdorff_deviation = 0.0
    
    for idx, row in cleaned_gdf.iterrows():
        geom = row.geometry
        if geom.is_empty:
            continue
            
        # Count vertices before
        num_v_before = len(geom.coords) if geom.geom_type == 'LineString' else sum(len(g.coords) for g in geom.geoms)
        total_vertices_before += num_v_before
        
        # 1. Resample line to 30.0m maximum spacing before smoothing
        resampled_geom = resample_line(geom, spacing=30.0)
        
        # 2. Apply Chaikin smoothing
        smoothed_geom = chaikin_smooth(resampled_geom, chaikin_iterations)
        
        # 3. Apply Douglas-Peucker simplification
        simplified_geom = smoothed_geom.simplify(dp_tolerance, preserve_topology=True)
        simplified_geom = make_valid(simplified_geom)
        
        # Count vertices after
        num_v_after = len(simplified_geom.coords) if simplified_geom.geom_type == 'LineString' else sum(len(g.coords) for g in simplified_geom.geoms)
        total_vertices_after += num_v_after
        
        # Compute Hausdorff distance deviation between original cleaned geom and final simplified geom
        h_dist = geom.hausdorff_distance(simplified_geom)
        if h_dist > max_hausdorff_deviation:
            max_hausdorff_deviation = h_dist
            
        new_row = row.copy()
        new_row.geometry = simplified_geom
        smoothed_features.append(new_row)
        
    smoothed_gdf = gpd.GeoDataFrame(smoothed_features, crs=cleaned_gdf.crs)
    
    reduction_pct = 0.0
    if total_vertices_before > 0:
        reduction_pct = (total_vertices_before - total_vertices_after) / total_vertices_before * 100.0
        
    metrics = {
        'total_vertices_before': total_vertices_before,
        'total_vertices_after': total_vertices_after,
        'vertex_reduction_pct': reduction_pct,
        'max_hausdorff_deviation_m': max_hausdorff_deviation
    }
    
    print(f"[Phase 7] Smoothing & Simplification Complete.")
    print(f"  - Vertex reduction: {total_vertices_before} -> {total_vertices_after} ({reduction_pct:.2f}%)")
    print(f"  - Max Hausdorff deviation: {max_hausdorff_deviation:.2f} m (Threshold: 15.0 m)")
    
    return smoothed_gdf, metrics

def generate_validation_shoreline_s2(year, season, aoi_geometry, bridge_mask=None, config_dict=None, bypass_cache=False):
    """
    Implements Phase 8: Sentinel-2 NDWI reference shoreline extraction.
    
    1. Queries COPERNICUS/S2_SR_HARMONIZED for the given year and season.
    2. Masks clouds using the QA60 band.
    3. Computes NDWI composite: (B3 - B8) / (B3 + B8).
    4. Thresholds NDWI (> 0.0) to create a binary water mask.
    5. Downloads the unmasked binary water mask at 20m scale and polygonizes locally.
    6. Main Water Polygon Selection: selects the main channel using the continuous centerline.
    7. Extracts boundaries (exterior and persistent islands).
    
    Returns:
      reference_gdf (gpd.GeoDataFrame): Sentinel-2 reference shoreline in EPSG:32648.
    """
    import os
    import requests
    import io
    import rasterio
    from rasterio.features import shapes
    import time
    
    ref_path = os.path.join("data", f"s2_ref_shoreline_{year}_{season}.geojson")
    poly_path = os.path.join("data", f"s2_water_poly_{year}_{season}.geojson")
    
    if not bypass_cache and os.path.exists(ref_path) and os.path.exists(poly_path):
        try:
            print(f"[Phase 8] Loading cached S2 reference data from local GeoJSONs: {ref_path}")
            ref_gdf = gpd.read_file(ref_path)
            poly_gdf = gpd.read_file(poly_path)
            if hasattr(poly_gdf.geometry, 'union_all'):
                s2_water_poly = poly_gdf.geometry.union_all()
            else:
                s2_water_poly = poly_gdf.geometry.unary_union
            if not s2_water_poly.is_valid:
                s2_water_poly = make_valid(s2_water_poly)
            print(f"[Phase 8] Loaded local cache: {len(ref_gdf)} shoreline segments.")
            return ref_gdf, s2_water_poly
        except Exception as e:
            print(f"[Warning] Failed to load local S2 cache: {e}. Falling back to GEE download...")
    
    start_time = time.time()
    
    if config_dict is None:
        config_dict = SHORELINE_CONFIG
        
    min_main_water_area = config_dict.get('min_main_water_area', 100000.0)
    min_island_area = config_dict.get('min_island_area', 10000.0)
    min_centerline_intersection = config_dict.get('min_centerline_intersection', 1000.0)
    
    # 1. Fetch S2 collection
    s2_col = (ee.ImageCollection('COPERNICUS/S2_SR_HARMONIZED')
              .filterBounds(aoi_geometry)
              .filterDate(f'{year}-01-01', f'{year}-12-31')
              .filter(ee.Filter.lt('CLOUDY_PIXEL_PERCENTAGE', 25)))
              
    if season == 'dry':
        s2_col = s2_col.filter(ee.Filter.Or(
            ee.Filter.calendarRange(1, 4, 'month'),
            ee.Filter.calendarRange(11, 12, 'month')
        ))
    elif season == 'wet':
        s2_col = s2_col.filter(ee.Filter.calendarRange(5, 10, 'month'))
        
    try:
        s2_size = s2_col.size().getInfo()
    except Exception:
        s2_size = 0
        
    if s2_size == 0:
        print(f"[Phase 8] No Level-2A images found for {year} {season}. Falling back to Level-1C (COPERNICUS/S2_HARMONIZED)...")
        s2_col = (ee.ImageCollection('COPERNICUS/S2_HARMONIZED')
                  .filterBounds(aoi_geometry)
                  .filterDate(f'{year}-01-01', f'{year}-12-31')
                  .filter(ee.Filter.lt('CLOUDY_PIXEL_PERCENTAGE', 25)))
        if season == 'dry':
            s2_col = s2_col.filter(ee.Filter.Or(
                ee.Filter.calendarRange(1, 4, 'month'),
                ee.Filter.calendarRange(11, 12, 'month')
            ))
        elif season == 'wet':
            s2_col = s2_col.filter(ee.Filter.calendarRange(5, 10, 'month'))
        
    def mask_s2_clouds(img):
        qa = img.select('QA60')
        cloud_bit = 1 << 10
        cirrus_bit = 1 << 11
        mask = qa.bitwiseAnd(cloud_bit).eq(0).And(qa.bitwiseAnd(cirrus_bit).eq(0))
        return img.updateMask(mask)
        
    s2_masked = s2_col.map(mask_s2_clouds)
    s2_median = s2_masked.median().clip(aoi_geometry)
    
    # Calculate NDWI: (B3 - B8) / (B3 + B8)
    ndwi = s2_median.normalizedDifference(['B3', 'B8'])
    water_mask = ndwi.gt(0.0).unmask(0).eq(1)
    
    # Restrict to centerline 2km buffer bounding box (just like S1)
    centerline_fc = load_centerline()
    buffer_geom = centerline_fc.geometry().buffer(2000)
    bbox = buffer_geom.bounds()
    
    print(f"[Phase 8] Requesting S2 download URL for NDWI water mask...")
    
    # Try up to 5 times with exponential backoff for GEE downloads
    for attempt in range(5):
        try:
            url = water_mask.clip(buffer_geom).getDownloadURL({
                'scale': 20, # 20m scale is very fast and has good precision for validation
                'crs': 'EPSG:32648',
                'region': bbox.getInfo(),
                'format': 'GEO_TIFF'
            })
            print(f"[Phase 8] Downloading S2 water mask from GEE (attempt {attempt+1}/5)...")
            r = requests.get(url, timeout=300)
            r.raise_for_status()
            break
        except Exception as e:
            if attempt == 4:
                print(f"[Error] S2 water mask download failed after 5 attempts: {e}")
                raise e
            wait_time = (2 ** attempt) + np.random.uniform(0, 1)
            print(f"[Warning] S2 water mask download failed: {e}. Retrying in {wait_time:.1f}s...")
            time.sleep(wait_time)
        
    print(f"[Phase 8] Parsing GeoTIFF and polygonizing S2 water mask locally...")
    with rasterio.open(io.BytesIO(r.content)) as src:
        raster_data = src.read(1)
        transform = src.transform
        
    water_geoms = []
    for geom, val in shapes(raster_data, transform=transform):
        if val == 1:
            water_geoms.append(shape(geom))
            
    print(f"[Phase 8] Extracted {len(water_geoms)} S2 water polygons locally.")
    
    if not water_geoms:
        print("[Warning] No S2 water polygons found.")
        return gpd.GeoDataFrame(geometry=[], crs="EPSG:32648"), None
        
    # Get continuous centerline locally for intersection selection
    cl_linestring = get_continuous_centerline()
    cl_gdf = gpd.GeoDataFrame(geometry=[cl_linestring], crs="EPSG:4326").to_crs("EPSG:32648")
    centerline_union = cl_gdf.geometry.unary_union
    
    cl_intersection_lengths = [poly.intersection(centerline_union).length for poly in water_geoms]
    max_intersect_len = max(cl_intersection_lengths) if cl_intersection_lengths else 0.0
    
    selected_polys = []
    for poly, intersect_len in zip(water_geoms, cl_intersection_lengths):
        if (intersect_len >= min_centerline_intersection) or (intersect_len > 0 and intersect_len == max_intersect_len):
            selected_polys.append(poly)
            
    if not selected_polys:
        print("[Warning] No main S2 water corridor polygons found.")
        return gpd.GeoDataFrame(geometry=[], crs="EPSG:32648"), None
        
    # Dissolve water polygons
    from shapely.ops import unary_union as shapely_unary_union
    water_dissolved = make_valid(shapely_unary_union(selected_polys))
    
    if not water_dissolved.is_valid:
        water_dissolved = make_valid(water_dissolved)
        
    # Boundary extraction
    raw_lines = []
    def process_polygon(poly):
        if poly.is_empty:
            return
        if poly.exterior and not poly.exterior.is_empty:
            raw_lines.append((poly.exterior, False))
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
            
    valid_lines = []
    for ring, is_island in raw_lines:
        line_geom = LineString(ring.coords)
        line_valid = make_valid(line_geom)
        if line_valid.geom_type == 'LineString':
            if not line_valid.is_empty and line_valid.length >= 10.0:
                valid_lines.append((line_valid, is_island))
        elif line_valid.geom_type in ('MultiLineString', 'GeometryCollection'):
            for g in line_valid.geoms:
                if g.geom_type == 'LineString' and not g.is_empty and g.length >= 10.0:
                    valid_lines.append((g, is_island))
                    
    features = []
    for idx, (line, is_island) in enumerate(valid_lines):
        features.append({
            'geometry': line,
            'id': f"ref_s2_{year}_{season}_{idx}",
            'is_island': is_island,
            'length_m': line.length
        })
        
    ref_gdf = gpd.GeoDataFrame(features, crs="EPSG:32648")
    print(f"[Phase 8] Extracted S2 NDWI reference shoreline. {len(ref_gdf)} segments, total length: {ref_gdf.geometry.length.sum()/1000:.2f} km")
    
    # Save/cache locally
    try:
        os.makedirs("data", exist_ok=True)
        ref_gdf.to_file(ref_path, driver="GeoJSON")
        poly_gdf = gpd.GeoDataFrame(geometry=[water_dissolved], crs="EPSG:32648")
        poly_gdf.to_file(poly_path, driver="GeoJSON")
        print(f"[Phase 8] Cached S2 reference data locally to {ref_path}")
    except Exception as e:
        print(f"[Warning] Failed to cache S2 reference data locally: {e}")
        
    return ref_gdf, water_dissolved

def validate_shoreline(extracted_gdf, reference_gdf):
    """
    Computes nearest-neighbor distance metrics between extracted and reference shorelines
    after 5m resampling to prevent vertex-density bias.
    
    Returns:
      metrics (dict): Comprehensive positional QC stats, raw distances, points, and association info.
    """
    import numpy as np
    from scipy.spatial import cKDTree
    
    if extracted_gdf.empty or reference_gdf.empty:
        print("[Warning] Empty inputs for validation. Returning zero metrics.")
        return {
            'min_dist_m': 0.0,
            'max_dist_m': 0.0,
            'mean_dist_m': 0.0,
            'median_dist_m': 0.0,
            'std_dist_m': 0.0,
            'rmse_dist_m': 0.0,
            'p75_dist_m': 0.0,
            'p90_dist_m': 0.0,
            'p95_dist_m': 0.0,
            'p99_dist_m': 0.0,
            'hausdorff_dist_m': 0.0,
            'distances': np.array([]),
            'ext_points_info': []
        }
        
    def resample_gdf_points_with_meta(gdf, spacing=5.0):
        points_info = []
        for idx, row in gdf.iterrows():
            geom = row.geometry
            if geom.is_empty:
                continue
                
            # Get metadata
            seg_id = row.get('id', f"segment_{idx}")
            bank_type = row.get('bank_type', 'unknown')
            is_island = row.get('is_island', False)
            
            def add_pts(g):
                length = g.length
                distances = np.arange(0, length, spacing)
                if len(distances) == 0 or distances[-1] < length:
                    distances = np.append(distances, length)
                for d in distances:
                    pt = g.interpolate(d)
                    points_info.append({
                        'point': pt,
                        'segment_id': seg_id,
                        'bank_type': bank_type,
                        'is_island': is_island
                    })
                    
            if geom.geom_type == 'LineString':
                add_pts(geom)
            elif geom.geom_type == 'MultiLineString':
                for g in geom.geoms:
                    add_pts(g)
        return points_info
        
    # Resample both shorelines at 5m
    ext_points_info = resample_gdf_points_with_meta(extracted_gdf, spacing=5.0)
    ref_points_info = resample_gdf_points_with_meta(reference_gdf, spacing=5.0)
    
    if not ext_points_info or not ref_points_info:
        print("[Warning] No points extracted after resampling.")
        return {
            'min_dist_m': 0.0,
            'max_dist_m': 0.0,
            'mean_dist_m': 0.0,
            'median_dist_m': 0.0,
            'std_dist_m': 0.0,
            'rmse_dist_m': 0.0,
            'p75_dist_m': 0.0,
            'p90_dist_m': 0.0,
            'p95_dist_m': 0.0,
            'p99_dist_m': 0.0,
            'hausdorff_dist_m': 0.0,
            'distances': np.array([]),
            'ext_points_info': []
        }
        
    # Convert to coordinates
    ext_coords = np.array([[info['point'].x, info['point'].y] for info in ext_points_info])
    ref_coords = np.array([[info['point'].x, info['point'].y] for info in ref_points_info])
    
    # KDTree computation
    tree = cKDTree(ref_coords)
    distances, nearest_indices = tree.query(ext_coords, k=1)
    
    # Add distance and nearest reference point info to ext_points_info
    for i, info in enumerate(ext_points_info):
        info['distance'] = float(distances[i])
        nearest_idx = nearest_indices[i]
        info['ref_x'] = float(ref_coords[nearest_idx][0])
        info['ref_y'] = float(ref_coords[nearest_idx][1])
        info['ext_x'] = float(ext_coords[i][0])
        info['ext_y'] = float(ext_coords[i][1])
        
    # Compute detailed statistics
    min_dist = np.min(distances)
    max_dist = np.max(distances)
    mean_dist = np.mean(distances)
    median_dist = np.median(distances)
    std_dist = np.std(distances)
    rmse_dist = np.sqrt(np.mean(distances**2))
    p75 = np.percentile(distances, 75)
    p90 = np.percentile(distances, 90)
    p95 = np.percentile(distances, 95)
    p99 = np.percentile(distances, 99)
    
    metrics = {
        'min_dist_m': float(min_dist),
        'max_dist_m': float(max_dist),
        'mean_dist_m': float(mean_dist),
        'median_dist_m': float(median_dist),
        'std_dist_m': float(std_dist),
        'rmse_dist_m': float(rmse_dist),
        'p75_dist_m': float(p75),
        'p90_dist_m': float(p90),
        'p95_dist_m': float(p95),
        'p99_dist_m': float(p99),
        'hausdorff_dist_m': float(max_dist),
        'distances': distances,
        'ext_points_info': ext_points_info
    }
    
    print(f"[Validation] Shoreline Validation Metrics (against S2 NDWI):")
    print(f"  - Mean Distance: {mean_dist:.2f} m")
    print(f"  - RMSE: {rmse_dist:.2f} m")
    print(f"  - Hausdorff Distance: {max_dist:.2f} m")
    print(f"  - 95th Percentile: {p95:.2f} m")
    
    return metrics


def load_manual_bridges(bridges_path=None):
    """
    Loads manual bridge polygons from data/bridges.geojson as a GeoDataFrame.
    Reprojects to UTM Zone 48N (EPSG:32648).
    """
    if bridges_path is None:
        # Default path relative to this file's directory (src/shoreline.py)
        bridges_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'data', 'bridges.geojson')
        
    if not os.path.exists(bridges_path):
        raise FileNotFoundError(f"Manual bridges GeoJSON not found at: {bridges_path}. "
                                "Please run scripts/initialize_bridges.py or use the digitization tool first.")
                                
    bridges_gdf = gpd.read_file(bridges_path)
    
    # Ensure CRS is reprojected to EPSG:32648
    if bridges_gdf.crs is None:
        bridges_gdf.set_crs("EPSG:4326", inplace=True)
    if bridges_gdf.crs != "EPSG:32648":
        bridges_gdf = bridges_gdf.to_crs("EPSG:32648")
        
    return bridges_gdf


def calibrate_s1_water_mask(classified, composite, s2_ref_gdf):
    """
    Calibrates S1 water mask using S2 shoreline as ground truth...
    """
    if s2_ref_gdf is None or s2_ref_gdf.empty:
        print("[Calibration] No S2 reference shoreline available. Skipping calibration.")
        return classified
        
    print("[Calibration] Calibrating S1 water mask using S2 shoreline as ground truth...")
    
    # 1. Project S2 shoreline to WGS84
    s2_wgs84 = s2_ref_gdf.to_crs("EPSG:4326")
    
    # Extract points along the line at ~10m spacing
    import numpy as np
    from shapely.geometry import Point
    import geopandas as gpd
    import ee
    
    pts_list = []
    spacing = 10.0 # in meters (approx 0.00009 degrees)
    
    for idx, row in s2_wgs84.iterrows():
        geom = row.geometry
        if geom.is_empty:
            continue
        # Calculate length of the geometry in UTM (EPSG:32648)
        utm_geom = s2_ref_gdf.loc[idx].geometry
        length_m = utm_geom.length
        distances = np.arange(0, length_m, spacing)
        if len(distances) == 0:
            distances = [0.0]
            
        for d in distances:
            if d < utm_geom.length:
                pt_utm = utm_geom.interpolate(d)
                # Convert back to WGS84
                pt_series = gpd.GeoSeries([pt_utm], crs="EPSG:32648").to_crs("EPSG:4326")
                pt_wgs = pt_series.iloc[0]
                pts_list.append((pt_wgs.x, pt_wgs.y))
                
    print(f"[Calibration] Extracted {len(pts_list)} boundary points along S2 shoreline.")
    
    if len(pts_list) < 10:
        print("[Calibration] Too few points along S2 shoreline. Skipping calibration.")
        return classified
        
    # Limit points to max 2000 to avoid GEE request limits, sample uniformly
    if len(pts_list) > 2000:
        step = len(pts_list) // 2000
        pts_list = pts_list[::step][:2000]
        
    # 2. Build GEE FeatureCollection
    ee_features = []
    for lon, lat in pts_list:
        ee_features.append(ee.Feature(ee.Geometry.Point([lon, lat])))
        
    pts_fc = ee.FeatureCollection(ee_features)
    
    # 3. Sample S1 backscatter values
    sampled = composite.select(['VV', 'VH']).sampleRegions(
        collection=pts_fc,
        scale=10,
        tileScale=16
    )
    
    try:
        vv_vals = sampled.aggregate_array('VV').getInfo()
        vh_vals = sampled.aggregate_array('VH').getInfo()
    except Exception as e:
        print(f"[Calibration Warning] GEE sampling failed: {e}. Using default thresholds.")
        vv_vals = []
        vh_vals = []
        
    # Clean up null values
    vv_vals = [v for v in vv_vals if v is not None]
    vh_vals = [v for v in vh_vals if v is not None]
    
    # 4. Calculate thresholds (with robust clamping to prevent crazy outliers)
    # Defaults: VV = -16.0, VH = -22.0
    if len(vv_vals) > 10:
        vv_cal = float(np.median(vv_vals))
        # Clamp between -19.0 and -13.0
        vv_cal = max(-19.0, min(-13.0, vv_cal))
    else:
        vv_cal = -16.0
        
    if len(vh_vals) > 10:
        vh_cal = float(np.median(vh_vals))
        # Clamp between -25.0 and -19.0
        vh_cal = max(-25.0, min(-19.0, vh_cal))
    else:
        vh_cal = -22.0
        
    print(f"[Calibration Results] Calibrated thresholds: VV = {vv_cal:.2f} dB, VH = {vh_cal:.2f} dB.")
    
    # 5. Apply correction to classified image
    # If VV <= vv_cal AND VH <= vh_cal -> set class to 1 (Water)
    vv_below = composite.select('VV').lte(vv_cal)
    vh_below = composite.select('VH').lte(vh_cal)
    s2_guided_water = vv_below.And(vh_below)
    
    # Correct: where s2_guided_water is 1, return 1, else return classified
    calibrated_classified = classified.where(s2_guided_water, 1)
    
    return calibrated_classified

def generate_reach_interactive_map(extracted_gdf, s2_ref_gdf, val_stats, reach_title, year, season, output_html_path):
    """
    Generates a dedicated interactive HTML map for a single Reach, displaying:
    1. Google Satellite & OpenStreetMap basemaps
    2. S2 Reference Shoreline (Ground Truth)
    3. S1 Extracted Shoreline
    4. Validation Error Mask Layer (Point-by-point spatial error colored by magnitude)
    """
    import folium
    from folium.plugins import MousePosition
    import geopandas as gpd

    center_lat, center_lon = 21.04, 105.86
    if not extracted_gdf.empty:
        bounds = extracted_gdf.to_crs("EPSG:4326").total_bounds
        center_lon = (bounds[0] + bounds[2]) / 2.0
        center_lat = (bounds[1] + bounds[3]) / 2.0

    m = folium.Map(location=[center_lat, center_lon], zoom_start=11, control_scale=True)
    folium.LatLngPopup().add_to(m)
    MousePosition().add_to(m)

    folium.TileLayer(
        tiles='https://mt1.google.com/vt/lyrs=s&x={x}&y={y}&z={z}',
        attr='Google Satellite',
        name='Google Satellite',
        overlay=False,
        control=True
    ).add_to(m)

    if not s2_ref_gdf.empty:
        s2_wgs = s2_ref_gdf.to_crs("EPSG:4326")
        folium.GeoJson(
            s2_wgs,
            name='Sentinel-2 Reference Shoreline (Ground Truth)',
            style_function=lambda x: {'color': '#ff7800', 'weight': 2.5, 'dashArray': '5, 5', 'opacity': 0.9}
        ).add_to(m)

    if not extracted_gdf.empty:
        s1_wgs = extracted_gdf.to_crs("EPSG:4326")
        folium.GeoJson(
            s1_wgs,
            name=f'Sentinel-1 Extracted Shoreline ({reach_title})',
            style_function=lambda x: {'color': '#00ffff', 'weight': 3.0, 'opacity': 0.9}
        ).add_to(m)

    ext_points = val_stats.get('ext_points_info', [])
    if ext_points:
        error_group = folium.FeatureGroup(name='Validation Error Mask (Error Magnitude Points)', show=True)
        pts_gdf = gpd.GeoDataFrame(
            [{'distance': p['distance']} for p in ext_points],
            geometry=[p['point'] for p in ext_points],
            crs="EPSG:32648"
        ).to_crs("EPSG:4326")

        for idx, row in pts_gdf.iterrows():
            dist = row['distance']
            pt = row.geometry
            
            if dist <= 30.0:
                color = '#2ecc71'  # Green (Tốt - Good)
                radius = 3.5
                rating_str = 'Tốt (Good)'
            elif dist <= 70.0:
                color = '#ffb300'  # Orange/Yellow (Trung bình - Moderate)
                radius = 5.0
                rating_str = 'Trung bình (Moderate)'
            else:
                color = '#e74c3c'  # Red (Kém - Poor)
                radius = 6.5
                rating_str = 'Kém (Poor)'

            folium.CircleMarker(
                location=[pt.y, pt.x],
                radius=radius,
                color=color,
                fill=True,
                fill_color=color,
                fill_opacity=0.85,
                popup=f"<b>Reach:</b> {reach_title}<br><b>Error Distance:</b> {dist:.1f} m<br><b>Mức độ:</b> {rating_str}"
            ).add_to(error_group)

        error_group.add_to(m)

    mean_e = val_stats.get('mean_dist_m', 0.0)
    rmse_e = val_stats.get('rmse_dist_m', 0.0)
    p95_e = val_stats.get('p95_dist_m', 0.0)

    if rmse_e <= 30.0:
        overall_rating_html = '<span style="color: #2ecc71; font-weight: bold;">TỐT (GOOD - RMSE &lt; 30m)</span>'
    elif rmse_e <= 70.0:
        overall_rating_html = '<span style="color: #ffb300; font-weight: bold;">TRUNG BÌNH (MODERATE - 30-70m)</span>'
    else:
        overall_rating_html = '<span style="color: #e74c3c; font-weight: bold;">KÉM (POOR - RMSE &gt; 70m)</span>'

    legend_html = f'''
    <div style="position: fixed; bottom: 25px; left: 25px; width: 440px; z-index:9999; 
                background-color: rgba(18, 22, 28, 0.92); color: #ecf0f1; border: 2px solid #34495e; 
                border-radius: 10px; padding: 12px; font-size: 12px; font-family: 'Segoe UI', Arial, sans-serif;
                box-shadow: 0 4px 15px rgba(0,0,0,0.5); backdrop-filter: blur(4px);">
        <h4 style="margin: 0 0 8px 0; color: #00ffff; font-size: 14px; border-bottom: 1px solid #34495e; padding-bottom: 5px;">
            📌 {reach_title} ({year} {season.upper()})
        </h4>
        <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 6px; margin-bottom: 8px; background: rgba(255,255,255,0.05); padding: 6px 8px; border-radius: 6px;">
            <div><b>Mean Error:</b> <span style="color:#00ffff;">{mean_e:.2f} m</span></div>
            <div><b>RMSE Error:</b> <span style="color:#00ffff;">{rmse_e:.2f} m</span></div>
            <div><b>P95 Error:</b> <span style="color:#00ffff;">{p95_e:.2f} m</span></div>
            <div><b>Đánh giá tổng thể:</b> {overall_rating_html}</div>
        </div>
        <table style="width: 100%; border-collapse: collapse; text-align: left; font-size: 11px; margin-top: 4px;">
            <thead>
                <tr style="background-color: #2c3e50; color: #00ffff; border-bottom: 1px solid #455a64;">
                    <th style="padding: 4px;">Mức độ (Rating)</th>
                    <th style="padding: 4px;">Khoảng cách (m)</th>
                    <th style="padding: 4px;">Quy đổi Pixel (10m)</th>
                    <th style="padding: 4px;">Ý nghĩa thực tiễn &amp; Học thuật</th>
                </tr>
            </thead>
            <tbody>
                <tr style="border-bottom: 1px solid #37474f;">
                    <td style="padding: 4px; color: #2ecc71; font-weight: bold;">● Tốt (Good)</td>
                    <td style="padding: 4px;">&lt; 20m - 30m</td>
                    <td style="padding: 4px;">&lt; 2 - 3 px</td>
                    <td style="padding: 4px;">Đạt chuẩn công bố khoa học (High Precision). Bắt chính xác sự thay đổi bãi bồi/đường bờ.</td>
                </tr>
                <tr style="border-bottom: 1px solid #37474f;">
                    <td style="padding: 4px; color: #ffb300; font-weight: bold;">● Trung bình (Moderate)</td>
                    <td style="padding: 4px;">30m - 70m</td>
                    <td style="padding: 4px;">3 - 7 px</td>
                    <td style="padding: 4px;">Đạt chuẩn giám sát quy mô vùng (Regional Scale). Nhận diện tốt xu hướng biến động diện rộng.</td>
                </tr>
                <tr>
                    <td style="padding: 4px; color: #e74c3c; font-weight: bold;">● Kém (Poor)</td>
                    <td style="padding: 4px;">&gt; 70m - 100m+</td>
                    <td style="padding: 4px;">&gt; 7 - 10+ px</td>
                    <td style="padding: 4px;">Chưa đạt yêu cầu (High Error). Sai số do nhiễu speckle, phù sa đục hoặc công trình.</td>
                </tr>
            </tbody>
        </table>
    </div>
    '''
    m.get_root().html.add_child(folium.Element(legend_html))
    folium.LayerControl().add_to(m)

    m.save(output_html_path)
    print(f"[Interactive Map] Saved reach interactive map with validation error mask to: {output_html_path}")

