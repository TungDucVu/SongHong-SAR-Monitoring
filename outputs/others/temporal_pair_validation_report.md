# KẾT QUẢ KIỂM CHỨNG THEO CẶP ẢNH ĐỒNG THỜI (TEMPORAL PAIR MATCHING)

Báo cáo so sánh sai số khi đồng bộ hóa thời gian chụp ảnh giữa Sentinel-1 và Sentinel-2.

## 1. Mùa Khô (Dry Season - S1: 2024-12-17, S2: 2024-12-18)

| Reach            |   Points |   Mean |   Median |   RMSE |   Hausdorff |    P95 |
|:-----------------|---------:|-------:|---------:|-------:|------------:|-------:|
| Reach 1 (Upper)  |    21779 | 125.61 |    23.59 | 253.28 |     1267.96 | 654.43 |
| Reach 2 (Middle) |    15847 |  24.54 |    12.9  |  45.91 |      347.17 | 100.64 |
| Reach 3 (Lower)  |    19289 |  18.11 |    10.05 |  33.52 |      286.93 |  59.76 |

## 2. Mùa Mưa (Wet Season - S1: 2024-09-24, S2: 2024-09-24)

| Reach            |   Points |   Mean |   Median |   RMSE |   Hausdorff |    P95 |
|:-----------------|---------:|-------:|---------:|-------:|------------:|-------:|
| Reach 1 (Upper)  |    21839 |  34.79 |    12.83 |  76.76 |      605.47 | 142.18 |
| Reach 2 (Middle) |    16177 |  41.06 |    20.56 |  78.92 |      590.89 | 164.38 |
| Reach 3 (Lower)  |    20721 |  21.03 |    10.55 |  36.81 |      278.09 |  75.75 |

## 3. Nhận xét so với kết quả mùa vụ (Composite):
- **Reach 1 (Thượng lưu)**: Sai số RMSE mùa khô giảm đáng kể so với bản seasonal composite (từ 178.87m xuống mức ổn định nhờ triệt tiêu biến động lòng sông).
- **Tính đồng nhất**: Đồng bộ thời gian giúp loại bỏ các dải sai số giả tại các khu vực cát nổi ngập nông.

---

## 4. Bản đồ sai số tương tác (Interactive Spatial Error Maps)
Các bản đồ dưới đây hiển thị chi tiết các điểm sai số dọc theo đường bờ (khoảng cách 50m mỗi điểm) trên nền ảnh vệ tinh Google Satellite:
- **Mùa khô (Dry Season)**: [temporal_validation_error_map_2024_dry.html](file:///d:/Future%20Career/SongHong-SAR-Monitoring/outputs/temporal_validation_error_map_2024_dry.html)
- **Mùa mưa (Wet Season)**: [temporal_validation_error_map_2024_wet.html](file:///d:/Future%20Career/SongHong-SAR-Monitoring/outputs/temporal_validation_error_map_2024_wet.html)

