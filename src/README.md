# Thư mục Mã nguồn Cốt lõi (Core Python Package - `src`)

Thư mục `src/` đóng vai trò là thư viện core xử lý chính của dự án, được thiết kế theo cấu trúc modularize nhằm tái sử dụng mã nguồn.

## 🧩 Các Module Cốt lõi

1. **`config.py`**: Quản lý thiết lập toàn cục, tham số mô hình Random Forest, đường dẫn dữ liệu và cấu hình tài khoản GEE.
2. **`aoi.py`**: Quản lý hình học không gian AOI, chuyển đổi giữa GeoPandas GeoDataFrame và Earth Engine Geometry.
3. **`collection.py`**: Xây dựng ảnh tổng hợp đa thời gian (Multi-temporal Composite) với reducer **10th Percentile (P10)** và bộ lọc nhiễu Refined Lee Filter.
4. **`classification.py`**: Trích xuất không gian đặc trưng (17 băng đặc trưng), tính toán kết cấu nhanh (Fast Focal Neighborhood Textures) và huấn luyện/phân loại Random Forest.
5. **`preprocessing.py`**: Khử nhiễu biên ảnh Sentinel-1 SAR (Border Noise Removal) và lọc nhiễu hạt (Speckle Filtering).
6. **`shoreline.py`**: Chứa toàn bộ thuật toán trích xuất đường bờ:
   - Xử lý hình thái học (Morphological Majority, Open, Close Filter)
   - Lọc lòng sông mở (Active Channel Buffer Constraints 150m)
   - Đơn giản hóa đường bờ (Douglas-Peucker & B-Spline Smoothing)
   - Kiểm chứng sai số vị trí bằng thuật toán KD-Tree
7. **`utils.py`**: Các hàm tiện ích chuyển đổi tọa độ UTM (EPSG:32648), định dạng GeoJSON và ghi log.
