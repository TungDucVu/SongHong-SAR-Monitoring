# SongHong SAR Monitoring 🛰️🌊

> **Giám sát biến động đường bờ và bãi bồi Sông Hồng tại Hà Nội bằng dữ liệu Sentinel-1 SAR (2017 – 2026)**
> 
> *An end-to-end, publication-grade, semi-automated pipeline for monitoring river dynamics, sandbar morphodynamics, and shoreline migration under seasonal discharge variations using Google Earth Engine & Python Machine Learning.*

[![GEE](https://img.shields.io/badge/Google%20Earth%20Engine-4285F4?logo=google&logoColor=white)](https://earthengine.google.com)
[![Sentinel-1](https://img.shields.io/badge/Sentinel--1%20SAR-003087?logo=esa&logoColor=white)](https://sentinel.esa.int/web/sentinel/missions/sentinel-1)
[![Python](https://img.shields.io/badge/Python-3.10+-3776AB?logo=python&logoColor=white)](https://python.org)
[![VNSC](https://img.shields.io/badge/Affiliation-Vietnam%20Space%20Center-red)](https://vnsc.org.vn)

---

## 📋 Giới thiệu Dự án

Dự án **SongHong SAR Monitoring** được phát triển tại **Trung tâm Vũ trụ Việt Nam (VNSC)** (Phiên bản `v1.0-OptionA-Production`).

Hệ thống thiết lập một quy trình viễn thám bán tự động trên nền tảng **Google Earth Engine (GEE API)** và **Python local** nhằm giám sát diện tích mặt nước, lòng dẫn hoạt động và động lực học bãi bồi (sandbars) trên đoạn sông Hồng chảy qua Hà Nội dài **171.84 km** (diện tích hành lang $343.68\text{ km}^2$, từ Sơn Tây đến Phú Xuyên).

---

## 📊 Kết quả Thử nghiệm Định lượng Mẫu 2024 (Pilot Benchmark)

> [!IMPORTANT]
> tất cả kết quả thống kê định lượng hiện tại đại diện cho **bước nghiệm thu thử nghiệm định hình mô hình trên bộ mẫu năm 2024**. Xem chi tiết đường dẫn từng file kết quả tại [EXAMPLE.md](./EXAMPLE.md).

### 1. Đánh giá Sai số Vị trí Đường bờ năm 2024 (Tối ưu Option A)
* **Sai số Trung vị toàn sông (Median P50):** Đạt **$14.10\text{ m}$** (Mùa khô) và **$18.47\text{ m}$** (Mùa mưa) — tiệm cận mức sai số $1.5\text{ pixel}$ ($10\text{m}$).
* **Độ chính xác cao nhất tại Reach 3 (Hạ lưu - Phú Xuyên):** Sai số trung vị đạt mức lý tưởng **$6.16\text{ m}$** trong mùa khô ($< 1\text{ pixel}$), RMSE **$18.72\text{ m}$** (Dry) và **$25.72\text{ m}$** (Wet) — **Đạt chuẩn công bố khoa học (High Precision)**.
* **Tỷ lệ trùng khớp Vùng đệm (Buffer Agreement):** Đạt **$91.24\%$** trong khoảng đệm $50\text{ m}$ và **$97.10\%$** trong khoảng đệm $100\text{ m}$ (Mùa khô 2024).

![Hình 1: So sánh Sai số Vị trí Đường bờ theo Phân đoạn Sông Hồng](./outputs/REPORT/figures/fig1_reach_error_comparison.png)

![Hình 2: Đường cong Tỷ lệ trùng khớp theo Khoảng đệm](./outputs/REPORT/figures/fig2_buffer_accuracy_curve.png)

### 2. Động lực học Biến động Diện tích
* **Mặt nước sông:** Mùa mưa diện tích mặt nước mở rộng thêm **$44.80\text{ km}^2$** (tương ứng tăng **$+38.49\%$**) trên toàn hành lang Hà Nội.
* **Bãi bồi (Sandbars):** Tổng diện tích bãi nổi mùa khô đạt **$62.50\text{ km}^2$**. Khi chuyển sang mùa mưa, **$69.60\%$** diện tích bãi bồi bị ngập nước (chỉ còn lại $19.00\text{ km}^2$).

![Hình 5: Biến động Diện tích Mặt nước và Bãi bồi](./outputs/REPORT/figures/fig5_water_sand_area_dynamics.png)

---

## 🛠️ Đổi mới Kỹ thuật Cốt lõi (Key Innovations)

1. **Multi-temporal 10th Percentile Composite (P10):** Triệt tiêu sóng nhám bề mặt và hiện tượng tán xạ đục do phù sa mùa mưa.
2. **Fast Focal Neighborhood Textures:** Tính toán nhanh 6 chỉ số kết cấu không gian ($3\times3$) trực tiếp trên GEE Server Side.
3. **Bridge Piercing (Nối bờ qua 6 cầu lớn):** Loại bỏ hoàn toàn hiệu ứng bóng đứt gãy radar dưới gầm 6 cầu bắc qua sông Hồng.
4. **Phân đoạn 3 Reach Thủy văn:** Chia hành lang sông Hồng thành 3 mô hình Random Forest phân đoạn local: Reach 1 (Thượng lưu Sơn Tây), Reach 2 (Trung lưu Nội đô Hà Nội), và Reach 3 (Hạ lưu meander Phú Xuyên).

---

## 📈 Phân Tích Chuỗi Thời Gian & Biến Động Đường Bờ (2017 – 2026)

Hệ thống đã mở rộng và trích xuất thành công trọn bộ **20 mùa (2017 – 2026, 10 năm × 2 mùa Dry & Wet)** trên toàn bộ hành lang 171.84 km Sông Hồng qua Hà Nội.

### 1. Biểu Đồ Phân Tích Động Lực Học Chuỗi Thời Gian
![Hình 1: Biến Động Diện Tích Mặt Nước Sông Hồng 2017-2026](./outputs/REPORT/figures/fig_multiyear_water_area_trend.png)

* **Biến động Diện tích Mặt nước ($km^2$):** Diện tích mặt nước mùa khô duy trì ổn định từ $63.84\text{ km}^2 - 71.93\text{ km}^2$. Mùa mưa dâng rộng từ $69.19\text{ km}^2 - 84.91\text{ km}^2$. Hai đỉnh lũ cực đoan được ghi nhận vào năm **2017 ($84.91\text{ km}^2$)** và **Siêu bão Yagi Tháng 9/2024 ($79.07\text{ km}^2$)**.

![Hình 2: Xu Hướng Sai Số Vị Trí Đường Bờ 2017-2026](./outputs/REPORT/figures/fig_multiyear_positional_accuracy_trend.png)

* **Sai số Vị trí KD-Tree (vs. S2 NDWI):** Median P50 duy trì ổn định ở mức xuất sắc từ **$7.41\text{m} - 11.81\text{m}$** ($< 1.2\text{ pixels}$). RMSE trung bình toàn sông dao động từ **$35.58\text{m} - 56.08\text{m}$** (tiệm cận chuẩn Tốt / Regional Scale).

![Hình 3: Chiều Dài Đường Bờ Vector & Cù Lao Bãi Nổi](./outputs/REPORT/figures/fig_multiyear_shoreline_length_and_islands.png)

---

## 🌍 Các Nhân Tố Tác Động Bên Ngoài Đến Sự Biến Thủy & Đường Bờ

Diễn biến đường bờ và diện tích lòng sông Hồng giai đoạn 2017 – 2026 chịu sự chi phối mạnh mẽ của 4 nhóm tác động nhân tạo và tự nhiên:

1. **Điều tiết Thủy điện & Bẫy Phù sa Thượng nguồn:**
   - Hệ thống các hồ chứa lớn (Sơn La, Hòa Bình, Tuyên Quang, Thác Bà) giữ lại tới $70\% - 85\%$ lượng bồi tích phù sa thô, gây nên hiện tượng **"nước đói phù sa" (Clear-water erosion)**. Dòng nước trong xói mạnh vào lòng dẫn và chân đê vùng hạ lưu.
2. **Khai Thác Cát & Hạ Thấp Lòng Dẫn Sông Hồng:**
   - Hoạt động khai thác cát quy mô lớn kéo dài nhiều năm đã làm **hạ thấp lòng dẫn sông Hồng từ $1.5\text{m} - 3.5\text{m}$**. Hệ quả làm tụt mực nước mùa khô, ngầm hóa các bãi sỏi nông và làm gia tăng nguy cơ sạt lở chân bờ ở Reach 1 & Reach 3.
3. **Biến Đổi Khí Hậu & Thiên Tai Cực Đoan (Lũ Lịch Sử & Siêu Bão):**
   - Đợt lũ mở ngập lớn năm 2017 ($84.91\text{ km}^2$) và Siêu bão Yagi tháng 9/2024 ($79.07\text{ km}^2$) tạo áp lực thủy động lực học lớn, làm dịch chuyển bờ lõm khúc uốn Sơn Tây từ $15 - 35\text{m}$ và nhấn chìm tạm thời $80\%$ các cù lao bãi nổi.
4. **Kiên Cố Hóa Đô Thị & Bờ Kè Nhân Tạo (Reach 2):**
   - Tuyến đê và bờ kè bê tông bảo vệ nội đô Hà Nội (Reach 2) giữ vị trí bờ sông gần như cố định ($\le 10\text{m}$ dịch chuyển trong 10 năm), đẩy năng lượng dòng chảy tập trung xói bồi tự nhiên sang 2 phân đoạn nông nghiệp Reach 1 và Reach 3.

---

## 📁 Cấu Trúc Thư Mục Dự Án Tối Ưu

```
SongHong-SAR-Monitoring/
├── main.py                             # ⚡ Bộ điều khiển CLI tập trung (Quickstart Runner)
├── WALKTHROUGH.md                      # 📖 Hướng dẫn vận hành & tùy biến mã nguồn chi tiết
├── README.md                           # 📄 Hướng dẫn tổng quan dự án
├── main_workflow/                      # 🚀 Kịch bản chạy mô hình theo Reach (1, 2, 3)
├── scripts/                            # 🛠️ Script vẽ bản đồ Master, trích xuất & vẽ biểu đồ 10 năm
├── src/                                # 🧩 Mã nguồn Python Core Package (collection, shoreline, v.v.)
├── aoi/                                # 📐 Dữ liệu không gian GeoJSON chính thức
├── data/                               # 💾 Cache dữ liệu ground truth Sentinel-2 MNDWI (2017-2026)
└── outputs/                            # 📦 Kết quả đầu ra tập trung
    ├── REPORT/                         # 📄 Báo cáo khoa học (MD/TeX), Slides HTML & Hình ảnh PNG
    ├── {year}/                         # 📁 Thư mục từng năm (2017 đến 2026)
    │   ├── {year}_dry/                 # 🗺️ GeoJSON, HTML QC Map, Error Map, PNG, CSV Mùa khô
    │   └── {year}_wet/                 # 🗺️ GeoJSON, HTML QC Map, Error Map, PNG, CSV Mùa mưa
    └── others/                         # 📐 Master GeoJSON 10 năm, Master Folium Map & Metadata
```

---

## ⚡ Bắt Đầu Nhanh (Quickstart Lệnh CLI)

### 1. Cài đặt Môi trường Python & Xác thực GEE
```bash
pip install earthengine-api geemap geopandas shapely rasterio folium scikit-learn matplotlib seaborn networkx pandas geedim
earthengine authenticate
```

### 2. Khởi chạy Mô hình Ngay lập tức
```bash
# Chạy toàn bộ 3 Reach cho 1 năm mẫu và tạo bản đồ Master Hybrid:
python main.py --reach all

# Khởi chạy tự động trích xuất chuỗi thời gian 10 năm (2017-2026):
python main.py --full-composite

# Ghép nối Master GeoJSON & Vẽ bản đồ tương tác Multi-Temporal 10 năm:
python scripts/aggregate_multiyear_shoreline.py

# Vẽ lại các biểu đồ phân tích biến động 10 năm:
python scripts/plot_multiyear_trends.py
```

### 3. Xem Báo Cáo Phân Tích Khoa Học Chuyên Sâu
Mở bản báo cáo phân tích khoa học chuyên sâu giải thích thuật toán, sai số và biến động 10 năm tại [outputs/REPORT/bao_cao_chuyen_sau_thuat_toan_va_bien_dong_2017_2026.md](./outputs/REPORT/bao_cao_chuyen_sau_thuat_toan_va_bien_dong_2017_2026.md).


