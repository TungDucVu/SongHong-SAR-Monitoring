# Thư mục Luồng Thực thi Phân đoạn Sông (Main Workflow Execution)

Thư mục này chứa các kịch bản thực thi trực tiếp quy trình trích xuất đường bờ và bãi bồi tự động cho từng phân đoạn sông (Reach) theo phương án sản xuất **v1.0-OptionA-Production**.

## 🚀 Các File Thực thi Chính

1. **`run_reach1_local.py`**: Khởi chạy quy trình trích xuất cho **Reach 1 (Thượng lưu: Sơn Tây – Ba Vì – Phúc Thọ)**.
   - Thử nghiệm cả 2 mùa (Mùa khô & Mùa mưa).
   - Tối ưu hóa sai số RMSE mùa khô giảm **-31.0%** ($48.82\text{m}$).

2. **`run_reach2_local.py`**: Khởi chạy quy trình trích xuất cho **Reach 2 (Trung lưu: Nội đô Hà Nội)**.
   - Xử lý các yếu tố nhiễu cầu nhân tạo (6 cầu lớn) và đê kè đô thị.
   - RMSE mùa khô đạt **$35.98\text{m}$** (Tiệm cận mức Tốt).

3. **`run_reach3_local.py`**: Khởi chạy quy trình trích xuất cho **Reach 3 (Hạ lưu: Phú Xuyên – Thường Tín – Thanh Trì)**.
   - Đạt độ chính xác cao nhất tuyệt đối: RMSE mùa khô **$18.72\text{m}$** ($< 2\text{ pixels}$) & mùa mưa **$25.72\text{m}$** ($< 3\text{ pixels}$).
   - Đạt chuẩn khoa học cao nhất (**High Precision / Publication Grade**).

## 💡 Hướng dẫn Sử dụng

Bạn có thể chạy riêng từng file bằng lệnh Python hoặc chạy thông qua tập trung `main.py` ở thư mục gốc:

```bash
# Chạy trực tiếp script phân đoạn 1:
python main_workflow/run_reach1_local.py

# Hoặc thông qua main runner:
python main.py --reach 1
```
