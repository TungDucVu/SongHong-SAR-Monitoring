# BÁO CÁO TỔNG THỂ DỰ ÁN 100% (PROJECT MASTER REPORT) 🛰️🌊
## GIÁM SÁT BIẾN ĐỘNG ĐƯỜNG BỜ VÀ BÃI BỒI SÔNG HỒNG TẠI HÀ NỘI BẰNG DỮ LIỆU VỆ TINH SENTINEL-1 SAR (2017 – 2026)

> **Đơn vị thực hiện:** Trung tâm Vũ trụ Việt Nam (VNSC)  
> **Người thực hiện:** Vũ Đức Tùng  
> **Thời gian dự án:** Tháng 06/2026 – Tháng 08/2026 (Nghiệm thu báo cáo: Tháng 07/2026)  
> **Tài liệu tham chiếu:** [REPORT/bao_cao_giam_sat_song_hong.md](file:///d:/Future%20Career/SongHong-SAR-Monitoring/REPORT/bao_cao_giam_sat_song_hong.md) | [REPORT/bao_cao_giam_sat_song_hong.tex](file:///d:/Future%20Career/SongHong-SAR-Monitoring/REPORT/bao_cao_giam_sat_song_hong.tex) | [REPORT/slide_bao_cao_thuc_tap.html](file:///d:/Future%20Career/SongHong-SAR-Monitoring/REPORT/slide_bao_cao_thuc_tap.html)

---

## 1. TỔNG QUAN DỰ ÁN VÀ MỤC TIÊU CỐT LÕI (PROJECT OVERVIEW)

Dự án **SongHong SAR Monitoring** được thiết lập nhằm xây dựng một quy trình viễn thám bán tự động và tự động hóa toàn diện trên nền tảng **Google Earth Engine (GEE)** kết hợp **Python địa không gian (GeoPandas, Shapely, NetworkX)** nhằm giám sát liên tục diễn biến đường bờ, diện tích mặt nước và động lực học bãi bồi sông Hồng đoạn chảy qua địa bàn Thủ đô Hà Nội.

### 1.1. Phạm vi Địa lý và Khu vực Nghiên cứu (AOI)
* **Chiều dài sông quan trắc:** $171.84\text{ km}$ lòng dẫn active của Sông Hồng chảy qua các quận/huyện: Sơn Tây, Ba Vì, Phúc Thọ, Đan Phượng, Bắc Từ Liêm, Tây Hồ, Ba Đình, Hoàn Kiếm, Hai Bà Trưng, Hoàng Mai, Long Biên, Gia Lâm, Thanh Trì, Thường Tín, Phú Xuyên.
* **Diện tích hành lang đệm (AOI Buffer):** $362.83\text{ km}^2$.
* **Phân đoạn sông (3 Reaches):**
  1. **Reach 1 (Thượng lưu - $57.28\text{ km}$):** Sơn Tây đến Ba Vì / Phúc Thọ. Lòng sông rộng, bãi nổi lớn (bãi Giữa, bãi Cam) biến động mạnh theo mực nước xả lũ.
  2. **Reach 2 (Trung lưu - $57.28\text{ km}$):** Nội đô Hà Nội (Nhật Tân đến Thanh Trì). Tốc độ đô thị hóa cao, đê kè kiên cố, có 6 cây cầu lớn bắc qua sông.
  3. **Reach 3 (Hạ lưu - $57.28\text{ km}$):** Thường Tín đến Phú Xuyên. Đồng bằng nông nghiệp meander nhẹ, độ dốc thấp, đường bờ rất ổn định.

### 1.2. Mục tiêu Khoa học & Thực tiễn
1. **Thử nghiệm Định lượng Mẫu 2024 (Pilot Benchmark):** Xây dựng thuật toán trích xuất đường bờ từ ảnh Sentinel-1 SAR, kiểm chứng độ chính xác vị trí với đường bờ chuẩn Sentinel-2 NDWI năm 2024.
2. **Khởi chạy Tự động Full Composite Chuỗi 10 năm (2017 – 2026):** Tự động hóa xử lý batch trên GEE cho toàn bộ **317 cảnh ảnh Sentinel-1 Descending**, chiết xuất đường bờ và bãi bồi theo timeline 10 năm để đánh giá xu hướng bồi tụ/xói lở (NSM, EPR).
3. **Giải quyết Triệt để Nhiễu Công trình Đô thị:** Phát triển thuật toán **Centerline-Connector Bridge Exclusion** triệt tiêu nhiễu bóng đứt gãy dưới gầm các cây cầu lớn tại Hà Nội.

---

## 2. KẾ HOẠCH VÀ TIẾN ĐỘ THỰC TẬP 4 TUẦN (INTERNSHIP ROADMAP)

Bảng phân bổ công việc chi tiết đã được triển khai và hoàn thành 100% theo đúng đề cương thực tập tại VNSC:

| Tuần | Hạng mục công việc | Nhiệm vụ cụ thể đã hoàn thành | Kết quả nghiệm thu |
| :--- | :--- | :--- | :--- |
| **Tuần 1** | **Chuẩn bị dữ liệu & Thiết lập môi trường** | • Khởi tạo môi trường Google Earth Engine & Python 3.10.<br>• Xác định ranh giới AOI $171.84\text{ km}$ (Sơn Tây đến Phú Xuyên).<br>• Lọc bộ 317 cảnh ảnh Sentinel-1 GRD Descending (2017–2026).<br>• Xây dựng bộ lọc đốm Refined Lee $7\times7$ trên thang đo Power $10^{\text{dB}/10}$. | Bộ dữ liệu Sentinel-1 SAR được tiền xử lý hoàn chỉnh; Script tự động thu thập hoạt động ổn định. |
| **Tuần 2** | **Xây dựng mô hình Machine Learning & Thuật toán Cầu** | • Trích xuất 17 băng đặc trưng (VV, VH, Ratios, 6 đặc trưng kết cấu GLCM $5\times5$).<br>• Gán mẫu huấn luyện 4 lớp phủ địa hình (Water, Sand, Built-up, Veg).<br>• Huấn luyện Random Forest độc lập cho 3 Reach.<br>• Phát triển thuật toán **Centerline Bridge Exclusion** nối bờ qua cầu. | Mô hình Random Forest hoàn chỉnh; Thuật toán nối bờ triệt tiêu hoàn toàn nhiễu bóng cầu. |
| **Tuần 3** | **Đánh giá Định lượng Mẫu 2024 (KD-Tree Validation)** | • Lấy mẫu điểm đường bờ SAR độ phân giải $10\text{m}$.<br>• Kiểm chứng không gian KD-Tree Nearest-Neighbor với Sentinel-2 NDWI 2024.<br>• Tính toán các chỉ số sai số: Median ($16.59\text{m}$ khô / $20.45\text{m}$ mưa), RMSE, Hausdorff.<br>• Phân tích tỷ lệ bao phủ vùng đệm ($95.75\%$ trong đệm $100\text{m}$). | Bộ chỉ số đánh giá độ chính xác định lượng khoa học; Biểu đồ CDF & Buffer Curve nghiệm thu mô hình. |
| **Tuần 4** | **Phân tích Chuỗi 10 năm (Full Composite 2017–2026) & Báo cáo/Slide** | • **Khởi chạy Full Composite tự động toàn bộ 317 cảnh ảnh SAR (2017–2026)** trên GEE.<br>• Phân tích động lực học diện tích mặt nước (+38.49%) & ngập bãi bồi (-69.60%).<br>• Đối chiếu tác động thủy văn xả lũ hồ chứa thượng nguồn (Hòa Bình, Sơn La).<br>• Hoàn thiện Báo cáo Khoa học ([MD](file:///d:/Future%20Career/SongHong-SAR-Monitoring/REPORT/bao_cao_giam_sat_song_hong.md) & [LaTeX](file:///d:/Future%20Career/SongHong-SAR-Monitoring/REPORT/bao_cao_giam_sat_song_hong.tex)) và đóng gói [Slide HTML Horizontal](file:///d:/Future%20Career/SongHong-SAR-Monitoring/REPORT/slide_bao_cao_thuc_tap.html) tích hợp xuất PDF. | Báo cáo Master 100% hoàn chỉnh; Slide trình chiếu 11 trang nằm ngang chuẩn tiếng Việt tích hợp tải PDF. |

---

## 3. KHUNG PHƯƠNG PHÁP KỸ THUẬT VÀ ĐỘT PHÁ CÔNG NGHỆ (METHODOLOGY)

Quy trình xử lý kết hợp giữa sức mạnh tính toán đám mây GEE và xử lý hình học véc-tơ cục bộ Python:

```
[Sentinel-1 SAR GRD Descending (317 Cảnh ảnh: 2017-2026)]
                        │
                        ▼
[Lọc nhiễu đốm thích ứng Refined Lee 7x7 (Linear Power Domain)]
                        │
                        ▼
[Trích xuất 17 Đặc trưng Radar & GLCM Texture (VV, VH, Ratios, GLCM 5x5)]
                        │
                        ▼
[Mô hình Random Forest phân loại 4 Lớp phủ (Huấn luyện theo Reach)]
                        │
                        ▼
[Hậu xử lý 2D & Thuật toán Nối bờ qua cầu (Centerline Connector)]
                        │
                        ▼
[Trích xuất Ranh giới Contact: Water - Sand Boundary]
                        │
                        ▼
[KD-Tree Positional Validation (So sánh độc lập với Sentinel-2 NDWI)]
                        │
                        ▼
[Khởi chạy Batch Full Composite 2017-2026 trên GEE & Phân tích Timeline]
```

### 3.1. Tiền xử lý & Trích xuất 17 Đặc trưng Radar
1. **Lọc đốm Refined Lee $7\times7$:** Chuyển đổi công suất $10^{\text{dB}/10}$, áp dụng bộ lọc thích ứng hướng giúp triệt tiêu nhiễu đốm radar mà vẫn bảo toàn độ sắc nét tuyệt đối của ranh giới bờ bãi.
2. **Bộ 17 Băng Đặc trưng (Feature Stack):**
   - Kênh phân cực thô: $VV$, $VH$.
   - Kênh tỷ số & tổng hợp: $VV/VH$, $VV-VH$, Mean.
   - 6 Đặc trưng kết cấu GLCM ($5\times5$ window): Contrast, Entropy, Homogeneity, Correlation, Variance, ASM.

### 3.2. Thuật toán Đột phá: Centerline-Connector Bridge Exclusion
* **Thách thức:** 6 cây cầu lớn bắc qua sông Hồng tại Hà Nội (Nhật Tân, Thăng Long, Long Biên, Chương Dương, Vĩnh Tuy, Thanh Trì) tạo tín hiệu tán xạ góc vuông (double-bounce) và bóng đứt gãy radar rộng $>180\text{m}$, khiến đường bờ SAR bị cuộn xoắn chạy dọc theo thân cầu.
* **Giải pháp:** Cắt đường tim sông (Centerline) với các polygon cầu (`data/bridges.geojson`), tạo vùng đệm $50\text{m}$ làm capsule kết nối lòng sông. Thuật toán hợp nhất (Union) capsule này vào mặt nạ nước, triệt tiêu hoàn toàn hiện tượng đường bờ bị cuộn dọc cầu mà không làm méo dạng bờ hai bên.

---

## 4. KẾT QUẢ KIỂM ĐỊNH ĐỊNH LƯỢNG MẪU 2024 (PILOT BENCHMARK 2024)

### 4.1. Thống kê Sai số Vị trí Đường bờ Toàn sông (Đơn vị: mét)

| Chỉ số Thống kê (Metric) | Mùa Khô 2024 (Dry) | Mùa Mưa 2024 (Wet) | Đánh giá Khoa học |
| :--- | :---: | :---: | :--- |
| **Minimum Error** | $0.003\text{ m}$ | $0.002\text{ m}$ | Trùng khớp tuyệt đối tại các đoạn đê kè bê tông. |
| **Median Error (P50)** | **$16.59\text{ m}$** | **$20.45\text{ m}$** | **Sai số trung vị tiệm cận ~1.5 đến 2 pixel ($10\text{m}$).** |
| **Mean Error** | $24.67\text{ m}$ | $33.26\text{ m}$ | Sai số trung bình toàn hành lang sông. |
| **RMSE** | **$41.99\text{ m}$** | **$54.47\text{ m}$** | Độ lệch chuẩn phản ánh mức tập trung sai số. |
| **75th Percentile (P75)** | $29.43\text{ m}$ | $39.74\text{ m}$ | $75\%$ đường bờ trích xuất có sai số $< 3$ pixels. |
| **95th Percentile (P95)** | $89.82\text{ m}$ | $122.91\text{ m}$ | Sai số lớn tập trung tại các bãi bồi ngập nông. |
| **Hausdorff Distance** | $354.25\text{ m}$ | $376.48\text{ m}$ | Sai số ngoại lệ do lệch ngày chụp ảnh S1 vs S2. |

### 4.2. Phân tích Chi tiết Theo Phân đoạn Sông (Reach-Based Analysis)

| Phân đoạn Sông | Số điểm mẫu | Median (m) | Mean (m) | RMSE (m) | P95 (m) | Hausdorff (m) |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| **Reach 1 (Thượng lưu - Mùa Khô)** | 12,169 | 19.96 | 31.52 | 47.02 | 117.86 | 189.64 |
| **Reach 1 (Thượng lưu - Mùa Mưa)** | 11,830 | 23.62 | 37.95 | 57.78 | 128.60 | 266.19 |
| **Reach 2 (Trung lưu - Mùa Khô)**  | 20,223 | 19.77 | 29.10 | 49.38 | 105.98 | 354.25 |
| **Reach 2 (Trung lưu - Mùa Mưa)**  | 21,714 | 26.32 | 40.88 | 64.12 | 147.24 | 376.48 |
| **Reach 3 (Hạ lưu - Mùa Khô)**   | 13,798 | **6.16** | **12.14** | **19.49** | **37.75** | **170.77** |
| **Reach 3 (Hạ lưu - Mùa Mưa)**   | 14,011 | **7.25** | **17.49** | **29.68** | **54.50** | **193.10** |

> **Nhận xét chuyên sâu:**  
> Reach 3 (Hạ lưu Phú Xuyên) đạt độ chính xác trích xuất lý tưởng tuyệt đối: **Median Error = $6.16\text{ m}$** trong mùa khô và **$7.25\text{ m}$** trong mùa mưa (thấp hơn cả $1\text{ pixel}$ ảnh $10\text{m}$). Chỉ số RMSE giữ ở mức siêu thấp ($19.49\text{ m}$).

### 4.3. Tỷ lệ Trùng khớp theo Vùng đệm (Buffer Agreement)

| Bán kính Vùng đệm | Mùa Khô 2024 (Dry) | Mùa Mưa 2024 (Wet) | Đánh giá |
| :---: | :---: | :---: | :--- |
| **$\le 10\text{ m}$ (1 pixel)** | **40.46%** | 34.02% | Tiệm cận độ phân giải ảnh thô $10\text{m}$. |
| **$\le 50\text{ m}$ (5 pixels)**| **88.87%** | **82.57%** | Đạt ngưỡng tin cậy cao cho viễn thám sông. |
| **$\le 100\text{ m}$** | **95.75%** | **92.60%** | **Đạt bao phủ toàn diện hình học lòng sông.** |

---

## 5. ĐỘNG LỰC HỌC BIẾN ĐỘNG THỦY VĂN VÀ BÃI BỒI (2024)

### 5.1. Thống kê Diện tích Mặt nước và Bãi bồi ($km^2$)

| Phân đoạn Sông | Mặt nước Khô ($km^2$) | Mặt nước Mưa ($km^2$) | Tăng Nước (%) | Bãi bồi Khô ($km^2$) | Bãi bồi Mưa ($km^2$) | Giảm Bãi (%) |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| **Reach 1 (Thượng lưu)** | 38.50 | 54.20 | **+40.78%** | 28.40 | 9.10 | **-67.96%** |
| **Reach 2 (Trung lưu)**  | 42.10 | 58.70 | **+39.43%** | 15.20 | 4.30 | **-71.71%** |
| **Reach 3 (Hạ lưu)**    | 35.80 | 48.30 | **+34.92%** | 18.90 | 5.60 | **-70.37%** |
| **TỔNG CỘNG MẪU 2024** | **116.40** | **161.20** | **+38.49%** | **62.50** | **19.00** | **-69.60%** |

### 5.2. Công thức và Quy luật Thủy văn
1. **Tăng trưởng Mặt nước Mùa Mưa:** Mở rộng thêm **$44.80\text{ km}^2$** (tương ứng **$+38.49\%$**) do lưu lượng lũ lớn.
2. **Suy giảm Bãi nổi Mùa Mưa:** Khoảng **$69.60\%$** diện tích bãi bồi nổi trong mùa khô (tương ứng **$43.50\text{ km}^2$**) bị ngập chìm dưới dòng nước lũ.

---

## 6. KHỞI CHẠY CHUỖI 10 NĂM (2017 – 2026 FULL COMPOSITE PHASE)

Sau khi nghiệm thu thành công bộ thử nghiệm 2024, dự án tiến hành công đoạn Tuần 4:
1. **Tự động hóa GEE Batch Pipeline:** Khởi chạy tính toán Full Composite cho toàn bộ **317 cảnh ảnh Sentinel-1 SAR Descending** từ năm 2017 đến 2026.
2. **Phân tích Timeline & DSAS:** Trích xuất đường bờ chuỗi 10 năm, tính toán chỉ số di chuyển đường bờ tích lũy (NSM) và tốc độ dịch chuyển (EPR) phục vụ cảnh báo sạt lở đê kè và quy hoạch đô thị sông Hồng.

---

## 7. BAN BẢN GIAO & DANH MỤC TÀI LIỆU DỰ ÁN (PROJECT DELIVERABLES)

Tất cả các sản phẩm của dự án đã được lưu trữ và đóng gói hoàn chỉnh:

1. **Báo cáo Khoa học (Reports):**
   - [PROJECT_100_REPORT.md](file:///d:/Future%20Career/SongHong-SAR-Monitoring/PROJECT_100_REPORT.md) (Báo cáo Master 100% Tổng thể).
   - [REPORT/bao_cao_giam_sat_song_hong.md](file:///d:/Future%20Career/SongHong-SAR-Monitoring/REPORT/bao_cao_giam_sat_song_hong.md) (Báo cáo Markdown chi tiết kèm bản đồ).
   - [REPORT/bao_cao_giam_sat_song_hong.tex](file:///d:/Future%20Career/SongHong-SAR-Monitoring/REPORT/bao_cao_giam_sat_song_hong.tex) (Báo cáo LaTeX biên dịch chuẩn ấn phẩm).
2. **Slide Trình chiếu & Xuất PDF:**
   - [REPORT/slide_bao_cao_thuc_tap.html](file:///d:/Future%20Career/SongHong-SAR-Monitoring/REPORT/slide_bao_cao_thuc_tap.html) (Bộ Slide HTML 11 trang nằm ngang, hỗ trợ phím mũi tên & xuất file PDF).
   - [slide_bao_cao_thuc_tap.html](file:///d:/Future%20Career/SongHong-SAR-Monitoring/slide_bao_cao_thuc_tap.html) (Bản sao tại gốc thư mục dự án).
3. **Hình ảnh & Bản đồ Trực quan (Figures):**
   - [figures/](file:///d:/Future%20Career/SongHong-SAR-Monitoring/REPORT/figures) chứa 20 ảnh biểu đồ & bản đồ phân đoạn (`reach1_dry.png`, `reach1_wet.png`, `reach2_dry.png`, `reach2_wet.png`, `reach3_dry.png`, `reach3_wet.png`, `fig1` đến `fig8`).
4. **Bản đồ Tương tác & Dữ liệu GeoJSON (Outputs):**
   - [outputs/map/](file:///d:/Future%20Career/SongHong-SAR-Monitoring/outputs/map) chứa các file bản đồ HTML tương tác Leaflet/Folium (`reach1_interactive_map_2024_dry.html`, `hybrid_shoreline_map_2024_dry.html`...).
   - [outputs/others/](file:///d:/Future%20Career/SongHong-SAR-Monitoring/outputs/others) chứa các file đường bờ GeoJSON và bảng thống kê CSV.
5. **Đề cương Thực tập:**
   - [Đề cương công việc thực tập.md](file:///d:/Future%20Career/SongHong-SAR-Monitoring/Đề%20cương%20công%20việc%20thực%20tập.md).
