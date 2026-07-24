# DANH MỤC CÁC TỆP SỬ DỤNG TRONG PIPELINE SẢN XUẤT CHÍNH THỨC (USING.MD)

Tài liệu này niêm yết toàn bộ danh mục các tệp mã nguồn, dữ liệu, kịch bản thực thi và tài liệu cấu hình chính thức được duy trì và sử dụng trong hệ thống **SongHong-SAR-Monitoring** (Phiên bản `v1.0-OptionA-Production`).

---

## 1. KỊCH BẢN ĐIỀU KHIỂN & LUỒNG THỰC THI

| Tệp Kịch bản | Vai trò & Mục đích | Trạng thái |
| :--- | :--- | :---: |
| [main.py](file:///d:/Future%20Career/SongHong-SAR-Monitoring/main.py) | **Unified Quickstart CLI Runner**: Bộ điều khiển trung tâm khởi chạy toàn bộ Reach 1, 2, 3, Master Hybrid Maps và chuỗi thời gian 10 năm. | **Active** |
| [main_workflow/run_reach1_local.py](file:///d:/Future%20Career/SongHong-SAR-Monitoring/main_workflow/run_reach1_local.py) | **Reach 1 Local RF Runner**: Mô hình Random Forest phân loại đoạn Thượng lưu Ba Vì / Sơn Tây (Otsu 4-class, Hard Negative Mining, HAND/Slope). | **Active** |
| [main_workflow/run_reach2_local.py](file:///d:/Future%20Career/SongHong-SAR-Monitoring/main_workflow/run_reach2_local.py) | **Reach 2 Local RF Runner**: Mô hình Random Forest phân loại đoạn Trung lưu Hà Nội (Bridge Piercing nối bờ qua 6 cầu lớn, Island Buffer Overlay). | **Active** |
| [main_workflow/run_reach3_local.py](file:///d:/Future%20Career/SongHong-SAR-Monitoring/main_workflow/run_reach3_local.py) | **Reach 3 Local RF Runner**: Mô hình Random Forest phân loại đoạn Hạ lưu Đồng bằng Phú Xuyên (Đạt chuẩn Tốt xuất sắc $<2\text{ px}$). | **Active** |

---

## 2. THƯ VIỆN MÃ NGUỒN LÕI (`src/`)

| Tệp Mã nguồn | Mô tả Chức năng | Trạng thái |
| :--- | :--- | :---: |
| [src/config.py](file:///d:/Future%20Career/SongHong-SAR-Monitoring/src/config.py) | Định nghĩa tham số cấu hình hệ thống, GEE Project ID (`songhong-sar-monitoring`) và tham số Random Forest. | **Active** |
| [src/collection.py](file:///d:/Future%20Career/SongHong-SAR-Monitoring/src/collection.py) | Lọc và ghép ảnh Sentinel-1 composite theo mùa bằng **10th Percentile Reducer (P10)** và Refined Lee Filter. | **Active** |
| [src/classification.py](file:///d:/Future%20Career/SongHong-SAR-Monitoring/src/classification.py) | Trích xuất 17 kênh đặc trưng, tính toán Fast Focal Neighborhood Textures ($3\times3$) và phân loại Random Forest. | **Active** |
| [src/shoreline.py](file:///d:/Future%20Career/SongHong-SAR-Monitoring/src/shoreline.py) | Lọc hình thái học, Active Channel Buffer 150m, đơn giản hóa Douglas-Peucker/B-Spline & kiểm chứng KD-Tree. | **Active** |
| [src/preprocessing.py](file:///d:/Future%20Career/SongHong-SAR-Monitoring/src/preprocessing.py) | Tiền xử lý khử nhiễu biên ảnh Sentinel-1 SAR (Border Noise Removal) và lọc nhiễu hạt. | **Active** |
| [src/aoi.py](file:///d:/Future%20Career/SongHong-SAR-Monitoring/src/aoi.py) | Tự động tải và nạp dữ liệu không gian AOI hành lang sông Hồng. | **Active** |
| [src/utils.py](file:///d:/Future%20Career/SongHong-SAR-Monitoring/src/utils.py) | Tiện ích hình học, chuyển đổi hệ tọa độ UTM (EPSG:32648) và ghi log. | **Active** |

---

## 3. THƯ MỤC CÔNG CỤ & TIỆN ÍCH (`scripts/`)

| Tệp Tiện ích | Vai trò & Mục đích | Trạng thái |
| :--- | :--- | :---: |
| [scripts/plot_hybrid_map.py](file:///d:/Future%20Career/SongHong-SAR-Monitoring/scripts/plot_hybrid_map.py) | Ghép nối dữ liệu GeoJSON 3 Reach và tạo bản đồ tương tác HTML Folium Master Hybrid toàn sông (171.84 km). | **Active** |
| [scripts/train_classifier.py](file:///d:/Future%20Career/SongHong-SAR-Monitoring/scripts/train_classifier.py) | Huấn luyện và đánh giá ma trận nhầm lẫn (Confusion Matrix) mô hình Random Forest. | **Active** |
| [scripts/extract_research_shoreline.py](file:///d:/Future%20Career/SongHong-SAR-Monitoring/scripts/extract_research_shoreline.py) | Kịch bản tự động xử lý trích xuất đường bờ chuỗi thời gian nhiều năm (2017 – 2026). | **Active** |

---

## 4. DỮ LIỆU KHÔNG GIAN & BỘ MẪU ĐỐI CHỨNG (`aoi/` & `data/`)

| Đường dẫn Dữ liệu | Nội dung & Mục đích | Trạng thái |
| :--- | :--- | :---: |
| [aoi/song_hong_aoi.geojson](file:///d:/Future%20Career/SongHong-SAR-Monitoring/aoi/song_hong_aoi.geojson) | Ranh giới AOI hành lang 2km toàn sông Hồng. | **Active** |
| [aoi/song_hong_centerline.geojson](file:///d:/Future%20Career/SongHong-SAR-Monitoring/aoi/song_hong_centerline.geojson) | Trục đường tâm thủy văn chính xác dài 171.84 km. | **Active** |
| [aoi/training_polygons.geojson](file:///d:/Future%20Career/SongHong-SAR-Monitoring/aoi/training_polygons.geojson) | Bộ đa giác mẫu huấn luyện 4 lớp cho Random Forest. | **Active** |
| `data/s2_ref_shoreline_*.geojson` | Cache GeoJSON đường bờ đối chứng Sentinel-2 MNDWI (2017-2026). | **Active** |
| `data/s2_water_poly_*.geojson` | Cache GeoJSON mặt nạ nước Sentinel-2 NDWI (2017-2026). | **Active** |

---

## 5. TỆP ĐẦU RA SẢN XUẤT CHÍNH THỨC (`outputs/`)

- 🗺️ **[outputs/map/hybrid_shoreline_map_2024_dry.html](file:///d:/Future%20Career/SongHong-SAR-Monitoring/outputs/map/hybrid_shoreline_map_2024_dry.html)**: Bản đồ tương tác Tổng hợp Master Mùa Khô 2024.
- 🗺️ **[outputs/map/hybrid_shoreline_map_2024_wet.html](file:///d:/Future%20Career/SongHong-SAR-Monitoring/outputs/map/hybrid_shoreline_map_2024_wet.html)**: Bản đồ tương tác Tổng hợp Master Mùa Mưa 2024.
- 🗺️ **`outputs/map/reach*_interactive_map_2024_*.html`**: Bản đồ tương tác từng Reach kèm **3-Tier Validation Rating Legend**.
- 📐 **`outputs/others/reach*_s1_shoreline_2024_*.geojson`**: GeoJSON đường bờ sản xuất Sentinel-1 SAR.
- 📐 **`outputs/others/reach*_s2_ref_2024_*.geojson`**: GeoJSON đường bờ tham chiếu Sentinel-2 MNDWI.
- 📄 **`outputs/REPORT/`**: Thư mục chứa Báo cáo khoa học (MD/TeX), Slide thuyết minh HTML5 & 30 hình ảnh PNG.

---

## 6. TÀI LIỆU HƯỚNG DẪN & BÁO CÁO KHOA HỌC (`docs/` & Root)

| Tệp Tài liệu | Nội dung & Mục đích | Trạng thái |
| :--- | :--- | :---: |
| [README.md](file:///d:/Future%20Career/SongHong-SAR-Monitoring/README.md) | Tài liệu giới thiệu tổng quan dự án & mô tả GitHub. | **Active** |
| [WALKTHROUGH.md](file:///d:/Future%20Career/SongHong-SAR-Monitoring/WALKTHROUGH.md) | Hướng dẫn vận hành chi tiết & tùy biến mã nguồn. | **Active** |
| [EXAMPLE.md](file:///d:/Future%20Career/SongHong-SAR-Monitoring/EXAMPLE.md) | Danh mục chi tiết vị trí các file kết quả thử nghiệm mẫu 2024. | **Active** |
| [docs/model.md](file:///d:/Future%20Career/SongHong-SAR-Monitoring/docs/model.md) | Mô tả chi tiết kiến trúc thuật toán & tham số mô hình. | **Active** |
| [docs/using.md](file:///d:/Future%20Career/SongHong-SAR-Monitoring/docs/using.md) | Danh mục niêm yết tệp sử dụng trong hệ thống sản xuất. | **Active** |
| [docs/PROJECT_100_REPORT.md](file:///d:/Future%20Career/SongHong-SAR-Monitoring/docs/PROJECT_100_REPORT.md) | Báo cáo nghiệm thu tổng thể 100% tiến độ dự án. | **Active** |
