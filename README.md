# SongHong SAR Monitoring 🛰️

> **Giám sát biến động đường bờ và bãi bồi Sông Hồng tại Hà Nội bằng dữ liệu Sentinel-1 SAR**

[![GEE](https://img.shields.io/badge/Google%20Earth%20Engine-4285F4?logo=google&logoColor=white)](https://earthengine.google.com)
[![Sentinel-1](https://img.shields.io/badge/Sentinel--1%20SAR-003087?logo=esa&logoColor=white)](https://sentinel.esa.int/web/sentinel/missions/sentinel-1)
[![Python](https://img.shields.io/badge/Python-3.9+-3776AB?logo=python&logoColor=white)](https://python.org)

---

## 📋 Giới thiệu

Dự án xây dựng quy trình **bán tự động** giám sát biến động mặt nước, đường bờ và bãi bồi Sông Hồng đoạn qua Hà Nội, sử dụng ảnh vệ tinh SAR Sentinel-1 từ năm 2015 đến 2024.

**Người thực hiện:** Vũ Đức Tùng | **Tháng:** 07/2026

## 🎯 Mục tiêu

- Xây dựng quy trình tự động phân loại **Mặt nước / Bãi bồi / Đất** từ SAR
- Phát triển mô hình **Random Forest** trên Google Earth Engine
- Phân tích biến động **10 năm** (2015–2024) tại các điểm trọng điểm: Long Biên, Nhật Tân, Vĩnh Tuy
- Tương quan kết quả với dữ liệu **thủy văn**

## 📁 Cấu trúc dự án

```
SongHong-SAR-Monitoring/
├── aoi/
│   ├── song_hong_aoi.geojson     # Vùng nghiên cứu (AOI)
│   └── README.md
├── scripts/
│   ├── 00_environment_check.py   # Kiểm tra GEE & AOI
│   ├── 01_data_collection.py     # Thu thập Sentinel-1 (2015–2024)
│   ├── 02_preprocessing.py       # Tiền xử lý & đặc trưng SAR
│   ├── 03_visualization_check.py # Kiểm tra trực quan
│   └── 04_export_sample.py       # Export GeoTIFF mẫu
├── docs/
│   └── week1_notes.md            # Ghi chú kỹ thuật
├── outputs/                      # Kết quả (không commit)
└── Đề cương công việc thực tập.md
```

## ⚡ Bắt đầu nhanh

### 1. Cài đặt thư viện

```bash
pip install earthengine-api geemap
earthengine authenticate
```

### 2. Chạy theo thứ tự

```bash
# Kiểm tra môi trường GEE
python scripts/00_environment_check.py

# Thống kê dữ liệu Sentinel-1 (2015–2024)
python scripts/01_data_collection.py

# Tiền xử lý và tính đặc trưng
python scripts/02_preprocessing.py

# Kiểm tra trực quan
python scripts/03_visualization_check.py

# Export GeoTIFF mẫu lên Google Drive
python scripts/04_export_sample.py
```

## 🛰️ Dữ liệu

| Nguồn | Dataset | Giai đoạn |
|---|---|---|
| Sentinel-1 | `COPERNICUS/S1_GRD` | 2015–2024 |
| Sentinel-2 | `COPERNICUS/S2_SR_HARMONIZED` | Đối chiếu |
| GEE Project | `crested-library-500309-i2` | — |

## 📊 Kết quả mong đợi

- Chuỗi bản đồ phân loại (Mặt nước / Bãi bồi / Đất) hàng tháng 2015–2024
- Biểu đồ biến động diện tích theo thời gian
- Độ chính xác phân loại > 85% (OA)

## 📅 Tiến độ

| Tuần | Hạng mục | Deadline | Trạng thái |
|---|---|---|---|
| Tuần 1 | Chuẩn bị dữ liệu & GEE | 07/07/2026 | 🔄 Đang thực hiện |
| Tuần 2 | Mô hình Random Forest | 14/07/2026 | ⏳ |
| Tuần 3 | Tự động hóa chuỗi thời gian | 21/07/2026 | ⏳ |
| Tuần 4 | Phân tích & Báo cáo | 31/07/2026 | ⏳ |
