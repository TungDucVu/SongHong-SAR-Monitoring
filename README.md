# SongHong SAR Monitoring 🛰️

> **Giám sát biến động đường bờ và bãi bồi Sông Hồng tại Hà Nội bằng dữ liệu Sentinel-1 SAR**

[![GEE](https://img.shields.io/badge/Google%20Earth%20Engine-4285F4?logo=google&logoColor=white)](https://earthengine.google.com)
[![Sentinel-1](https://img.shields.io/badge/Sentinel--1%20SAR-003087?logo=esa&logoColor=white)](https://sentinel.esa.int/web/sentinel/missions/sentinel-1)
[![Python](https://img.shields.io/badge/Python-3.9+-3776AB?logo=python&logoColor=white)](https://python.org)

---

## 📋 Giới thiệu

Dự án này xây dựng quy trình **bán tự động** giám sát biến động mặt nước, đường bờ và các bãi bồi Sông Hồng đoạn qua Hà Nội (từ Sơn Tây đến Phú Xuyên, độ dài ~80km), sử dụng chuỗi ảnh vệ tinh radar Sentinel-1 SAR trong giai đoạn 10 năm (2015–2024).

Dự án được thiết kế theo cấu trúc **mô-đun hóa (modular structure)** chuyên nghiệp, phân tách rõ ràng cấu hình, thuật toán xử lý ảnh, truy vấn dữ liệu và các hàm tiện ích, kết hợp với giao diện trực quan hóa Jupyter Notebook.

---

## 📁 Cấu trúc thư mục dự án

```
SongHong-SAR-Monitoring/
├── aoi/
│   ├── song_hong_aoi.geojson     # Vùng nghiên cứu (AOI) dạng GeoJSON
│   └── README.md                 # Tài liệu hướng dẫn AOI
├── src/                          # Thư mục mã nguồn chính (Python Package)
│   ├── __init__.py
│   ├── config.py                 # Cấu hình dự án (Project ID, orbits, thresholds, paths)
│   ├── aoi.py                    # Tiện ích liên quan AOI và tự động upload GEE Asset
│   ├── preprocessing.py          # Bộ lọc Speckle (Refined Lee) & Tính đặc trưng (VV, VH, Ratio)
│   ├── collection.py             # Truy vấn, thống kê, tạo monthly/annual composites
│   └── utils.py                  # Xuất báo cáo CSV/JSON, export GeoTIFF, lưu map HTML
├── docs/
│   ├── report_phase1_phase2.md   # Báo cáo tổng hợp Phase 1 & Phase 2 (Đầy đủ)
│   └── report_phase3.md          # Báo cáo tổng hợp Phase 3 (Huấn luyện RF & Hậu xử lý đường bờ)
├── outputs/                      # Thư mục chứa kết quả cục bộ (được bỏ qua bởi git)
├── week1_pipeline.ipynb          # Jupyter Notebook tích hợp chạy toàn bộ quy trình Tuần 1
├── week2_pipeline.ipynb          # Jupyter Notebook tích hợp chạy toàn bộ quy trình Tuần 2
├── .gitignore                    # Quản lý các file không commit
└── Đề cương công việc thực tập.md # Đề cương thực tập chi tiết
```

---

## ⚡ Bắt đầu nhanh

### 1. Cài đặt thư viện
Cài đặt các thư viện cần thiết bằng pip:
```bash
pip install earthengine-api geemap jupyter numpy
```

### 2. Xác thực Google Earth Engine
```bash
earthengine authenticate
```

### 3. Chạy quy trình
Khởi chạy Jupyter Notebook hoặc mở file trong VS Code:
```bash
jupyter notebook week1_pipeline.ipynb
```
Chạy lần lượt các cell để thực thi:
1. **Thiết lập & Nạp AOI:** Kết nối GEE project `crested-library-500309-i2` và tự động đồng bộ AOI GeoJSON lên Assets.
2. **Kiểm tra Metadata S1:** In metadata và kiểm tra độ phân giải của ảnh mẫu.
3. **Phân tích độ phủ:** Thống kê số lượng ảnh theo năm/tháng (thu được 317 ảnh) và xuất báo cáo CSV.
4. **Tiền xử lý & Kiểm chứng tự động:** Lọc speckle noise (Refined Lee) và tính đặc trưng. Kiểm chứng trị số backscatter tại điểm nước/đất.
5. **Trực quan hóa:** Hiển thị và lưu bản đồ HTML so sánh mùa khô/lũ.
6. **Export GeoTIFF:** Gửi các task xuất ảnh composite độ phân giải 10m lên Google Drive.

---

## 🛰️ Dữ liệu & Kết quả kiểm chứng (Tuần 1)

- **Tổng số lượng ảnh S1:** 317 ảnh (Không có gap dữ liệu hàng năm).
- **Trị số VV Kiểm chứng (Tháng 1/2024):**
  - Mặt nước: **-18.70 dB** (Ngưỡng lý thuyết: < -15 dB) -> **ĐẠT** ✅
  - Đất liền: **-1.54 dB** (Ngưỡng lý thuyết: > -10 dB) -> **ĐẠT** ✅

---

## 📅 Tiến độ tổng thể

| Tuần | Hạng mục công việc | Deadline | Trạng thái |
|---|---|---|---|
| **Tuần 1** | **Chuẩn bị dữ liệu & Thiết lập môi trường** | Ngày thứ 7 | ✅ Hoàn thành |
| **Tuần 2** | **Xây dựng mô hình Machine Learning (Random Forest)** | Ngày thứ 14 | ✅ Hoàn thành |
| **Tuần 3** | **Đánh giá độ chính xác & Hậu xử lý Đường bờ** | Ngày thứ 21 | ✅ Hoàn thành |
| **Tuần 4** | **Phân tích hình thái thời gian, đối chiếu thủy văn & Báo cáo** | Ngày cuối tháng | ⏳ Chờ thực hiện |
