import json
import matplotlib.pyplot as plt
from shapely.geometry import shape

# Load generated ESA AOI GeoJSON
with open(r"d:\Future Career\SongHong-SAR-Monitoring\aoi\song_hong_aoi.geojson", "r", encoding="utf-8") as f:
    geojson = json.load(f)

geom = shape(geojson["features"][0]["geometry"])
poly_area_km2 = geom.area * 111 * 103

# Plot
plt.figure(figsize=(10, 8))

# Check geometry type: could be Polygon or MultiPolygon
if geom.geom_type == 'Polygon':
    x, y = geom.exterior.xy
    plt.plot(x, y, 'r-', linewidth=1.5, label='ESA Water Buffer AOI')
    plt.fill(x, y, alpha=0.2, color='red')
elif geom.geom_type == 'MultiPolygon':
    for poly in geom.geoms:
        x, y = poly.exterior.xy
        plt.plot(x, y, 'r-', linewidth=1.5)
        plt.fill(x, y, alpha=0.2, color='red')
    plt.plot([], [], 'r-', label='ESA Water Buffer AOI (MultiPolygon)')

# Highlight locations
plt.plot(105.85, 21.03, "bo", label="Hanoi Center (approx)")
plt.plot(105.32, 21.19, "go", label="Son Tay / Ba Vi (approx)")
plt.plot(105.95, 20.70, "mo", label="Phu Xuyen (approx)")

plt.title(f"ESA Water Buffer +2km AOI (Area: {poly_area_km2:.2f} sq km)")
plt.xlabel("Longitude")
plt.ylabel("Latitude")
plt.grid(True)
plt.legend()

plot_path = r"d:\Future Career\SongHong-SAR-Monitoring\outputs\esa_aoi_plot.png"
plt.savefig(plot_path, dpi=150)
print(f"Saved plot to: {plot_path}")
