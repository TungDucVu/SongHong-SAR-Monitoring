# DANH MỤC CÁC TỆP SỬ DỤNG TRONG PIPELINE SẢN XUẤT CHÍNH THỨC (USING.MD)

Tài liệu này niêm yết toàn bộ danh mục các tệp mã nguồn, dữ liệu, kịch bản thực thi và tài liệu cấu hình chính thức được duy trì và sử dụng trong hệ thống **SongHong-SAR-Monitoring**. Tất cả các tệp không nằm trong danh mục này đã được dọn dẹp để giữ cho thư mục làm việc của dự án tối giản và chuyên nghiệp.

---

## 1. KỊCH BẢN THỰC THI CHÍNH (`main_workflow/`)

| Tệp Kịch bản | Vai trò & Mục đích | Trạng thái |
| :--- | :--- | :---: |
| [main_workflow/run_hybrid_pipeline.py](file:///d:/Future%20Career/SongHong-SAR-Monitoring/main_workflow/run_hybrid_pipeline.py) | **Master Script Tích hợp**: Khởi chạy toàn bộ quy trình lai kép cho Reach 1, Reach 2&3 và tự động xuất bản đồ HTML. | **Active** |
| [main_workflow/run_reach1_local.py](file:///d:/Future%20Career/SongHong-SAR-Monitoring/main_workflow/run_reach1_local.py) | **Reach 1 Local RF Runner**: Mô hình Random Forest cục bộ phân loại đoạn Thượng lưu Ba Vì / Sơn Tây (Otsu 4-class, Hard Negative Mining, HAND/Slope). | **Active** |
| [main_workflow/run_reach2_3_global.py](file:///d:/Future%20Career/SongHong-SAR-Monitoring/main_workflow/run_reach2_3_global.py) | **Reach 2 & 3 Global RF Runner**: Mô hình Global Random Forest phân loại diện rộng 114km hành lang Hà Nội & Đồng bằng sông Hồng. | **Active** |

---

## 2. THƯ VIỆN MÃ NGUỒN LÕI (`src/`)

| Tệp Mã nguồn | Mô tả Chức năng | Trạng thái |
| :--- | :--- | :---: |
| [src/shoreline.py](file:///d:/Future%20Career/SongHong-SAR-Monitoring/src/shoreline.py) | Thuật toán trích xuất ranh giới chung, làm sạch đồ thị, làm mịn Chaikin & kiểm định sai số. | **Active** |
| [src/classification.py](file:///d:/Future%20Career/SongHong-SAR-Monitoring/src/classification.py) | Huấn luyện Random Forest, tạo GLCM textures (Contrast, Variance, Entropy, ASM) & phân loại ảnh ra-đa. | **Active** |
| [src/preprocessing.py](file:///d:/Future%20Career/SongHong-SAR-Monitoring/src/preprocessing.py) | Khử nhiễu đốm Refined Lee Filter cho ảnh Sentinel-1 SAR. | **Active** |
| [src/collection.py](file:///d:/Future%20Career/SongHong-SAR-Monitoring/src/collection.py) | Lọc và ghép ảnh Sentinel-1 composite theo mùa (Dry / Wet Season Median Composites). | **Active** |
| [src/qc.py](file:///d:/Future%20Career/SongHong-SAR-Monitoring/src/qc.py) | Hệ thống kiểm tra chất lượng tự động (QC Checkpoints & Assertions). | **Active** |
| [src/qa_suite.py](file:///d:/Future%20Career/SongHong-SAR-Monitoring/src/qa_suite.py) | Bộ công cụ đánh giá & kiểm định chất lượng ranh giới mặt nước. | **Active** |
| [src/aoi.py](file:///d:/Future%20Career/SongHong-SAR-Monitoring/src/aoi.py) | Tự động tải và dựng hình học hành lang sông Hồng (AOI Buffer 2km). | **Active** |
| [src/config.py](file:///d:/Future%20Career/SongHong-SAR-Monitoring/src/config.py) | Chứa các tham số cấu hình hệ thống, ngưỡng chỉ số và đường dẫn lưu trữ. | **Active** |

---

## 3. THƯ MỤC CÔNG CỤ & TIỆN ÍCH (`scripts/`)

| Tệp Tiện ích | Vai trò & Mục đích | Trạng thái |
| :--- | :--- | :---: |
| [scripts/plot_hybrid_map.py](file:///d:/Future%20Career/SongHong-SAR-Monitoring/scripts/plot_hybrid_map.py) | Tự động đọc dữ liệu GeoJSON 3 Reach và tạo bản đồ tương tác HTML Folium. | **Active** |
| [scripts/expand_training_polys.py](file:///d:/Future%20Career/SongHong-SAR-Monitoring/scripts/expand_training_polys.py) | Mở rộng và chuẩn hóa tập đa giác mẫu huấn luyện cho Random Forest. | **Active** |
| [scripts/download_s2_water_masks.py](file:///d:/Future%20Career/SongHong-SAR-Monitoring/scripts/download_s2_water_masks.py) | Tải và lưu trữ cache dữ liệu tham chiếu Sentinel-2 NDWI. | **Active** |
| [scripts/generate_osm_based_aoi.py](file:///d:/Future%20Career/SongHong-SAR-Monitoring/scripts/generate_osm_based_aoi.py) | Dựng AOI hành lang sông từ OpenStreetMap. | **Active** |

---

## 4. DỮ LIỆU CHUẨN (`data/`)

| Tệp Dữ liệu | Nội dung | Trạng thái |
| :--- | :--- | :---: |
| [data/bridges.geojson](file:///d:/Future%20Career/SongHong-SAR-Monitoring/data/bridges.geojson) | Tập đa giác các cây cầu bắc qua sông Hồng (Nhật Tân, Long Biên, Thăng Long, Vĩnh Tuy, Thanh Trì). | **Active** |
| `data/s2_ref_shoreline_*.geojson` | GeoJSON đường bờ chuẩn Sentinel-2 NDWI cache theo từng mùa/năm. | **Active** |
| `data/s2_water_poly_*.geojson` | GeoJSON mặt nạ nước Sentinel-2 cache theo từng mùa/năm. | **Active** |

---

## 5. TỆP ĐẦU RA SẢN XUẤT THU GỌN (`outputs/`)

Toàn bộ các tệp `.tif` raster nặng và tệp HTML debug tạm thời đã được làm sạch. Thư mục `outputs/` chỉ giữ lại các tệp sản xuất cuối cùng:

- 🗺️ **[outputs/hybrid_shoreline_map_2024_dry.html](file:///d:/Future%20Career/SongHong-SAR-Monitoring/outputs/hybrid_shoreline_map_2024_dry.html)**: Bản đồ tương tác Hybrid Mùa Khô 2024.
- 🗺️ **[outputs/hybrid_shoreline_map_2024_wet.html](file:///d:/Future%20Career/SongHong-SAR-Monitoring/outputs/hybrid_shoreline_map_2024_wet.html)**: Bản đồ tương tác Hybrid Mùa Mưa 2024.
- 🗺️ **`outputs/shoreline_2024_*_final.geojson`**: GeoJSON đường bờ Sentinel-1 sản xuất chính thức.
- 🗺️ **`outputs/shoreline_2024_*_s2_ref.geojson`**: GeoJSON đường bờ tham chiếu Sentinel-2.
- 📊 **`outputs/error_histogram_2024_*.png`**: Đồ thị Phân bố Sai số Khoảng cách.
- 📊 **`outputs/error_cdf_2024_*.png`**: Đồ thị Phân bố Tích lũy Sai số (Empirical CDF).
- 📈 **`outputs/reach_validation_statistics_2024_*.csv`**: Bảng thống kê sai số kiểm định theo từng Reach.

---

## 6. BÁO CÁO & TÀI LIỆU HƯỚNG DẪN (`docs/` & `config/`)

| Tệp Tài liệu | Nội dung & Mục đích | Trạng thái |
| :--- | :--- | :---: |
| [docs/progress_report_2024.md](file:///d:/Future%20Career/SongHong-SAR-Monitoring/docs/progress_report_2024.md) | Báo cáo tiến độ chi tiết bằng tiếng Việt cho năm 2024. | **Active** |
| [docs/reach1_optimization_report.md](file:///d:/Future%20Career/SongHong-SAR-Monitoring/docs/reach1_optimization_report.md) | Báo cáo tối ưu hóa và đánh giá sai số kiểm định cho Reach 1. | **Active** |
| [docs/reach2_3_optimization_report.md](file:///d:/Future%20Career/SongHong-SAR-Monitoring/docs/reach2_3_optimization_report.md) | Báo cáo tối ưu hóa và đánh giá sai số kiểm định cho Reach 2 & 3. | **Active** |
| [config/model.md](file:///d:/Future%20Career/SongHong-SAR-Monitoring/config/model.md) | Hướng dẫn mô hình và nguyên tắc chạy toàn bộ hệ thống. | **Active** |
| [README.md](file:///d:/Future%20Career/SongHong-SAR-Monitoring/README.md) | Tài liệu giới thiệu và hướng dẫn tổng quan dự án. | **Active** |
