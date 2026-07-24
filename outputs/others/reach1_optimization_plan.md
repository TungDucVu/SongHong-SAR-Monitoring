# KẾ HOẠCH TỐI ƯU HÓA ĐỘ CHÍNH XÁC PHÂN ĐOẠN THƯỢNG LƯU (REACH 1)
**Mục tiêu:** Giảm sai số RMSE của phân đoạn Thượng lưu (Reach 1) từ **178.87 m** xuống dưới **80 m** ở mùa khô và từ **63.22 m** xuống dưới **45 m** ở mùa mưa.

---

## 🛠️ CÁC TÁC VỤ TRIỂN KHAI (ACTION ITEMS)

### Tác vụ 1: Đồng bộ hóa thời gian ảnh kiểm chứng (Temporal Pair Matching)
*   **Mục tiêu**: Loại bỏ sai số do bãi cát dịch chuyển vật lý giữa các thời điểm chụp của 2 vệ tinh.
*   **Các bước thực hiện**:
    1.  Trong script `scripts/extract_research_shoreline.py` hoặc hàm lấy ảnh Sentinel-2, thay vì sử dụng ảnh composite trung vị của cả mùa, hãy viết hàm truy vấn tìm cặp ảnh Sentinel-1 và Sentinel-2 có **ngày thu nhận sát nhau nhất** (lệch $\le 1$ ngày).
    2.  Ví dụ cặp ngày tối ưu trong năm 2024:
        - Mùa khô: S1 ngày `2024-02-15` và S2 ngày `2024-02-16`.
        - Mùa mưa: S1 ngày `2024-08-20` và S2 ngày `2024-08-20` (cùng ngày).
    3.  Chạy trích xuất và kiểm chứng đường bờ trên cặp ảnh đồng thời này để thiết lập mức sai số kỹ thuật chuẩn (baseline).

---

### Tác vụ 2: Bổ sung đặc trưng Biến động thời gian (Temporal Variance Feature)
*   **Mục tiêu**: Phân tách bãi bồi cát động (độ ẩm thay đổi liên tục) ra khỏi mặt nước ổn định.
*   **Các bước thực hiện**:
    1.  Cập nhật hàm tạo đặc trưng trong `src/classification.py` (hàm `create_feature_stack`):
        - Tính toán **Độ lệch chuẩn (Standard Deviation)** của phân cực $VV$ và $VH$ trên toàn bộ chuỗi ảnh trong mùa trước khi tính ảnh trung vị:
          ```javascript
          // GEE Javascript / Python API
          var vvStdDev = s1Collection.select('VV').reduce(ee.Reducer.stdDev()).rename('VV_stdDev');
          var vhStdDev = s1Collection.select('VH').reduce(ee.Reducer.stdDev()).rename('VH_stdDev');
          ```
    2.  Thêm 2 kênh `VV_stdDev` và `VH_stdDev` vào danh sách biến huấn luyện `CLASSIFIER_FEATURES` trong `src/config.py`.
    3.  Huấn luyện lại mô hình Random Forest. Các bãi cát động sẽ được phân loại chính xác hơn nhờ chỉ số phương sai cao.

---

### Tác vụ 3: Huấn luyện Bộ phân loại cục bộ cho Reach 1 (Reach-Specific RF)
*   **Mục tiêu**: Tránh hiện tượng mô hình toàn cục bị thiên vị bởi khu vực Trung/Hạ lưu.
*   **Các bước thực hiện**:
    1.  Tạo đa giác mặt nạ cho Reach 1 bằng cách buffer tim sông đoạn từ km 0 đến km 57.28.
    2.  Số hóa bổ sung khoảng **30 mẫu huấn luyện mới** trong phạm vi Reach 1 cho lớp phủ:
        - **Cát ẩm (Wet Sand)**: Khu vực mép nước của các doi cát lớn.
        - **Kênh nước nông (Shallow Water)**: Các nhánh sông nhỏ uốn lượn.
    3.  Huấn luyện một mô hình Random Forest riêng biệt chuyên dụng cho Reach 1 (`rf_classifier_reach1`) và chỉ áp dụng mô hình này cho vùng ảnh thuộc Reach 1.

---

### Tác vụ 4: Điều chỉnh bộ lọc đốm thích ứng (Speckle Filter Tuning)
*   **Mục tiêu**: Bảo toàn các nhánh sông hẹp và đường mép cát sắc nét.
*   **Các bước thực hiện**:
    1.  Tại file `src/preprocessing.py`, viết thêm cấu hình cho phép điều chỉnh kích thước cửa sổ lọc Refined Lee về **$5\times5$ pixel** thay vì cố định $7\times7$ cho riêng Reach 1.
    2.  Hoặc thay thế bằng **Lọc đốm đa thời gian (Multi-temporal Speckle Filter)** của GEE để lọc nhiễu hạt dựa trên chuỗi thời gian mà không làm giảm độ sắc nét không gian của ranh giới bờ sông.

---

## 📈 TIÊU CHÍ ĐÁNH GIÁ THÀNH CÔNG (KPIs)
*   [ ] Số lượng điểm lấy mẫu trong Reach 1 đạt tỷ lệ $\ge 85\%$ nằm trong khoảng sai số $\le 50\text{ m}$.
*   [ ] Chỉ số sai số RMSE của Reach 1 (Mùa khô) giảm xuống dưới **80 m** (giảm ~55% so với mức 178.87m hiện tại).
*   [ ] Sai số Hausdorff cực đại của Reach 1 (Mùa khô) giảm xuống dưới **200 m** (loại bỏ hoàn toàn các đoạn đứt gãy topo).
*   [ ] Các kênh sông nhỏ chạy quanh bãi Minh Châu được trích xuất liên tục, không bị đứt đoạn thành các hồ biệt lập.
