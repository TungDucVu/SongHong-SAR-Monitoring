import sys, os
sys.path.insert(0, os.getcwd())
import json
import requests
import folium
import matplotlib.pyplot as plt
from shapely.geometry import shape, mapping, LineString, MultiLineString, Polygon
from shapely.ops import unary_union, linemerge, polygonize

# Initialize GEE for verification only (not boundary)
import ee
print("1. Initializing GEE for verification...")
ee.Initialize(project='crested-library-500309-i2')

print("2. Fetching Hanoi administrative boundary from OpenStreetMap...")
overpass_url = "https://lz4.overpass-api.de/api/interpreter"

# Query to get Hanoi relation (id 1903516)
hanoi_query = """
[out:json][timeout:90];
relation(1903516);
out geom;
"""

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
    'Accept': 'application/json, text/javascript, */*; q=0.01',
    'Origin': 'https://overpass-turbo.eu',
    'Referer': 'https://overpass-turbo.eu/',
}

try:
    response = requests.post(overpass_url, data={'data': hanoi_query}, headers=headers, timeout=30)
    if response.status_code != 200:
        # Try fallback
        print("LZ4 failed, trying backup endpoint for Hanoi boundary...")
        response = requests.post("https://overpass.osm.ch/api/interpreter", data={'data': hanoi_query}, headers=headers, timeout=30)
    data = response.json()
except Exception as e:
    print(f"Failed to query OSM for Hanoi boundary: {e}")
    sys.exit(1)

elements = data.get('elements', [])
if not elements:
    print("Error: Hanoi relation not found!")
    sys.exit(1)

rel = elements[0]
members = rel.get('members', [])
boundary_lines = []
for member in members:
    role = member.get('role', '')
    if role != 'inner' and 'geometry' in member:
        coords = [[pt['lon'], pt['lat']] for pt in member['geometry']]
        if len(coords) >= 2:
            boundary_lines.append(LineString(coords))

polygons = list(polygonize(boundary_lines))
if not polygons:
    print("Error: Could not construct Hanoi boundary polygon!")
    sys.exit(1)

hanoi_shape = unary_union(polygons)
print(f"Loaded Hanoi Boundary. Area: {hanoi_shape.area * 111 * 103:.2f} sq km")

print("3. Querying OSM Red River (Song Hong) centerline...")
overpass_query_river = """
[out:json][timeout:90];
(
  relation["name"="Sông Hồng"]["waterway"="river"](20.5,105.2,21.3,106.1);
  way["name"="Sông Hồng"]["waterway"="river"](20.5,105.2,21.3,106.1);
);
out geom;
"""

try:
    response = requests.post(overpass_url, data={'data': overpass_query_river}, headers=headers, timeout=30)
    if response.status_code != 200:
        print("LZ4 failed, trying backup endpoint for river...")
        response = requests.post("https://overpass.osm.ch/api/interpreter", data={'data': overpass_query_river}, headers=headers, timeout=30)
    data = response.json()
except Exception as e:
    print(f"Failed to query OSM for river: {e}")
    sys.exit(1)

elements_river = data.get('elements', [])
print(f"Found {len(elements_river)} elements from OSM.")

osm_lines = []
for elem in elements_river:
    elem_type = elem['type']
    if elem_type == 'way':
        coords = [[pt['lon'], pt['lat']] for pt in elem['geometry']]
        if len(coords) >= 2:
            osm_lines.append(LineString(coords))
    elif elem_type == 'relation':
        for member in elem.get('members', []):
            if 'geometry' in member and len(member['geometry']) >= 2:
                coords = [[pt['lon'], pt['lat']] for pt in member['geometry']]
                osm_lines.append(LineString(coords))

if not osm_lines:
    print("Error: No river lines found from OSM!")
    sys.exit(1)

osm_river_geom = unary_union(osm_lines)

print("4. Clipping OSM Red River geometry by Hanoi boundary...")
clipped_river = osm_river_geom.intersection(hanoi_shape)

print("5. Creating visual check plot...")
fig, ax = plt.subplots(figsize=(10, 8))
if hanoi_shape.geom_type == 'Polygon':
    x, y = hanoi_shape.exterior.xy
    ax.plot(x, y, color='red', linewidth=1.5, label='Hanoi Boundary')
elif hanoi_shape.geom_type == 'MultiPolygon':
    for poly in hanoi_shape.geoms:
        x, y = poly.exterior.xy
        ax.plot(x, y, color='red', linewidth=1.5, label='Hanoi Boundary' if poly == list(hanoi_shape.geoms)[0] else "")

if clipped_river.geom_type == 'LineString':
    x, y = clipped_river.xy
    ax.plot(x, y, color='blue', linewidth=2, label='Clipped Red River (OSM)')
elif clipped_river.geom_type == 'MultiLineString':
    for line in clipped_river.geoms:
        x, y = line.xy
        ax.plot(x, y, color='blue', linewidth=2, label='Clipped Red River (OSM)' if line == list(clipped_river.geoms)[0] else "")

ax.set_title("OSM Red River Centerline Clipped by Hanoi")
ax.legend()
plot_path = r"d:\Future Career\SongHong-SAR-Monitoring\outputs\osm_river_check.png"
plt.savefig(plot_path, dpi=150)
plt.close()

