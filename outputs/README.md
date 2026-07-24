# Thư mục Kết quả Đầu ra (Pipeline Outputs & Visualizations)

Thư mục này chứa toàn bộ các sản phẩm kết quả trích xuất vector, bản đồ tương tác HTML và các báo cáo định lượng kiểm chứng của dự án.

## 📁 Cấu trúc Thư mục Kết quả

```
outputs/
├── reach1_s1_shoreline_2024_*.geojson   # Vector đường bờ GeoJSON Reach 1 (Dry/Wet)
├── reach2_s1_shoreline_2024_*.geojson   # Vector đường bờ GeoJSON Reach 2 (Dry/Wet)
├── reach3_s1_shoreline_2024_*.geojson   # Vector đường bờ GeoJSON Reach 3 (Dry/Wet)
├── reach1_s2_ref_2024_*.geojson         # Vector tham chiếu S2 Reach 1
├── reach2_s2_ref_2024_*.geojson         # Vector tham chiếu S2 Reach 2
├── reach3_s2_ref_2024_*.geojson         # Vector tham chiếu S2 Reach 3
├── map/                                 # Bản đồ tương tác Folium HTML
│   ├── hybrid_shoreline_map_2024_dry.html  # Bản đồ Master Hybrid toàn sông (Mùa khô)
│   ├── hybrid_shoreline_map_2024_wet.html  # Bản đồ Master Hybrid toàn sông (Mùa mưa)
│   └── reach*_interactive_map_2024_*.html  # Bản đồ tương tác chi tiết từng Reach
└── others/                              # Báo cáo thống kê CSV & log kiểm chứng
```

## 🎨 Phân cấp Màu Đánh giá Sai số Vị trí (3-Tier Rating Standard)

Trình tương tác HTML hiển thị mức độ sai số theo chuẩn quốc tế:
- 🟢 **Xanh lá (Good / Tốt):** Sai số $< 30\text{m}$ ($< 3\text{ pixels}$) — Chuẩn công bố khoa học.
- 🟡 **Vàng (Moderate / Trung bình):** Sai số $30\text{m} - 70\text{m}$ ($3 - 7\text{ pixels}$) — Chuẩn giám sát quy mô vùng.
- 🔴 **Đỏ (Poor / Kém):** Sai số $> 70\text{m}$ ($> 7\text{ pixels}$) — Khu vực nhiễu hoặc sai số cục bộ.
