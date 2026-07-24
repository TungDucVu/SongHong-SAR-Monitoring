# Thư mục Scripts Công cụ & Tiền xử lý (Utility & Batch Processing Scripts)

Thư mục này chứa các kịch bản Python phục vụ huấn luyện mô hình, vẽ biểu đồ tổng hợp và chạy xử lý hàng loạt.

## 🛠️ Danh sách Scripts

1. **`plot_hybrid_map.py`**: Tự động đọc dữ liệu GeoJSON đường bờ trích xuất từ 3 phân đoạn sông để ghép nối thành bản đồ tương tác Master Hybrid Folium duy nhất cho toàn bộ 171.84 km sông Hồng.
2. **`train_classifier.py`**: Kịch bản huấn luyện, đánh giá ma trận nhầm lẫn (Confusion Matrix) và tối ưu tham số mô hình Random Forest 4 lớp.
3. **`extract_research_shoreline.py`**: Kịch bản tự động xử lý hàng loạt trích xuất đường bờ chuỗi thời gian nhiều năm (2017 – 2026).
4. **`visualize_features.py`**: Vẽ biểu đồ tương quan phân bố đặc trưng (Boxplots & Feature Correlation Heatmaps).
