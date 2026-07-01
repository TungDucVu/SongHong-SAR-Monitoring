import sys, os
sys.path.insert(0, os.getcwd())
import ee
import json
import folium
from shapely.geometry import shape, mapping, MultiPolygon, Polygon
from shapely.ops import unary_union

# Initialize GEE
ee.Initialize(project='crested-library-500309-i2')

print("1. Fetching Hanoi boundary from GEE (FAO GAUL Level 1)...")
gaul1 = ee.FeatureCollection("FAO/GAUL/2015/level1")
hanoi_fc = gaul1.filter(ee.Filter.inList('ADM1_NAME', ['Ha Noi City', 'Ha Tay']))
hanoi_geojson = hanoi_fc.geometry().getInfo()
hanoi_shape = shape(hanoi_geojson)

print("2. Setting up Red River centerline...")
centerline_coords = [
    [105.3200, 21.1900],
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
centerline_line = ee.Geometry.LineString(centerline_coords)

# Convert centerline to Shapely line
centerline_shape = shape(centerline_line.getInfo())

print("3. Fetching ESA WorldCover water mask to refine shape...")
study_area_bbox = ee.Geometry.Rectangle([105.25, 20.60, 106.05, 21.25])
esa = ee.Image("ESA/WorldCover/v100/2020")
water_mask = esa.select('Map').eq(80)

# Vectorize water mask at 30m
water_vectors = water_mask.selfMask().reduceToVectors(
    geometry=study_area_bbox,
    scale=30,
    maxPixels=1e9
)

# Filter to keep only water bodies intersecting the centerline
river_water = water_vectors.filterBounds(centerline_line)
water_geojson = river_water.geometry().getInfo()
water_shape = shape(water_geojson)

print("4. Performing buffering and spatial union...")
# Buffer size for 3.0km (approx 0.027 degrees)
buffer_dist = 0.027

# Buffer centerline by 3.0km
centerline_buffered = centerline_shape.buffer(buffer_dist, cap_style=1, join_style=1)

# Buffer ESA water mask by 3.0km
water_buffered = water_shape.buffer(buffer_dist, cap_style=1, join_style=1)

# Union the centerline buffer and the ESA water buffer to bridge any gaps and track the actual riverbanks
union_buffered = centerline_buffered.union(water_buffered)

# Clip the unioned buffer by the Hanoi boundary
final_aoi = union_buffered.intersection(hanoi_shape)

# Check Area
poly_area_km2 = final_aoi.area * 111 * 103
print(f"Final AOI Area (within Hanoi, 3.0km buffer): {poly_area_km2:.2f} sq km")

# Construct final GeoJSON
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
        "name": "Song Hong AOI - Hanoi Section (Hanoi Clip, Centerline & ESA +3km Buffer)",
        "description": "Hành lang Sông Hồng qua Hà Nội, lấy buffer 3km từ tim sông và bờ sông (ESA), giới hạn trong ranh giới Hà Nội",
        "crs": "WGS84 / EPSG:4326",
        "method": "Hanoi GAUL boundary + Centerline.buffer(3km) + ESA_Water.buffer(3km) -> Union -> Clip by Hanoi",
        "created": "2026-07-01",
        "author": "Vu Duc Tung"
      },
      "geometry": mapping(final_aoi)
    }
  ]
}

# Save GeoJSON
main_out_path = r"d:\Future Career\SongHong-SAR-Monitoring\aoi\song_hong_aoi.geojson"
with open(main_out_path, "w", encoding="utf-8") as f:
    json.dump(geojson_output, f, indent=2)

backup_out_path = r"d:\Future Career\SongHong-SAR-Monitoring\outputs\esa_water_aoi.geojson"
with open(backup_out_path, "w", encoding="utf-8") as f:
    json.dump(geojson_output, f, indent=2)

print(f"Generated new AOI GeoJSON at: {main_out_path}")

print("5. Creating interactive HTML map for visual verification...")
m = folium.Map(location=[21.04, 105.86], zoom_start=10, tiles='openstreetmap')

# Add Google Satellite base map
folium.TileLayer(
    tiles='https://mt1.google.com/vt/lyrs=s&x={x}&y={y}&z={z}',
    attr='Google',
    name='Google Satellite',
    overlay=False,
    control=True
).add_to(m)

# Add Hanoi boundary
folium.GeoJson(
    hanoi_geojson,
    name="Hanoi Boundary",
    style_function=lambda x: {'fillColor': 'none', 'color': 'gray', 'weight': 2, 'dashArray': '5, 5'}
).add_to(m)

# Add centerline
folium.PolyLine(
    locations=[[pt[1], pt[0]] for pt in centerline_coords],
    color='red',
    weight=3,
    tooltip="Red River Centerline",
    name="Red River Centerline"
).add_to(m)

# Add final AOI
folium.GeoJson(
    geojson_output,
    name="Song Hong AOI (3km Buffer)",
    style_function=lambda x: {'fillColor': '#1a73e8', 'fillOpacity': 0.35, 'color': '#1a73e8', 'weight': 2}
).add_to(m)

folium.LayerControl().add_to(m)

html_path = r"d:\Future Career\SongHong-SAR-Monitoring\outputs\check_final_aoi.html"
m.save(html_path)
print(f"Saved verification map to: {html_path}")
