# DANH MỤC CÁC TỆP SỬ DỤNG TRONG PIPELINE SẢN XUẤT CHÍNH THỨC (USING.MD)

Tài liệu này niêm yết toàn bộ danh mục các tệp mã nguồn, dữ liệu, kịch bản thực thi và tài liệu cấu hình chính thức được duy trì và sử dụng trong hệ thống **SongHong-SAR-Monitoring**.

---

## 1. KỊCH BẢN THỰC THI CHÍNH (`main_workflow/`)

| Tệp Kịch bản | Vai trò & Mục đích | Trạng thái |
| :--- | :--- | :---: |
| [main_workflow/run_hybrid_pipeline.py](file:///d:/Future%20Career/SongHong-SAR-Monitoring/main_workflow/run_hybrid_pipeline.py) | **Master Script Tích hợp (3 Reaches)**: Khởi chạy toàn bộ quy trình 3 mô hình lai ghép cho Reach 1, Reach 2, Reach 3 và tự động xuất bản đồ tương tác. | **Active** |
| [main_workflow/run_reach1_local.py](file:///d:/Future%20Career/SongHong-SAR-Monitoring/main_workflow/run_reach1_local.py) | **Reach 1 Local RF Runner**: Mô hình Random Forest phân loại đoạn Thượng lưu Ba Vì / Sơn Tây (Otsu 4-class, Hard Negative Mining, HAND/Slope). | **Active** |
| [main_workflow/run_reach2_local.py](file:///d:/Future%20Career/SongHong-SAR-Monitoring/main_workflow/run_reach2_local.py) | **Reach 2 Local RF Runner**: Mô hình Random Forest phân loại đoạn Trung lưu Hà Nội - tập trung phân loại bãi nổi/đảo nổi và bảo tồn đường bờ đô thị (bỏ qua can thiệp cầu). | **Active** |
| [main_workflow/run_reach3_local.py](file:///d:/Future%20Career/SongHong-SAR-Monitoring/main_workflow/run_reach3_local.py) | **Reach 3 Local RF Runner**: Mô hình Random Forest phân loại đoạn Hạ lưu Đồng bằng nông nghiệp. | **Active** |

---

## 2. THƯ VIỆN MÃ NGUỒN LÕI (`src/`)

| Tệp Mã nguồn | Mô tả Chức năng | Trạng thái |
| :--- | :--- | :---: |
| [src/shoreline.py](file:///d:/Future%20Career/SongHong-SAR-Monitoring/src/shoreline.py) | Thuật toán trích xuất ranh giới chung, làm sạch đồ thị, làm mịn Chaikin, kiểm định sai số & tự động sinh bản đồ tương tác cho từng Reach. | **Active** |
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
| [scripts/plot_hybrid_map.py](file:///d:/Future%20Career/SongHong-SAR-Monitoring/scripts/plot_hybrid_map.py) | Đọc dữ liệu GeoJSON 3 Reach và tạo bản đồ tương tác HTML Folium tổng hợp 3 phân đoạn. | **Active** |
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

## 5. TỆP ĐẦU RA SẢN XUẤT CHÍNH THỨC (`outputs/`)

- 🗺️ **[outputs/map/hybrid_shoreline_map_2024_dry.html](file:///d:/Future%20Career/SongHong-SAR-Monitoring/outputs/map/hybrid_shoreline_map_2024_dry.html)**: Bản đồ tương tác Tổng hợp 3 Reach Mùa Khô 2024.
- 🗺️ **[outputs/map/hybrid_shoreline_map_2024_wet.html](file:///d:/Future%20Career/SongHong-SAR-Monitoring/outputs/map/hybrid_shoreline_map_2024_wet.html)**: Bản đồ tương tác Tổng hợp 3 Reach Mùa Mưa 2024.
- 🗺️ **`outputs/map/reach1_interactive_map_2024_*.html`**: Bản đồ tương tác độc lập Reach 1 kèm **Validation Error Mask**.
- 🗺️ **`outputs/map/reach2_interactive_map_2024_*.html`**: Bản đồ tương tác độc lập Reach 2 kèm **Validation Error Mask**.
- 🗺️ **`outputs/map/reach3_interactive_map_2024_*.html`**: Bản đồ tương tác độc lập Reach 3 kèm **Validation Error Mask**.
- 🗺️ **`outputs/reach1_s1_shoreline_2024_*.geojson`**: GeoJSON đường bờ Sentinel-1 Reach 1.
- 🗺️ **`outputs/reach2_s1_shoreline_2024_*.geojson`**: GeoJSON đường bờ Sentinel-1 Reach 2.
- 🗺️ **`outputs/reach3_s1_shoreline_2024_*.geojson`**: GeoJSON đường bờ Sentinel-1 Reach 3.

---

## 6. BÁO CÁO & TÀI LIỆU HƯỚNG DẪN (`docs/` & `config/`)

| Tệp Tài liệu | Nội dung & Mục đích | Trạng thái |
| :--- | :--- | :---: |
| [docs/progress_report_2024.md](file:///d:/Future%20Career/SongHong-SAR-Monitoring/docs/progress_report_2024.md) | Báo cáo tiến độ chi tiết bằng tiếng Việt cho năm 2024. | **Active** |
| [docs/reach1_optimization_report.md](file:///d:/Future%20Career/SongHong-SAR-Monitoring/docs/reach1_optimization_report.md) | Báo cáo tối ưu hóa và đánh giá sai số kiểm định cho Reach 1. | **Active** |
| [docs/reach2_3_optimization_report.md](file:///d:/Future%20Career/SongHong-SAR-Monitoring/docs/reach2_3_optimization_report.md) | Báo cáo tối ưu hóa và đánh giá sai số kiểm định cho Reach 2 & 3. | **Active** |
| [config/model.md](file:///d:/Future%20Career/SongHong-SAR-Monitoring/config/model.md) | Hướng dẫn mô hình và nguyên tắc chạy toàn bộ hệ thống. | **Active** |
| [README.md](file:///d:/Future%20Career/SongHong-SAR-Monitoring/README.md) | Tài liệu giới thiệu và hướng dẫn tổng quan dự án. | **Active** |
