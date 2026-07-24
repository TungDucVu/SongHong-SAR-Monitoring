**Đề cương công việc thực tập**

1\. Thông tin chung

* **Người thực hiện:** Vũ Đức Tùng  
* **Tháng:** 07/2026  
* **Tên đề tài:** Giám sát biến động đường bờ sông bãi bồi Sông Hồng tại Hà Nội bằng dữ liệu Sentinel-1 SAR  
* **Mục tiêu cốt lõi của tháng:**   
  * Xây dựng quy trình bán tự động/tự động theo dõi biến động mặt nước và bãi bồi sông Hồng từ dữ liệu ảnh vệ tinh SAR.  
  * Phát triển mô hình phân loại sử dụng Machine Learning.  
  * Thiết lập chuỗi xử lý tự động trên nền tảng Google Earth Engine.  
  * Tạo ra các sản phẩm phân tích phục vụ đánh giá diễn biến hình thái dòng sông theo chuỗi thời gian (10 năm).

2\. Bảng phân bổ công việc chi tiết (Mẫu theo Tuần)

| Tuần | Hạng mục công việc | Nhiệm vụ cụ thể | Deadline | Kết quả mong đợi |
| :---- | :---- | :---- | :---- | :---- |
| **Tuần 1** | **Chuẩn bị dữ liệu & Thiết lập môi trường** | \- Xác định phạm vi nghiên cứu (AOI). \- Thiết lập môi trường Google Earth Engine. \- Thu thập dữ liệu Sentinel-1 GRD. \- Xây dựng quy trình tiền xử lý và tính toán các đặc trưng (VV, VH, VV/VH).   | Ngày thứ 7 của tháng | Bộ dữ liệu Sentinel-1 đã được tiền xử lý; Script tự động thu thập và xử lý dữ liệu hoạt động ổn định.  |
| **Tuần 2** | **Xây dựng mô hình Machine Learning** | \- Xây dựng tập dữ liệu huấn luyện cho các lớp: Mặt nước, Bãi bồi/Cát và Lớp phủ khác. \- Chia tập Train/Validation. \- Huấn luyện mô hình Random Forest và đánh giá kết quả phân loại ban đầu.  | Ngày thứ 14 của tháng | Mô hình Random Forest hoàn chỉnh; Kết quả phân loại thử nghiệm cho các thời điểm đại diện.  |
| **Tuần 3** | **Tự động hóa chuỗi thời gian & Đánh giá** | \- Tích hợp mô hình vào pipeline xử lý chuỗi thời gian. \- Tự động tính diện tích mặt nước và bãi bồi. \- Đánh giá bằng Confusion Matrix, Overall Accuracy và Kappa Coefficient. \- Kiểm chứng kết quả với ảnh Sentinel-2 tại các thời điểm phù hợp.  | Ngày thứ 21 của tháng | Pipeline xử lý tự động; Kết quả đánh giá độ chính xác của mô hình; Chuỗi dữ liệu diện tích theo thời gian.  |
| **Tuần 4** | **Phân tích chuỗi thời gian, Liên hệ thủy điện & Báo cáo** | \- Khởi chạy full composite toàn bộ 317 cảnh ảnh Sentinel-1 SAR (2017–2026) để phân tích biến động hình thái theo timeline. \- Phân tích biến động diện tích mặt nước và bãi bồi tại các khu vực trọng điểm. \- Đối chiếu với dữ liệu thủy văn và vận hành hồ chứa thủy điện thượng nguồn. \- Hoàn thiện báo cáo (MD/LaTeX) và chuẩn bị bộ slide trình trình bày kết quả. | Ngày cuối tháng | Bộ dữ liệu composite chuỗi 10 năm; Báo cáo hoàn chỉnh; Bộ slide trình bày HTML/PDF; Script tự động hóa GEE. |

