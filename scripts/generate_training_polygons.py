import sys
import json
import os
import math
import ee

sys.path.insert(0, os.getcwd())

def get_rotated_rectangle_vertices(lon, lat, length_m, width_m, angle_deg):
    """
    Generates coordinates of a rotated rectangle in degrees centered at (lon, lat).
    """
    lat_rad = math.radians(21.04)
    deg_lat_m = 111132.0
    deg_lon_m = 111132.0 * math.cos(lat_rad)
    
    local_vertices = [
        (-length_m / 2.0, -width_m / 2.0),
        (length_m / 2.0, -width_m / 2.0),
        (length_m / 2.0, width_m / 2.0),
        (-length_m / 2.0, width_m / 2.0)
    ]
    
    angle_rad = math.radians(angle_deg)
    cos_a = math.cos(angle_rad)
    sin_a = math.sin(angle_rad)
    
    coords = []
    for lx, ly in local_vertices:
        rx = lx * cos_a - ly * sin_a
        ry = lx * sin_a + ly * cos_a
        
        d_lon = rx / deg_lon_m
        d_lat = ry / deg_lat_m
        
        coords.append([lon + d_lon, lat + d_lat])
        
    coords.append(coords[0])
    return coords

def generate_polygons_from_sar():
    from src.config import GEE_PROJECT, ASSET_COMPOSITE_TEMPLATE
    from src.aoi import get_aoi_geometry
    
    # Initialize GEE
    try:
        ee.Initialize(project=GEE_PROJECT)
    except Exception:
        ee.Authenticate()
        ee.Initialize(project=GEE_PROJECT)
        
    print("[DATA] Fetching 2024 Dry composite and AOI to find pure pixels...")
    aoi_geometry = get_aoi_geometry()
    
    # Load composite
    composite_path = ASSET_COMPOSITE_TEMPLATE.format(year=2024, season='dry')
    composite = ee.Image(composite_path)
    
    # Generate random candidate points within the AOI
    # We generate 4000 points to ensure we get plenty of valid candidates in each class
    candidate_points = ee.FeatureCollection.randomPoints(aoi_geometry, 4000, seed=42)
    
    # Sample the S1 backscatter values
    sampled = composite.select(['VV', 'VH', 'angle']).sampleRegions(
        collection=candidate_points,
        scale=10,
        geometries=True,
        tileScale=4
    )
    
    print("[DATA] Downloading sampled pixel values from GEE...")
    features = sampled.getInfo().get('features', [])
    print(f"[DATA] Downloaded {len(features)} sampled points.")
    
    # Parse into classes based on strict backscatter criteria
    # Water: low VV (specular reflection)
    # Sandbar: moderate VV, low VH (no volume scattering, dry sand)
    # Others: high VV/VH (urban/vegetation/agriculture)
    water_candidates = []
    sandbar_candidates = []
    others_candidates = []
    
    for f in features:
        props = f.get('properties', {})
        geom = f.get('geometry', {})
        if not geom or geom.get('type') != 'Point':
            continue
            
        lon, lat = geom.get('coordinates')
        vv = props.get('VV')
        vh = props.get('VH')
        angle = props.get('angle')
        
        if vv is None or vh is None:
            continue
            
        # 1. Pure Water signature: VV < -17.5 dB
        if vv < -17.5 and vh < -23.0:
            water_candidates.append({'lon': lon, 'lat': lat, 'vv': vv, 'vh': vh, 'angle': angle})
            
        # 2. Pure Sandbar signature: moderate VV, lower VH
        elif -13.0 < vv < -3.5 and vh < -16.0:
            sandbar_candidates.append({'lon': lon, 'lat': lat, 'vv': vv, 'vh': vh, 'angle': angle})
            
        # 3. Others signature: higher backscatter (urban, dense crops, vegetation)
        elif vv > -13.0 and vh > -15.5:
            others_candidates.append({'lon': lon, 'lat': lat, 'vv': vv, 'vh': vh, 'angle': angle})
            
    print(f"[DATA] Candidates filtered by signature: Water={len(water_candidates)}, Sandbar={len(sandbar_candidates)}, Others={len(others_candidates)}")
    
    # We need to sort and divide these candidates into 5 geographic zones along the river length
    # To do this, we sort all points by longitude (as the Red River flows from Northwest/West 105.35 to Southeast/East 106.00)
    def select_representative_points(candidates, target_count=30):
        if len(candidates) < target_count:
            print(f"[Warning] Not enough candidates for class. Found {len(candidates)}, need {target_count}.")
            return candidates
            
        # Sort by longitude
        candidates_sorted = sorted(candidates, key=lambda x: x['lon'])
        
        # Divide into 5 equal bins
        bin_size = len(candidates_sorted) // 5
        selected = []
        
        for i in range(5):
            bin_data = candidates_sorted[i*bin_size : (i+1)*bin_size]
            # Select 6 points from this bin, spaced out
            # To space them out, we sort the bin by latitude and pick indices
            bin_data_sorted = sorted(bin_data, key=lambda x: x['lat'])
            step = max(1, len(bin_data_sorted) // 6)
            for j in range(6):
                idx = min(j * step, len(bin_data_sorted) - 1)
                selected.append(bin_data_sorted[idx])
                
        # Return exactly the selected ones
        return selected[:target_count]
        
    water_selected = select_representative_points(water_candidates, 30)
    sandbar_selected = select_representative_points(sandbar_candidates, 30)
    others_selected = select_representative_points(others_candidates, 30)
    
    print(f"[DATA] Selected: Water={len(water_selected)}, Sandbar={len(sandbar_selected)}, Others={len(others_selected)}")
    
    # Save the selected points as rotated rectangles matching general flow angles
    # Upstream -> Downstream general orientation angles
    # We can determine the angle based on longitude:
    # West (105.4) to East (105.9)
    def get_flow_angle(lon):
        if lon < 105.55: # Upstream (horizontal flow)
            return 5
        elif lon < 105.70: # Midstream
            return -15
        elif lon < 105.83: # Urban Hanoi (diagonal/vertical)
            return -45
        elif lon < 105.93: # Downstream
            return -65
        else: # Far Downstream (vertical flow)
            return -90

    features = []
    class_names = {0: "Water", 1: "Sandbar", 2: "Others"}
    
    for class_code, points in [(0, water_selected), (1, sandbar_selected), (2, others_selected)]:
        for idx, pt in enumerate(points):
            lon = pt['lon']
            lat = pt['lat']
            angle = get_flow_angle(lon)
            
            # Non-square rectangles (0.7 to 1.2 ha)
            # Water: long and narrow along flow direction
            # Sandbar: elongated shape
            # Others: standard block
            if class_code == 0:
                length_m, width_m = 130, 80
            elif class_code == 1:
                length_m, width_m = 110, 70
            else:
                length_m, width_m = 100, 90
                
            coords = get_rotated_rectangle_vertices(lon, lat, length_m, width_m, angle)
            area_ha = (length_m * width_m) / 10000.0
            
            feat = {
                "type": "Feature",
                "properties": {
                    "class": class_code,
                    "className": class_names[class_code],
                    "id": f"{class_names[class_code].lower()}_{idx+1}",
                    "area_ha": area_ha,
                    "length_m": length_m,
                    "width_m": width_m,
                    "angle_deg": angle,
                    "vv": pt['vv'],
                    "vh": pt['vh']
                },
                "geometry": {
                    "type": "Polygon",
                    "coordinates": [coords]
                }
            }
            features.append(feat)
            
    geojson = {
        "type": "FeatureCollection",
        "features": features
    }
    
    output_path = os.path.join("aoi", "training_polygons.geojson")
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(geojson, f, indent=2)
        
    print(f"[DATA] Successfully wrote {len(features)} data-driven training polygons to {output_path}")

if __name__ == "__main__":
    generate_polygons_from_sar()
