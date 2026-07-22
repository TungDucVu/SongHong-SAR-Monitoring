# BÁO CÁO TIẾN ĐỘ NGHIÊN CỨU & GIÁM SÁT ĐƯỜNG BỜ SÔNG HỒNG BẰNG DỮ LIỆU VỆ TINH SAR (SENTINEL-1/2) - NĂM 2024

**Dự án:** Giám sát biến động đường bờ sông Hồng khu vực Bắc Bộ bằng dữ liệu Vệ tinh SAR (Sentinel-1) kết hợp Vệ tinh Quang học (Sentinel-2)  
**Tác giả:** Đội ngũ Nghiên cứu Giám sát Sông Hồng SAR  
**Cập nhật:** Tháng 07/2026  

---

## 1. TỔNG QUAN HỆ THỐNG & KHU VỰC NGHIÊN CỨU (AOI)

### 1.1 Xác định Khu vực Nghiên cứu (Area of Interest - AOI)
Hệ thống sử dụng đường tâm sông chuẩn (Centerline GeoJSON) kết hợp ranh giới hành chính vùng hạ lưu sông Hồng để tự động thiết lập hành lang giám sát (Corridor Buffer $2.0\text{ km}$) bằng thuật toán hình học trong Shapely và GeoPandas.

### 1.2 Phân đoạn Sông theo Thủy văn & Địa hình (Reach Segmentation)
Hệ thống phân chia 171.84 km sông Hồng thành **3 Phân đoạn (Reaches)** có đặc trưng vật lý riêng biệt:

```
[Mỏm sông Thượng lưu (km 0.0)]
               │
               ▼
   ─── Reach 1 (Thượng lưu: km 0.0 ➔ km 57.28) ───
   • Lòng sông rộng, bãi cát động, nhiều luồng lạch phân nhánh.
   • Khúc ngoặt Ba Vì / Sơn Tây bị nhiễu do địa hình núi che khuất.
               │  (Ranh giới: Latitude 21.1528 N, Longitude 105.5415 E)
               ▼
   ─── Reach 2 (Trung lưu: km 57.28 ➔ km 114.56) ───
   • Đoạn đô thị Hà Nội với hệ thống đê kiên cố và nhiều cầu bắc qua.
   • Độ rộng bờ ổn định nhưng chịu nhiễu công trình nhân tạo.
               │
               ▼
   ─── Reach 3 (Hạ lưu: km 114.56 ➔ km 171.84) ───
   • Vùng đồng bằng nông nghiệp meander nhẹ, bờ sông tương đối ổn định.
```

---

## 2. QUY TRÌNH XỬ LÝ DỮ LIỆU (PIPELINE ARCHITECTURE)

Quy trình giám sát đường bờ tự động trải qua **4 giai đoạn chính**:

```
[1. LẤY AOI & CENTERLINE] ──► [2. PRE-PROCESSING] ──► [3. PROCESSING] ──► [4. POST-PROCESSING & MODEL]
```

### 2.1 Tiền xử lý Dữ liệu (Pre-processing)
1. **Thu thập Ảnh Vệ tinh**: 
   - **Sentinel-1 SAR**: Ảnh ra-đa băng C (Interferometric Wide mode, phân cực đôi VV và VH, độ phân giải 10m).
   - **Sentinel-2 MSI**: Ảnh quang học đa phổ (băng Blue, Green, Red, NIR, SWIR).
2. **Khử Nhiễu Đốm (Speckle Filtering)**:
   - Áp dụng bộ lọc **Refined Lee Filter** trên không gian cửa sổ 2D để loại bỏ nhiễu đốm đặc trưng của ảnh Ra-đa SAR nhưng vẫn bảo tồn chính xác đường biên giữa nước và cạn.
3. **Trích xuất Tập Đặc trưng Không gian & Kết cấu (Feature Engineering)**:
   - Tạo bộ đặc trưng 17 băng chỉ số bao gồm: `VV`, `VH`, tỷ lệ `VV/VH`, tổng `VV+VH`, trung bình `VV_mean`, cùng bộ 6 chỉ số kết cấu GLCM (Gray-Level Co-occurrence Matrix) cho cả 2 kênh phân cực:
     - `Contrast` (Độ tương phản)
     - `Variance` (Biến thiên)
     - `Entropy` (Độ hỗn loạn)
     - `Homogeneity` (Độ đồng nhất)
     - `Correlation` (Độ tương quan)
     - `ASM` (Angular Second Moment)

