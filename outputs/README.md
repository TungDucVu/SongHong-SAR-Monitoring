# Thư mục Kết quả Đầu ra (Pipeline Outputs & Visualizations)

Thư mục này quản lý tập trung toàn bộ các sản phẩm kết quả trích xuất vector, bản đồ tương tác HTML, báo cáo ấn phẩm khoa học và các file thống kê kiểm chứng của dự án.

## 📁 Cấu trúc Thư mục

```
outputs/
├── README.md              # Tài liệu hướng dẫn sử dụng sản phẩm đầu ra
├── map/                   # 🗺️ Thư mục chứa 8 bản đồ tương tác Folium HTML
│   ├── hybrid_shoreline_map_2024_dry.html  # Master Hybrid toàn sông (171.84 km) Mùa khô
│   ├── hybrid_shoreline_map_2024_wet.html  # Master Hybrid toàn sông (171.84 km) Mùa mưa
│   ├── reach1_interactive_map_2024_dry.html
│   ├── reach1_interactive_map_2024_wet.html
│   ├── reach2_interactive_map_2024_dry.html
│   ├── reach2_interactive_map_2024_wet.html
│   ├── reach3_interactive_map_2024_dry.html
│   └── reach3_interactive_map_2024_wet.html
├── REPORT/                # 📄 Thư mục chứa Báo cáo Nghiên cứu Khoa học & Slides
│   ├── README.md                       # Thuyết minh tài liệu báo cáo
│   ├── bao_cao_giam_sat_song_hong.md  # Báo cáo khoa học Markdown
│   ├── bao_cao_giam_sat_song_hong.tex # Báo cáo khoa học LaTeX ấn phẩm
│   ├── slide_bao_cao_thuc_tap.html    # Bài trình bày Slide HTML5 tương tác
│   └── figures/                        # 🖼️ Thư mục chứa 30 hình ảnh & biểu đồ PNG
│       ├── fig1_reach_error_comparison.png
│       ├── fig4_error_cdf_percentiles.png
│       ├── fig5_water_sand_area_dynamics.png
│       └── ...
└── others/                # 📐 Thư mục chứa 14 file GeoJSON vector & Bảng thống kê CSV
    ├── reach1_s1_shoreline_2024_dry.geojson
    ├── reach1_s1_shoreline_2024_wet.geojson
    ├── reach2_s1_shoreline_2024_dry.geojson
    ├── reach2_s1_shoreline_2024_wet.geojson
    ├── reach3_s1_shoreline_2024_dry.geojson
    ├── reach3_s1_shoreline_2024_wet.geojson
    ├── reach*_s2_ref_2024_*.geojson
    ├── validation_statistics_*.csv
    └── rf_metrics_*.txt
```

## 🎨 Phân cấp Màu Đánh giá Sai số Vị trí (3-Tier Rating Standard)

Trình tương tác HTML hiển thị mức độ sai số theo chuẩn quốc tế:
- 🟢 **Xanh lá (Good / Tốt):** Sai số $< 30\text{m}$ ($< 3\text{ pixels}$) — Chuẩn công bố khoa học.
- 🟡 **Vàng (Moderate / Trung bình):** Sai số $30\text{m} - 70\text{m}$ ($3 - 7\text{ pixels}$) — Chuẩn giám sát quy mô vùng.
- 🔴 **Đỏ (Poor / Kém):** Sai số $> 70\text{m}$ ($> 7\text{ pixels}$) — Khu vực nhiễu hoặc sai số cục bộ.
