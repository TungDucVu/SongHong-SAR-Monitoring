import os
import geopandas as gpd
from shapely.geometry import LineString

# Define verified bridge coordinates (lon, lat)
bridges_info = {
    "Thang Long": [[105.7855, 21.1128], [105.7874, 21.0852]],
    "Nhat Tan": [[105.8270, 21.1142], [105.8158, 21.0835]],
    "Long Bien": [[105.8560, 21.0450], [105.8690, 21.0400]],
    "Chuong Duong": [[105.8580, 21.0440], [105.8710, 21.0390]],
    "Vinh Tuy": [[105.8740, 21.0030], [105.8970, 20.9960]],
    "Thanh Tri": [[105.8920, 20.9830], [105.9120, 20.9710]],
    "Vinh Thinh": [[105.5026, 21.1937], [105.4824, 21.1581]],
    "Van Lang": [[105.4044, 21.2861], [105.4138, 21.3003]],
    "Trung Ha": [[105.3538, 21.2336], [105.3468, 21.2361]],
    "Yen Lenh": [[106.0241, 20.6574], [106.0454, 20.6588]]
}

features = []
for name, coords in bridges_info.items():
    features.append({
        "type": "Feature",
        "properties": {"name": name, "id": name.lower().replace(" ", "_")},
        "geometry": LineString(coords)
    })

# Convert to GeoDataFrame
gdf_lines = gpd.GeoDataFrame.from_features(features, crs="EPSG:4326")

# Reproject to UTM Zone 48N to buffer accurately in meters
gdf_utm = gdf_lines.to_crs("EPSG:32648")

# Buffer by 40 meters (representing bridge width buffer)
gdf_utm.geometry = gdf_utm.geometry.buffer(40.0)

# Reproject back to WGS84 for standard GeoJSON storage
gdf_wgs84 = gdf_utm.to_crs("EPSG:4326")

# Create data directory if not exists
os.makedirs("data", exist_ok=True)

# Save to data/bridges.geojson
output_path = os.path.join("data", "bridges.geojson")
gdf_wgs84.to_file(output_path, driver="GeoJSON")
print(f"[Success] Initialized {len(gdf_wgs84)} bridge polygons at: {output_path}")
print("Bridge names:", gdf_wgs84['name'].tolist())
