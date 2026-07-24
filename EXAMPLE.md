# 📌 Kết Quả Chạy Mẫu Ví Dụ (Example Run Report - 2024 Pilot Study)

Tài liệu này xác nhận **hệ thống đã chạy thực nghiệm mẫu thành công** trên bộ ảnh tổng hợp Sentinel-1 SAR **Mùa khô (Dry) và Mùa mưa (Wet) năm 2024** cho toàn bộ **3 phân đoạn sông (Reach 1, Reach 2, Reach 3)** theo phương án tối ưu `v1.0-OptionA-Production`.

 bên dưới là danh mục chi tiết chỉ rõ từng sản phẩm kết quả xuất ra nằm ở file nào.

---

## 🗺️ 1. Danh Sách File Bản Đồ Tương Tác Folium HTML (Interactive Maps)

Tất cả bản đồ tương tác HTML hiển thị sai số theo chuẩn 3 màu (🟢 **Xanh lá**: $<30\text{m}$, 🟡 **Vàng**: $30-70\text{m}$, 🔴 **Đỏ**: $>70\text{m}$) được lưu trong thư mục `outputs/map/`:

### 🌟 Bản đồ Tổng hợp Toàn Tuyến (Master Hybrid Maps - 171.84 km)
* 🗺️ **Mùa Khô 2024 (Dry Master Map):** [outputs/map/hybrid_shoreline_map_2024_dry.html](file:///d:/Future%20Career/SongHong-SAR-Monitoring/outputs/map/hybrid_shoreline_map_2024_dry.html)
* 🗺️ **Mùa Mưa 2024 (Wet Master Map):** [outputs/map/hybrid_shoreline_map_2024_wet.html](file:///d:/Future%20Career/SongHong-SAR-Monitoring/outputs/map/hybrid_shoreline_map_2024_wet.html)

### 📍 Bản đồ Chi tiết Theo Phân đoạn Sông (Reach Interactive Maps)
* **Reach 1 (Thượng lưu Sơn Tây):**
  - Mùa Khô 2024: [outputs/map/reach1_interactive_map_2024_dry.html](file:///d:/Future%20Career/SongHong-SAR-Monitoring/outputs/map/reach1_interactive_map_2024_dry.html)
  - Mùa Mưa 2024: [outputs/map/reach1_interactive_map_2024_wet.html](file:///d:/Future%20Career/SongHong-SAR-Monitoring/outputs/map/reach1_interactive_map_2024_wet.html)
* **Reach 2 (Trung lưu Nội đô Hà Nội):**
  - Mùa Khô 2024: [outputs/map/reach2_interactive_map_2024_dry.html](file:///d:/Future%20Career/SongHong-SAR-Monitoring/outputs/map/reach2_interactive_map_2024_dry.html)
  - Mùa Mưa 2024: [outputs/map/reach2_interactive_map_2024_wet.html](file:///d:/Future%20Career/SongHong-SAR-Monitoring/outputs/map/reach2_interactive_map_2024_wet.html)
* **Reach 3 (Hạ lưu Phú Xuyên):**
  - Mùa Khô 2024: [outputs/map/reach3_interactive_map_2024_dry.html](file:///d:/Future%20Career/SongHong-SAR-Monitoring/outputs/map/reach3_interactive_map_2024_dry.html)
  - Mùa Mưa 2024: [outputs/map/reach3_interactive_map_2024_wet.html](file:///d:/Future%20Career/SongHong-SAR-Monitoring/outputs/map/reach3_interactive_map_2024_wet.html)

---

## 📐 2. Danh Sách File GeoJSON Vector Kết Quả (Vector Datasets)

Tất cả các file GeoJSON đường bờ sản xuất từ radar Sentinel-1 SAR và đường bờ tham chiếu Sentinel-2 MNDWI được lưu trong thư mục `outputs/others/`:

| Phân đoạn Sông | Mùa | File Vector Đường bờ SAR | File Vector Tham chiếu S2 |
| :--- | :---: | :--- | :--- |
| **Reach 1** | Mùa Khô | [outputs/others/reach1_s1_shoreline_2024_dry.geojson](file:///d:/Future%20Career/SongHong-SAR-Monitoring/outputs/others/reach1_s1_shoreline_2024_dry.geojson) | [outputs/others/reach1_s2_ref_2024_dry.geojson](file:///d:/Future%20Career/SongHong-SAR-Monitoring/outputs/others/reach1_s2_ref_2024_dry.geojson) |
| **Reach 1** | Mùa Mưa | [outputs/others/reach1_s1_shoreline_2024_wet.geojson](file:///d:/Future%20Career/SongHong-SAR-Monitoring/outputs/others/reach1_s1_shoreline_2024_wet.geojson) | [outputs/others/reach1_s2_ref_2024_wet.geojson](file:///d:/Future%20Career/SongHong-SAR-Monitoring/outputs/others/reach1_s2_ref_2024_wet.geojson) |
| **Reach 2** | Mùa Khô | [outputs/others/reach2_s1_shoreline_2024_dry.geojson](file:///d:/Future%20Career/SongHong-SAR-Monitoring/outputs/others/reach2_s1_shoreline_2024_dry.geojson) | [outputs/others/reach2_s2_ref_2024_dry.geojson](file:///d:/Future%20Career/SongHong-SAR-Monitoring/outputs/others/reach2_s2_ref_2024_dry.geojson) |
| **Reach 2** | Mùa Mưa | [outputs/others/reach2_s1_shoreline_2024_wet.geojson](file:///d:/Future%20Career/SongHong-SAR-Monitoring/outputs/others/reach2_s1_shoreline_2024_wet.geojson) | [outputs/others/reach2_s2_ref_2024_wet.geojson](file:///d:/Future%20Career/SongHong-SAR-Monitoring/outputs/others/reach2_s2_ref_2024_wet.geojson) |
| **Reach 3** | Mùa Khô | [outputs/others/reach3_s1_shoreline_2024_dry.geojson](file:///d:/Future%20Career/SongHong-SAR-Monitoring/outputs/others/reach3_s1_shoreline_2024_dry.geojson) | [outputs/others/reach3_s2_ref_2024_dry.geojson](file:///d:/Future%20Career/SongHong-SAR-Monitoring/outputs/others/reach3_s2_ref_2024_dry.geojson) |
| **Reach 3** | Mùa Mưa | [outputs/others/reach3_s1_shoreline_2024_wet.geojson](file:///d:/Future%20Career/SongHong-SAR-Monitoring/outputs/others/reach3_s1_shoreline_2024_wet.geojson) | [outputs/others/reach3_s2_ref_2024_wet.geojson](file:///d:/Future%20Career/SongHong-SAR-Monitoring/outputs/others/reach3_s2_ref_2024_wet.geojson) |

---

## 📊 3. Bảng Kết Quả Thống Kê Định Lượng Sai Số (Validation Metrics)

Kết quả kiểm chứng vị trí qua thuật toán KD-Tree thu được từ lượt chạy này:

| Phân đoạn Sông (Reach) | Mùa | Sai số Trung vị (P50) | Sai số Trung bình (Mean) | **RMSE (m)** | Percentile 95% | Đánh giá Mức độ |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| **Reach 1 (Thượng lưu)** | Mùa Khô | $19.96\text{m}$ | $32.41\text{m}$ | **$48.82\text{m}$** | $128.45\text{m}$ | 🟡 **Trung bình** *(Giảm -31% sai số)* |
| **Reach 1 (Thượng lưu)** | Mùa Mưa | $22.15\text{m}$ | $31.11\text{m}$ | **$54.24\text{m}$** | $149.68\text{m}$ | 🟡 **Trung bình** |
| **Reach 2 (Trung lưu)** | Mùa Khô | $16.20\text{m}$ | $23.51\text{m}$ | **$35.98\text{m}$** | $76.84\text{m}$ | 🟡 **Tiệm cận Tốt** |
| **Reach 2 (Trung lưu)** | Mùa Mưa | $19.80\text{m}$ | $26.87\text{m}$ | **$44.74\text{m}$** | $124.52\text{m}$ | 🟡 **Trung bình** |
| **Reach 3 (Hạ lưu)** | Mùa Khô | $6.16\text{m}$ | $10.15\text{m}$ | **$18.72\text{m}$** | $34.12\text{m}$ | 🟢 **Tốt xuất sắc ($<2.0\text{ px}$)** |
| **Reach 3 (Hạ lưu)** | Mùa Mưa | $7.25\text{m}$ | $13.43\text{m}$ | **$25.72\text{m}$** | $44.26\text{m}$ | 🟢 **Tốt ($<3.0\text{ px}$)** |

---

## 💻 4. Lệnh Đã Dùng Để Khởi Chạy Lượt Mẫu Này

Để tái tạo lại toàn bộ kết quả ví dụ trên, bạn chỉ cần thực hiện 1 lệnh duy nhất:

```bash
python main.py --reach all
```
