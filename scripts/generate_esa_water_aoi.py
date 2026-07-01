import sys, os
sys.path.insert(0, os.getcwd())
import ee
import json
from shapely.geometry import shape, mapping
from shapely.ops import unary_union

# Initialize GEE
ee.Initialize(project='crested-library-500309-i2')

# Define a simple, generous rectangular bounding box covering the entire study area to avoid clipping
study_area_bbox = ee.Geometry.Rectangle([105.25, 20.60, 106.05, 21.25])

# 1. Load ESA WorldCover 2020 (v100)
esa = ee.Image("ESA/WorldCover/v100/2020")
water_mask = esa.select('Map').eq(80)

# 2. Convert raw water mask to vector polygons at 30m resolution inside the bbox
water_vectors = water_mask.selfMask().reduceToVectors(
    geometry=study_area_bbox,
    scale=30,
    maxPixels=1e9
)

# 3. Define the correct river centerline coordinates starting exactly at the Red River near Son Tay
centerline_coords = [
    [105.3200, 21.1900], # Start exactly at Red River near Ba Vi/Son Tay junction
    [105.3500, 21.1800],
    [105.3840, 21.1850],
    [105.4330, 21.1950],
    [105.4640, 21.1980],
    [105.5180, 21.1800],
    [105.5860, 21.1560],
    [105.6310, 21.1350],
    [105.7020, 21.1150],
    [105.7520, 21.0980],
    [105.8060, 21.0890],
    [105.8640, 21.0400],
    [105.8900, 20.9900],
    [105.9100, 20.9500],
    [105.9300, 20.8900],
    [105.9500, 20.8200],
    [105.9600, 20.7600],
    [105.9500, 20.7000],
    [105.9300, 20.6600]
]
river_line = ee.Geometry.LineString(centerline_coords)

# Filter polygons that intersect the river centerline
river_water = water_vectors.filterBounds(river_line)

# 4. Fetch the GeoJSON of water polygons to Python
print("Fetching ESA water polygons from GEE (scale=30m)...")
water_geojson = river_water.geometry().getInfo()

# 5. In Python, load water polygons and buffer them using Shapely
water_shape = shape(water_geojson)

print("Buffering ESA water geometry in Python...")
# Buffer of 0.018 degrees (approx 2.0 km)
# Doing buffer in Shapely automatically merges all intersecting polygons and bridges gaps
buffered_shape = water_shape.buffer(0.018, cap_style=1, join_style=1)

# Simplify shape to keep coordinate count reasonable
simplified_shape = buffered_shape.simplify(0.0005)

# Check area
poly_area_km2 = simplified_shape.area * 111 * 103
print(f"ESA Hybrid AOI Area: {poly_area_km2:.2f} sq km")

# Construct final GeoJSON FeatureCollection
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
        "name": "Song Hong AOI - Ha Noi Section (ESA Water +2km Buffer)",
        "description": "Hanh lang Sông Hồng qua Hà Nội, chiết xuất từ ESA WorldCover 2020 với buffer +2km từ bờ sông (GEE+Shapely Hybrid)",
        "crs": "WGS84 / EPSG:4326",
        "method": "ESA WorldCover class 80 -> GEE reduceToVectors(30m) -> filterBounds(detailed centerline) -> Python Shapely buffer(0.018deg) -> simplify(0.0005deg)",
        "created": "2026-07-01",
        "author": "Vu Duc Tung (Auto-generated from ESA)"
      },
      "geometry": mapping(simplified_shape)
    }
  ]
}

# Write directly to the main path
main_out_path = r"d:\Future Career\SongHong-SAR-Monitoring\aoi\song_hong_aoi.geojson"
with open(main_out_path, "w", encoding="utf-8") as f:
    json.dump(geojson_output, f, indent=2)

# Copy to outputs as backup
backup_out_path = r"d:\Future Career\SongHong-SAR-Monitoring\outputs\esa_water_aoi.geojson"
with open(backup_out_path, "w", encoding="utf-8") as f:
    json.dump(geojson_output, f, indent=2)

print(f"Generated ESA-based water buffer AOI GeoJSON at: {main_out_path}")