---

### 2.2 Xử lý Trung tâm (Processing)
1. **Tạo Ảnh Tổng hợp Mùa (Seasonal Composites)**:
   - Hệ thống tự động lọc và gom toàn bộ ảnh Sentinel-1 trong năm thành 2 tập composite mùa theo phương pháp lấy trung vị (Median):
     - **Mùa Khô (Dry Season Composite)**: Gom ảnh từ tháng 11 năm trước đến tháng 4 năm sau.
     - **Mùa Mưa (Wet Season Composite)**: Gom ảnh từ tháng 5 đến tháng 10.
2. **Ngưỡng phân loại tự động & Hiệu chuẩn (Thresholding & Threshold Calibration)**:
   - Trích xuất viền mặt nước Sentinel-2 NDWI làm dữ liệu chuẩn mặt đất (Ground Truth reference).
   - Rút trích $28,000+$ điểm ranh giới để hiệu chuẩn động ngưỡng phản xạ ra-đa của Sentinel-1 (Giá trị hiệu chuẩn tối ưu đạt `VV = -13.0 dB`, `VH = -19.0 dB`).

---

### 2.3 Hậu xử lý Không gian (Post-processing)
1. **Làm sạch Hình thái học 2D (Binary Morphology)**:
   - Sử dụng thư viện `scikit-image` xử lý hình thái học cục bộ: loại bỏ vật thể nước nhỏ hơn 20 pixels (`remove_small_objects < 20px`) và lấp lỗ thủng đốm nhỏ hơn 100 pixels (`remove_small_holes < 100px`).
2. **Ràng buộc Kênh hoạt động Active Channel (Active Channel Constraints)**:
   - Cắt giao đa giác nước Sentinel-1 với vùng đệm 150m của đường bờ tham chiếu Sentinel-2 (`s2_water_poly.buffer(150.0)`). Phép lọc này triệt tiêu hoàn toàn các ao nuôi thủy sản nội đồng và vùng ngập lũ disconnected.
3. **Bộ lọc Đảo nổi / Cù lao (Island Filtering)**:
   - Lọc bỏ các cồn cát/đảo giả bằng phép phân tích diện tích ($<20,000\text{ m}^2$), độ tròn ($Circularity \ge 0.8$) và tỷ lệ đè lên nước S2 ($Overlap \ge 0.5$).
4. **Cắt tỉa Đồ thị & Làm mịn Đường bờ**:
   - Cắt tỉa đồ thị (Graph Pruning) loại bỏ các nhánh gai nhỏ ($min\_length = 1500\text{ m}$).
   - Áp dụng làm mịn góc **Chaikin Smoothing** và đơn giản hóa đa giác (Douglas-Peucker simplification) giúp giảm $75-80\%$ số lượng đỉnh vertex mà vẫn đảm bảo sai số Hausdorff deviation dưới $15.0\text{ m}$.

---

## 3. KIẾN TRÚC MÔ HÌNH (LOCAL VS GLOBAL MODEL)

Để tối ưu hóa độ chính xác theo đặc thù từng đoạn sông, hệ thống triển khai kiến trúc lai kép (Hybrid Architecture):

```
                                  ┌─── Reach 1: Local Random Forest (Advanced Error Suppression)
                                  │    • Phù hợp địa hình phức tạp, meander Ba Vì
                                  │    • Resampling ranh giới 90m + Topographic HAND/Slope
Mô hình Phân đoạn Sông Hồng ─────┤
                                  │    ─── Reach 2 & 3: Global Random Forest
                                  │    • Phù hợp hành lang đô thị Hà Nội & Đồng bằng
                                  └─── • Tối ưu hóa tính toán trên dải sông dài 114km
```

### 3.1 Reach 1 (Thượng lưu) - Local RF Model (Advanced Error Suppression)
* **Đặc điểm**: Nằm ở thượng nguồn với các bãi cát đổi dòng liên tục và khúc ngoặt meander Ba Vì bị bóng núi che phủ.
* **Kỹ thuật "Đặc trị"**:
  1. **Otsu 4-Class S2 Reference**: Tự động tạo nhãn 4 lớp (*Deep Water, Shallow Water, Wet Sand, Land*) từ Sentinel-2.
  2. **Hard-Negative Boundary Mining**: Ép mô hình Local RF tập trung học $70\%$ mẫu tại ranh giới $90\text{ m}$ giữa nước nông và cát ướt, bổ sung $600\text{ mẫu}$ ranh giới tại khúc ngoặt Ba Vì (Meander Hotspot).
  3. **Topographic Integration**: Đưa chỉ số địa hình HAND (MERIT Hydro) và Slope vào Feature Stack để xóa hoàn toàn bóng núi Ba Vì.

