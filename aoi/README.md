# Thư mục AOI & Dữ liệu Không gian Đầu vào (AOI & Spatial Boundaries)

Thư mục này chứa các dữ liệu không gian GeoJSON chính thức chuẩn hóa (EPSG:4326 / EPSG:32648) cho dự án Giám sát Sông Hồng:

## 📐 Danh sách Dữ liệu Không gian Chính thức

1. **`song_hong_aoi.geojson`**: Ranh giới vùng nghiên cứu (AOI) tạo bởi khoảng đệm 2km xung quanh trục sông chính (diện tích hành lang ~343.68 km²).
2. **`song_hong_centerline.geojson`**: Trục đường tâm thủy văn chính xác dài 171.84 km phục vụ phân đoạn sông và đo khoảng cách chuẩn xác.
3. **`training_polygons.geojson`**: Bộ mẫu polygon huấn luyện chuẩn 4 lớp (Water, Sand, Built-up, Vegetation) cho mô hình Random Forest.
4. **`hanoi_boundary.geojson`**: Ranh giới hành chính thủ đô Hà Nội phục vụ cắt hành lang và kiểm định QC không gian.
5. **`aoi_reach1.geojson`**: Ranh giới phân đoạn 1 (Reach 1 - Thượng lưu Sơn Tây / Ba Vì / Phúc Thọ).
6. **`aoi_reach2.geojson`**: Ranh giới phân đoạn 2 (Reach 2 - Trung lưu Nội đô Hà Nội).
7. **`aoi_reach3.geojson`**: Ranh giới phân đoạn 3 (Reach 3 - Hạ lưu Phú Xuyên / Thường Tín / Thanh Trì).
