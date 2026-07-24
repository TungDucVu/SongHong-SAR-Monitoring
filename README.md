# SongHong SAR Monitoring 🛰️🌊

> **Giám sát biến động đường bờ và bãi bồi Sông Hồng tại Hà Nội bằng dữ liệu Sentinel-1 SAR (2017 – 2026)**
> 
> *An end-to-end, publication-grade, semi-automated pipeline for monitoring river dynamics, sandbar morphodynamics, and shoreline migration under seasonal discharge variations.*

[![GEE](https://img.shields.io/badge/Google%20Earth%20Engine-4285F4?logo=google&logoColor=white)](https://earthengine.google.com)
[![Sentinel-1](https://img.shields.io/badge/Sentinel--1%20SAR-003087?logo=esa&logoColor=white)](https://sentinel.esa.int/web/sentinel/missions/sentinel-1)
[![Python](https://img.shields.io/badge/Python-3.10+-3776AB?logo=python&logoColor=white)](https://python.org)
[![VNSC](https://img.shields.io/badge/Affiliation-Vietnam%20Space%20Center-red)](https://vnsc.org.vn)

---

## 📋 Giới thiệu Dự án

Dự án **SongHong SAR Monitoring** được phát triển tại **Trung tâm Vũ trụ Việt Nam (VNSC)** (Tháng 7/2026).

Hệ thống thiết lập một quy trình viễn thám bán tự động trên nền tảng **Google Earth Engine (GEE)** và **Python local** nhằm giám sát diện tích mặt nước, lòng dẫn hoạt động và động lực học bãi bồi (sandbars) trên đoạn sông Hồng chảy qua Hà Nội dài **171.84 km** (diện tích hành lang $362.83\text{ km}^2$, từ Sơn Tây đến Phú Xuyên).

---

## 📊 Kết quả Thử nghiệm Định lượng Mẫu 2024 (Pilot Benchmark)

> [!IMPORTANT]
> **Lưu ý:** Tất cả các kết quả thống kê định lượng hiện tại đại diện cho **bước nghiệm thu thử nghiệm định hình mô hình trên bộ mẫu năm 2024**. Công đoạn kế tiếp sẽ khởi chạy tự động toàn chuỗi 10 năm (2017–2026).

### 1. Đánh giá Sai số Vị trí Đường bờ năm 2024 (Tối ưu Option A)
* **Sai số Trung vị toàn sông (Median P50):** Đạt **$14.10\text{ m}$** (Mùa khô) và **$18.47\text{ m}$** (Mùa mưa) — tiệm cận mức sai số $1.5\text{ pixel}$ ($10\text{m}$).
* **Độ chính xác cao nhất tại Reach 3 (Hạ lưu - Phú Xuyên):** Sai số trung vị đạt mức lý tưởng **$6.16\text{ m}$** trong mùa khô ($< 1\text{ pixel}$), RMSE **$18.72\text{ m}$** (Dry) và **$25.72\text{ m}$** (Wet).
* **Tỷ lệ trùng khớp Vùng đệm (Buffer Agreement):** Đạt **$91.24\%$** trong khoảng đệm $50\text{ m}$ và **$97.10\%$** trong khoảng đệm $100\text{ m}$ (Mùa khô 2024).

![Hình 1: So sánh Sai số Vị trí Đường bờ theo Phân đoạn Sông Hồng](./REPORT/figures/fig1_reach_error_comparison.png)

![Hình 2: Đường cong Tỷ lệ trùng khớp theo Khoảng đệm](./REPORT/figures/fig2_buffer_accuracy_curve.png)

### 2. Động lực học Biến động Diện tích
* **Mặt nước sông:** Mùa mưa diện tích mặt nước mở rộng thêm **$44.80\text{ km}^2$** (tương ứng tăng **$+38.49\%$**) trên toàn hành lang Hà Nội.
* **Bãi bồi (Sandbars):** Tổng diện tích bãi nổi mùa khô đạt **$62.50\text{ km}^2$**. Khi chuyển sang mùa mưa, **$69.60\%$** diện tích bãi bồi bị ngập nước (chỉ còn lại $19.00\text{ km}^2$).

![Hình 5: Biến động Diện tích Mặt nước và Bãi bồi](./REPORT/figures/fig5_water_sand_area_dynamics.png)

---

## 🛠️ Đổi mới Kỹ thuật Cốt lõi (Key Innovations)

1. **Centerline Connector Bridge Exclusion:** Thuật toán tạo capsule đệm kết nối lòng sông dựa trên tim sông, loại bỏ hoàn toàn bóng đứt gãy radar dưới gầm 6 cầu lớn (Nhật Tân, Thăng Long, Long Biên, Chương Dương, Vĩnh Tuy, Thanh Trì).
2. **17-Band Feature Stack:** Kết hợp kênh phân cực thô ($VV, VH$), các tỷ số phân cực ($VV/VH, VV-VH, Mean$), và 6 chỉ số kết cấu không gian GLCM ($5\times5$).
3. **Phân đoạn 3 Reach Thủy văn:** Chia hành lang sông Hồng thành 3 mô hình Random Forest độc lập: Reach 1 (Thượng lưu), Reach 2 (Trung lưu đô thị), và Reach 3 (Hạ lưu meander).

---

## 📁 Cấu trúc Thư mục Dự án

```
SongHong-SAR-Monitoring/
├── REPORT/                             # Thư mục Báo cáo Khoa học Xuất bản
│   ├── bao_cao_giam_sat_song_hong.md   # Bản báo cáo Markdown khoa học chi tiết
│   ├── bao_cao_giam_sat_song_hong.tex  # Bản báo cáo LaTeX chuẩn ấn phẩm xuất bản
│   ├── figures/                        # Thư mục chứa 5 biểu đồ đồ họa sắc nét (PNG)
│   │   ├── fig1_reach_error_comparison.png
│   │   ├── fig2_buffer_accuracy_curve.png
│   │   ├── fig3_temporal_s1_coverage.png
│   │   ├── fig4_error_cdf_percentiles.png
│   │   └── fig5_water_sand_area_dynamics.png
│   ├── Arifin_2025_IOP_Conf.pdf        # Bài báo tham chiếu IOP
│   └── coastlinechangesdetection.pdf   # Bài báo tham chiếu VN J. Hydrometeorol
├── aoi/                                # Vùng nghiên cứu GeoJSON (Reach 1, 2, 3)
├── src/                                # Thư mục mã nguồn chính (Python Package)
│   ├── config.py                       # Cấu hình dự án & tham số GEE
│   ├── aoi.py                          # Tiện ích AOI & upload tự động GEE Asset
│   ├── preprocessing.py                # Bộ lọc Refined Lee 7x7 & tính đặc trưng
│   ├── collection.py                   # Truy vấn Sentinel-1 & tạo composite
│   └── utils.py                        # Hàm tiện ích hình học & export
├── outputs/                            # Kết quả trích xuất GeoJSON/CSV/HTML
├── week1_pipeline.ipynb                # Notebook tích hợp Tuần 1
├── week2_pipeline.ipynb                # Notebook tích hợp Tuần 2
├── project_summary_report.md           # Báo cáo tổng quan dự án
└── Đề cương công việc thực tập.md       # Đề cương thực tập chi tiết
```

---

## 📅 Lộ trình Tiến độ Tổng thể

| Tuần | Hạng mục Công việc | Kết quả Đạt được | Trạng thái |
| :--- | :--- | :--- | :---: |
| **Tuần 1** | **Chuẩn bị Dữ liệu & Tiền xử lý** | Thu thập 317 cảnh ảnh S1 (2017–2026), lọc speckle Refined Lee 7x7 | ✅ Hoàn thành |
| **Tuần 2** | **Xây dựng Mô hình Machine Learning** | Huấn luyện 3 mô hình Random Forest cho 3 Reach, trích xuất đặc trưng GLCM | ✅ Hoàn thành |
| **Tuần 3** | **Tự động hóa & Kiểm định Định lượng** | Thuật toán Bridge Exclusion nối bờ qua cầu, kiểm định KD-Tree mẫu 2024 | ✅ Hoàn thành |
| **Tuần 4** | **Chạy Chuỗi Thời gian 10 năm & Báo cáo** | Khởi chạy tự động 2017–2026 trên GEE, phân tích timeline & báo cáo | 🔄 Đang triển khai |

---

## ⚡ Bắt đầu Nhanh

### 1. Cài đặt Môi trường Python
```bash
pip install earthengine-api geemap geopandas shapely matplotlib seaborn networkx pandas
```

### 2. Xác thực Google Earth Engine
```bash
earthengine authenticate
```

### 3. Đọc Báo cáo Phân tích Khoa học
Mở bản báo cáo phân tích khoa học chi tiết kèm biểu đồ trực quan tại [REPORT/bao_cao_giam_sat_song_hong.md](./REPORT/bao_cao_giam_sat_song_hong.md) hoặc biên dịch bản LaTeX tại [REPORT/bao_cao_giam_sat_song_hong.tex](./REPORT/bao_cao_giam_sat_song_hong.tex).