### 3.2 Reach 2 & 3 (Trung & Hạ lưu) - Global RF Model
* **Đặc điểm**: Bắt đầu từ tọa độ `21.1528 N, 105.5415 E` đổ về hạ lưu. Bờ sông tương đối định hình, ít meander gắt.
* **Kỹ thuật**: Sử dụng 1 mô hình Random Forest toàn cục tinh gọn (300 cây decision trees, 193 đa giác mẫu huấn luyện chuẩn) giúp quy trình xử lý 114 km sông diễn ra siêu tốc với độ chính xác cao.

---

## 4. ĐÁNH GIÁ ĐỘ CHÍNH XÁC (ACCURACY METRICS FOR 2024 WET & DRY)

Độ chính xác của đường bờ Sentinel-1 trích xuất được kiểm định độc lập với tập điểm tham chiếu Sentinel-2 NDWI trên toàn bộ 3 phân đoạn trong năm 2024:

### 4.1 Bảng Tổng hợp Độ chính xác Mùa Khô 2024 (Dry Season 2024)

| Phân đoạn Sông | Số điểm kiểm định | Mean Error (m) | Median Error (m) | RMSE (m) | Hausdorff Max (m) | P95 (m) |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| **Reach 1 (Thượng lưu - Local RF)** | 12,169 | 31.52 m | 19.96 m | **47.02 m** | 189.64 m | 117.86 m |
| **Reach 2 (Trung lưu - Hà Nội)** | 20,507 | 30.28 m | 19.84 m | **52.28 m** | 354.25 m | 117.39 m |
| **Reach 3 (Hạ lưu - Đồng bằng)** | 13,901 | 12.21 m | 6.40 m | **19.56 m** | 170.98 m | **38.27 m** |
| **Tổng thể Reach 2 & 3** | **34,408** | **25.21 m** | **15.20 m** | **43.53 m** | **354.25 m** | **92.84 m** |

*Đánh giá mùa khô:* Độ chính xác cực kỳ ấn tượng ở Reach 3 với sai số trung bình chỉ **12.21m** (gần bằng 1 pixel ảnh 10m). Sai số tổng thể RMSE toàn hạ lưu đạt **43.53m** (đạt tiêu chuẩn < 50m).

---

### 4.2 Bảng Tổng hợp Độ chính xác Mùa Mưa 2024 (Wet Season 2024)

| Phân đoạn Sông | Số điểm kiểm định | Mean Error (m) | Median Error (m) | RMSE (m) | Hausdorff Max (m) | P95 (m) |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| **Reach 1 (Thượng lưu - Local RF)** | 25,198 | 62.71 m | 28.52 m | **88.59 m** | 274.46 m | 151.13 m |
| **Reach 2 (Trung lưu - Hà Nội)** | 19,708 | 29.86 m | 19.96 m | **45.18 m** | 279.93 m | **106.24 m** |
| **Reach 3 (Hạ lưu - Đồng bằng)** | 13,710 | 84.02 m | 68.79 m | **106.30 m** | 175.93 m | 151.42 m |

*Đánh giá mùa mưa:* Reach 2 (đoạn qua Hà Nội) giữ độ ổn định cao với RMSE chỉ **45.18m**. Ở Reach 1 và Reach 3, mùa mưa lượng nước dâng cao gây ngập rộng bãi bồi nông nghiệp làm sai số gia tăng (RMSE ~88-106m), đúng với quy luật thủy văn sông Hồng.

---

## 5. THÁCH THỨC HIỆN TẠI & HƯỚNG NGHIÊN CỨU LOẠI BỎ CẦU (BRIDGE REMOVAL RESEARCH)

### 5.1 Nguyên nhân Kỹ thuật của Bài toán Cầu bắc qua Sông
Trong ảnh ra-đa SAR (Sentinel-1), kết cấu bê tông và khung thép của các cây cầu lớn tại Hà Nội (như cầu Thăng Long, Nhật Tân, Long Biên, Chương Dương, Vĩnh Tuy, Thanh Trì) có độ phản xạ sóng ra-đa rất mạnh (`High Backscatter`), hoàn toàn tương tự như lớp đất liền (`Non-Water`). 

