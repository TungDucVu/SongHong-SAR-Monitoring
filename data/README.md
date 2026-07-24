# Thư mục Dữ liệu Bộ Mẫu Đối Chứng Sentinel-2 (Ground Truth Reference Cache)

Thư mục này lưu trữ bộ dữ liệu mặt nước và đường bờ chuẩn đối chứng được trích xuất từ vệ tinh quang học **Sentinel-2 (MNDWI/NDWI)** giai đoạn 2017 – 2026.

## 📁 Cấu trúc Dữ liệu

Dữ liệu được lưu trữ dạng GeoJSON trong hệ tọa độ WGS84 (`EPSG:4326`):

1. **`s2_ref_shoreline_{YYYY}_{season}.geojson`**: Đường bờ tham chiếu Sentinel-2 (MNDWI > 0.0) phân chia theo năm (`2017`–`2026`) và mùa (`dry` - mùa khô, `wet` - mùa mưa).
2. **`s2_water_poly_{YYYY}_{season}.geojson`**: Polygon lòng sông mở (Active River Channel) dùng làm mặt nạ không gian định hướng (Active Channel Buffer Constraints 150m).

## 🎯 Mục đích Kỹ thuật

- **Cache cục bộ (Local Caching):** Giảm thiểu số lần truy xuất trùng lặp tới Google Earth Engine API.
- **Tăng tốc độ kiểm chứng (KD-Tree Validation):** Cho phép các kịch bản kiểm chứng sai số đường bờ SAR chạy với tốc độ tính toán mili-giây trên máy local.
- **Độ tin cậy cao:** Đã được lọc mây (Cloud Masking QA60) và khử nhiễu thực vật ven bờ.