print("6. Buffering entire centerline by 2 km...")
# 2km in degrees is approx 0.018
buffer_dist = 0.018
raw_buffer_geom = osm_river_geom.buffer(buffer_dist, cap_style=1, join_style=1)

print("7. Clipping the 2km buffer by Hanoi boundary...")
final_aoi_geom = raw_buffer_geom.intersection(hanoi_shape)

# Check Area
poly_area_km2 = final_aoi_geom.area * 111 * 103
print(f"Final OSM-based AOI Area (within Hanoi, 2.0km buffer): {poly_area_km2:.2f} sq km")

# Construct GeoJSON
geojson_output = {
  "type": "FeatureCollection",
  "name": "song_hong_aoi",
  "crs": {
    "type": "name",
    "properties": {
      "name": "urn:ogc:def:crs:OGC:1.3:CRS84"
    }
  },
  "features": [
    {
      "type": "Feature",
      "properties": {
        "name": "Song Hong AOI - Hanoi Section (OSM Centerline + 2km Buffer)",
        "description": "Hành lang Sông Hồng qua Hà Nội, lấy buffer 2km từ centerline của OpenStreetMap, giới hạn trong ranh giới Hà Nội",
        "crs": "WGS84 / EPSG:4326",
        "method": "OSM Hanoi boundary + OSM_Red_River_Centerline.buffer(2km) -> Clip by Hanoi",
        "created": "2026-07-01",
        "author": "Vu Duc Tung"
      },
      "geometry": mapping(final_aoi_geom)
    }
  ]
}

# Save GeoJSON
main_out_path = r"d:\Future Career\SongHong-SAR-Monitoring\aoi\song_hong_aoi.geojson"
with open(main_out_path, "w", encoding="utf-8") as f:
    json.dump(geojson_output, f, indent=2)

buffer_out_path = r"d:\Future Career\SongHong-SAR-Monitoring\aoi\song_hong_buffer_2km.geojson"
with open(buffer_out_path, "w", encoding="utf-8") as f:
    json.dump(geojson_output, f, indent=2)

backup_out_path = r"d:\Future Career\SongHong-SAR-Monitoring\outputs\esa_water_aoi.geojson"
with open(backup_out_path, "w", encoding="utf-8") as f:
    json.dump(geojson_output, f, indent=2)

# Construct centerline GeoJSON
centerline_geojson_output = {
  "type": "FeatureCollection",
  "name": "song_hong_centerline",
  "crs": {
    "type": "name",
    "properties": {
      "name": "urn:ogc:def:crs:OGC:1.3:CRS84"
    }
  },
  "features": [
    {
      "type": "Feature",
      "properties": {
        "name": "Song Hong Centerline - Hanoi Section (OSM)",
        "description": "Đường tim sông Hồng qua Hà Nội từ OpenStreetMap, giới hạn trong ranh giới Hà Nội",
        "crs": "WGS84 / EPSG:4326",
        "method": "OSM Hanoi boundary + OSM_Red_River_Centerline -> Clip by Hanoi",
        "created": "2026-07-01",
        "author": "Vu Duc Tung"
      },
      "geometry": mapping(clipped_river)
    }
  ]
}

centerline_out_path = r"d:\Future Career\SongHong-SAR-Monitoring\aoi\song_hong_centerline.geojson"
with open(centerline_out_path, "w", encoding="utf-8") as f:
    json.dump(centerline_geojson_output, f, indent=2)

print(f"Saved final AOI GeoJSON to: {main_out_path}")
print(f"Saved buffer 2km GeoJSON to: {buffer_out_path}")
print(f"Saved centerline GeoJSON to: {centerline_out_path}")

print("8. Creating interactive HTML map for visual verification...")
m = folium.Map(location=[21.04, 105.86], zoom_start=10, tiles='openstreetmap')

# Add Google Satellite base map
folium.TileLayer(
    tiles='https://mt1.google.com/vt/lyrs=s&x={x}&y={y}&z={z}',
    attr='Google',
    name='Google Satellite',
    overlay=False,
    control=True
).add_to(m)

# Add Hanoi boundary - Styled with bold red color to stand out clearly!
folium.GeoJson(
    mapping(hanoi_shape),
    name="Hanoi Boundary",
    style_function=lambda x: {'fillColor': 'none', 'color': '#ff3300', 'weight': 3.5, 'opacity': 0.9}
).add_to(m)

# Add OSM river centerline
folium.GeoJson(
    mapping(clipped_river),
    name="OSM Red River Centerline",
    style_function=lambda x: {'color': '#1f51ff', 'weight': 2.5}
).add_to(m)

# Add final AOI
folium.GeoJson(
    geojson_output,
    name="Song Hong AOI (2km Buffer)",
    style_function=lambda x: {'fillColor': '#1a73e8', 'fillOpacity': 0.3, 'color': '#1a73e8', 'weight': 2}
).add_to(m)

folium.LayerControl().add_to(m)

html_path = r"d:\Future Career\SongHong-SAR-Monitoring\outputs\check_final_aoi.html"
m.save(html_path)
print(f"Saved verification map to: {html_path}")