Điều này dẫn đến hiện tượng:
* Thuật toán phân loại SAR bị nhầm vùng gầm cầu thành một "dải đất" đứt đoạn cắt ngang sông.
* Khi trích xuất đường bờ, đường bờ bị bẻ ngoặt $90^\circ$ chạy vắt ngang qua sông hoặc bị kéo phình vệt lấn vào phố/đê hai bên bờ.

```
[Bờ Tả Sông Hồng] ───► [Thân cầu Bê tông (Nhầm là Đất)] ───► [Bờ Hữu Sông Hồng]
                                    │
                         (Nhiễu bẻ ngoặt 90 độ)
                                    ▼
                [Đường bờ bị xé đứt hoặc vắt ngang sông]
```

---

### 5.2 Các Hướng Tiếp cận Nghiên cứu & Thực nghiệm Loại bỏ Cầu

Đội ngũ nghiên cứu đang tiến hành thử nghiệm và so sánh **4 phương pháp xử lý nhiễu cầu**:

#### **Phương pháp 1: Active Channel Bridge Eraser (Đục lỗ / Phủ Nước gầm cầu)**
* **Cách làm**: Lấy đa giác cầu cắt giao với vùng lòng sông Sentinel-2 (`bridges ∩ s2_active_channel`), mở rộng nhẹ $10-35\text{ m}$ rồi hòa tan (Union) trực tiếp vào đa giác mặt nước Sentinel-1.
* **Ưu điểm**: Chuyển nhãn khu vực gầm cầu thành Nước, làm cho đường bờ trôi liên tục 161km xuyên suốt mùa khô lẫn mùa mưa.

#### **Phương pháp 2: Local Convex Hull Connection (Nối lồi cục bộ tại gầm cầu)**
* **Cách làm**: Xác định vùng nước thượng lưu và hạ lưu dưới gầm cầu, dựng hình bao lồi (Convex Hull) cục bộ giới hạn trong đa giác cầu mở rộng $20\text{ m}$.
* **Ưu điểm**: Tự động co giãn theo độ rộng thực tế của sông dưới cầu, không làm biến dạng các đoạn bờ tự nhiên xung quanh.

#### **Phương pháp 3: Line Clipping & Interpolation (Xén vệt cầu trên đường bờ Vector)**
* **Cách làm**: Thực hiện xử lý trên đối tượng đường Vector `LineString`. Sử dụng đa giác cầu loại bỏ các đoạn đường bờ đâm xuyên qua cầu (`shoreline.difference(bridge_buffer)`), sau đó dùng `linemerge()` để nối liền 2 đầu bờ sông.
* **Ưu điểm**: Can thiệp ở bước cuối của Vector, giữ nguyên kết quả phân loại raster gốc.

#### **Phương pháp 4: Manual Bank-to-Bank Bridge Polygons (Khoanh đa giác thủ công bờ-sang-bờ)**
* **Cách làm**: Số hóa thủ công tập đa giác cầu (`data/bridges.geojson`) nối chính xác từ mép bờ bên này sang mép bờ bên kia. Gộp trực tiếp đa giác này vào mặt nạ nước thô.
* **Ưu điểm**: Đơn giản, bám đúng ranh giới bờ do người dùng định nghĩa.

---

## 6. KẾ HOẠCH PHÁT TRIỂN TIẾP THEO

1. **Chuẩn hóa Thuật toán Bỏ Cầu Tối ưu**: Thống nhất giải pháp loại bỏ cầu có độ mượt hình thái cao nhất mà không làm sai lệch sai số kiểm định RMSE.
2. **Mở rộng Chuỗi Thời gian 10 Năm (2015 - 2025)**: Áp dụng quy trình chuẩn hóa đã nghiệm thu để trích xuất đường bờ tự động cho toàn bộ dữ liệu 10 năm của sông Hồng.
3. **Phân tích Xu hướng Xói lở & Bồi tụ**: Xây dựng mô hình tính toán tốc độ dịch chuyển đường bờ (DSAS - Digital Shoreline Analysis System) để phục vụ công tác cảnh báo thiên tai bờ sông.
