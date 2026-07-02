import json
import requests
import sys
from shapely.geometry import LineString, mapping
from shapely.ops import unary_union, polygonize

print("Fetching Hanoi boundary from OSM Overpass API...")
overpass_url = "https://lz4.overpass-api.de/api/interpreter"
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
        print("LZ4 failed, trying backup endpoint for Hanoi boundary...")
        response = requests.post("https://overpass.osm.ch/api/interpreter", data={'data': hanoi_query}, headers=headers, timeout=30)
    data = response.json()
except Exception as e:
    print(f"Failed to query OSM for Hanoi boundary: {e}")
    sys.exit(1)

elements = data.get('elements', [])
if not elements:
    print("Error: Hanoi relation not found! Overpass response did not contain elements.")
    print("Response snippet:", str(data)[:500])
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

hanoi_geojson = {
    "type": "FeatureCollection",
    "name": "hanoi_boundary",
    "features": [
        {
            "type": "Feature",
            "properties": {
                "name": "Hanoi Administrative Boundary",
                "source": "OpenStreetMap Relation 1903516"
            },
            "geometry": mapping(hanoi_shape)
        }
    ]
}

out_path = "aoi/hanoi_boundary.geojson"
with open(out_path, "w", encoding="utf-8") as f:
    json.dump(hanoi_geojson, f, indent=2)

print(f"Successfully saved Hanoi boundary to: {out_path}")
