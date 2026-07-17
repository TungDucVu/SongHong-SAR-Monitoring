# BÁO CÁO CHI TIẾT PHASE 3: PHÂN LOẠI MACHINE LEARNING & TRÍCH XUẤT SHORELINE NGHIÊN CỨU SÔNG HỒNG

**Dự án:** Giám sát biến động đường bờ và bãi bồi Sông Hồng tại Hà Nội bằng dữ liệu Sentinel-1 SAR  
**Trạng thái:** Kế hoạch thực hiện chuẩn hóa (Frozen Pipeline)  

---

## MỤC LỤC
1. [Tổng quan Pipeline đề xuất](#tong-quan-pipeline-de-xuat)
2. [Chi tiết các Phase & Sub-phases](#chi-tiet-cac-phase--sub-phases)
   * [Phase 1: SAR Data Preparation (Chuẩn bị dữ liệu)](#phase-1-sar-data-preparation-chuan-bi-du-lieu)
   * [Phase 2: Feature Engineering (Trích xuất đặc trưng)](#phase-2-feature-engineering-trich-xuat-dac-trung)
   * [Phase 3: Random Forest Classification (Phân loại máy học)](#phase-3-random-forest-classification-phan-loai-may-hoc)
   * [Phase 4: Classification Refinement (Hậu xử lý mặt nạ)](#phase-4-classification-refinement-hau-xu-ly-mat-na)
   * [Phase 5: Water–Sand Shared Boundary Extraction (Trích xuất đường bờ)](#phase-5-water-sand-shared-boundary-extraction-trich-xuat-duong-bo)
   * [Phase 6: Shoreline Cleaning (Lọc sạch topo đường bờ)](#phase-6-shoreline-cleaning-loc-sach-topo-duong-bo)
   * [Phase 7: Shoreline Smoothing & Simplification (Làm mượt đường bờ)](#phase-7-shoreline-smoothing--simplification-lam-muot-duong-bo)
   * [Phase 8: Final Quality Control and Shoreline Validation (Kiểm chứng và đánh giá chất lượng cuối cùng)](#phase-8-final-quality-control-and-shoreline-validation-kiem-chung-va-danh-gia-chat-luong-cuoi-cung)
3. [Đề xuất cấu trúc Luận văn/Paper: Chương 4 – Đánh giá Thực nghiệm (Experimental Evaluation)](#de-xuat-cau-truc-luan-vanpaper-chuong-4--danh-gia-thuc-nghiem-experimental-evaluation)
4. [Kế hoạch triển khai mã nguồn](#ke-hoach-trien-khai-ma-nguon)

---

## TỔNG QUAN PIPELINE ĐỀ XUẤT

Để theo dõi biến động đường bờ Sông Hồng theo chuỗi thời gian, dự án thống nhất đóng băng (freeze) quy trình trích xuất đường bờ dựa trên **ranh giới hình học tiếp xúc trực tiếp giữa lớp Nước (Water) và Cát (Sand)**. Phương pháp này loại bỏ hoàn toàn các thuật toán phát hiện biên dạng pixel cục bộ để tập trung vào mối quan hệ topo không gian thực sự giữa dòng chảy chính và bãi bồi cát.

Pipeline này tập trung hoàn toàn vào thuật toán trích xuất đường bờ. Các đánh giá độ chính xác mở rộng, phân tích độ nhạy và tính nhất quán thời gian được trình bày riêng trong phần thực nghiệm của nghiên cứu.

> [!NOTE]
> **Lưu ý về Dữ liệu đầu ra**: Quy trình này không yêu cầu xuất ảnh raster dạng GeoTIFF (.tif) ra bên ngoài (Google Drive/Local). Toàn bộ thuật toán xử lý ảnh raster và vector được thực thi lập trình, kết quả đường bờ cuối cùng được kiểm chứng và trực quan hóa trực tiếp dưới dạng bản đồ tương tác HTML (Folium).

```text
       Sentinel-1 GRD (VV + VH)
                  │
                  ▼
         SAR Preprocessing
                  │
                  ▼
         Feature Engineering (GLCM + Polarizations)
                  │
                  ▼
         Random Forest Classification (Calibrated on 2024 Composites)
                  │
                  ▼
       Classification Refinement (Morphological Disk Filters)
                  │
                  ▼
     Water–Sand Shared Boundary Extraction (Main Corridor Only)
                  │
                  ▼
         Shoreline Graph Cleaning (Empirically Calibrated)
                  │
                  ▼
         Chaikin Smoothing (Vertex Density Interpolation)
                  │
                  ▼
       Douglas–Peucker Simplification (Redundant Vertex Reduction)
                  │
                  ▼
       Final Quality Control and Shoreline Validation
                  │
                  ▼
           Final Shoreline
```

---

## CHI TIẾT CÁC PHASE & SUB-PHASES

### PHASE 1: SAR DATA PREPARATION
Mục tiêu là tạo ra ảnh phân cực chuẩn hóa, triệt tiêu nhiễu địa hình và nhiễu đốm để thu được giá trị tán xạ ngược ($VV$ và $VH$) trung thực.

* **Sub-phase 1.1: Metadata & Orbit Calibration**
  * Áp dụng quỹ đạo chính xác (Apply Orbit File) để cập nhật thông tin vị trí vệ tinh.
* **Sub-phase 1.2: Noise Suppression**
  * **Thermal Noise Removal**: Loại bỏ nhiễu nhiệt giữa các dải quét (sub-swaths).
  * **Border Noise Removal**: Loại bỏ các pixel viền ảnh bị lỗi năng lượng thấp.
* **Sub-phase 1.3: Radiometric & Geometric Correction**
  * **Radiometric Calibration**: Chuyển đổi giá trị số (DN) sang hệ số tán xạ vật lý $\sigma^0$ (Sigma0) hoặc $\gamma^0$ (Gamma0).
  * **Terrain Correction (RDTC)**: Sử dụng mô hình độ cao số (DEM) để hiệu chỉnh biến dạng địa hình do góc nghiêng radar.
* **Sub-phase 1.4: Decibel Conversion & Adaptive Filtering**
  * Chuyển đổi giá trị tuyến tính sang logarit (dB scale):
    $$dB = 10 \log_{10}(Power)$$
  * Áp dụng bộ lọc thích ứng hướng **Refined Lee Filter (7×7)** để giảm nhiễu đốm (speckle) mà không làm mờ biên cạnh bãi cát và bờ sông.

> [!NOTE]
> **CHECKPOINT PHASE 1: KIỂM TRA CHẤT LƯỢNG TIỀN XỬ LÝ**
> * **Chỉ số đo lường (Metric)**: Tán xạ ngược tại vùng nước sâu ổn định $VV \le -15\text{ dB}$, $VH \le -22\text{ dB}$.
> * **Kiểm tra trực quan (Visual)**: Biên bờ sông sắc nét, không bị nhòe (no blur). Nhiễu đốm hạt muối tiêu giảm rõ rệt so với ảnh gốc. Nếu có vệt mờ biên, kiểm tra lại bộ lọc Lee.

---

### PHASE 2: FEATURE ENGINEERING
Xây dựng một bộ đặc trưng không gian và phân cực phong phú (Feature Stack) khoảng 10-12 kênh để tăng tối đa độ phân tách giữa các lớp phủ.

* **Sub-phase 2.1: Derived Polarizations**
  * Sử dụng các kênh phân cực gốc: $VV$, $VH$.
  * Tích hợp tỷ số phân cực (tương đương phép chia tuyến tính $VV/VH$ trong miền log):
    $$\text{Ratio} = VV_{\text{dB}} - VH_{\text{dB}}$$
  * Tính toán các đặc trưng số học:
    * Tổng tuyến tính chuyển dB: $VV + VH$
    * Giá trị trung bình: $\text{Mean}(VV, VH)$
* **Sub-phase 2.2: GLCM Texture Analysis**
  * Tính ma trận đồng xuất hiện mức xám (Gray-Level Co-occurrence Matrix) trên cửa sổ trượt $5\times5$ hoặc $7\times7$ pixel để nắm bắt cấu trúc bề mặt nhám của bãi bồi cát và thực vật:
    * **Contrast**: Độ tương phản nhám.
    * **Entropy**: Độ hỗn loạn thông tin.
    * **Homogeneity**: Độ đồng nhất bề mặt.
    * **Correlation**: Độ tương quan không gian.
    * **ASM (Angular Second Moment)**: Thể hiện độ đồng dạng.
    * **Variance**: Phương sai cục bộ.

> [!NOTE]
> **CHECKPOINT PHASE 2: KIỂM TRA ĐẶC TRƯNG ĐẦU VÀO**
> * **Chỉ số đo lường (Metric)**: Kiểm tra giá trị vô cực (Inf) hoặc rỗng (NaN) trên toàn bộ kênh ảnh đặc trưng. Đảm bảo tỷ lệ vô trị là 0%.
> * **Kiểm tra trực quan (Visual)**: Kênh GLCM Contrast làm nổi bật biên giới đất/nước và bãi bồi. Kênh Ratio và Difference phân cực phân tách rõ ranh giới cát ẩm và nước chảy.

---

### PHASE 3: RANDOM FOREST CLASSIFICATION
Thực hiện phân loại ảnh đa kênh thành các lớp phủ mục tiêu bằng thuật toán Học máy Random Forest.

* **Sub-phase 3.1: Class Definition**
  Phân loại lớp phủ thành 5 lớp chính:
  1. **Water (Nước)**: Lòng sông chính, kênh rạch lớn.
  2. **Sand (Cát)**: Bãi bồi cát nổi giữa sông, bãi cát ven bờ.
  3. **Vegetation (Thực vật)**: Đất nông nghiệp, cây bụi ven đê.
  4. **Built-up (Khu dân cư)**: Đô thị, công trình nhân tạo.
  5. **Others (Lớp phủ khác)**: Đất trống, vùng bóng đồi.
* **Sub-phase 3.2: Sampling Strategy & Baseline Calibration**
  * **Thiết lập Baseline năm 2024**: Dữ liệu mẫu huấn luyện và kiểm chứng sẽ ưu tiên thu thập và hiệu chuẩn trên các ảnh composite mùa khô (dry) và mùa lũ (wet) của năm 2024 trước để thiết lập baseline mô hình tối ưu trước khi mở rộng ra chuỗi thời gian 10 năm.
  * **Stratified Sampling**: Lấy mẫu phân tầng để bảo đảm đại diện đầy đủ các lớp phủ.
  * **Balanced Samples**: Cân bằng số lượng điểm mẫu giữa các lớp để tránh lệch mô hình (bias).
  * **Train/Test Split**: Chia bộ mẫu thành 70% huấn luyện và 30% kiểm chứng độc lập.

> [!NOTE]
> **CHECKPOINT PHASE 3: ĐÁNH GIÁ ĐỘ CHÍNH XÁC PHÂN LOẠI**
> * **Chỉ số đo lường (Metric)**: Báo cáo đầy đủ Precision, Recall, F1-score cho từng lớp phủ thay vì chỉ dùng Overall Accuracy (OA) và Kappa (do các lớp dễ như Water/Vegetation dễ làm sai lệch OA). Đặc biệt chú trọng lớp **Sand** (mục tiêu F1-score cho Sand $\ge 75\%$, hiệu chuẩn thực nghiệm).
> * **Kiểm tra trực quan (Visual)**: Ma trận nhầm lẫn (Confusion Matrix) không bị nhầm lẫn nghiêm trọng giữa lớp Cát (Sand) và các công trình đô thị (Built-up) hoặc đất trống khô (Others).

---

### PHASE 4: CLASSIFICATION REFINEMENT
Hậu xử lý kết quả phân loại dạng raster để thu được các vùng mặt nước và bãi cát sạch sẽ, liền mạch.

* **Sub-phase 4.1: Pixel-level Cleaning**
  * Áp dụng **Majority Filter** để loại bỏ các pixel phân loại sai lệch đơn lẻ (nhiễu muối tiêu).
* **Sub-phase 4.2: Morphological Filtering**
  * Áp dụng các bộ lọc hình thái toán học sử dụng **phần tử cấu trúc hình đĩa (disk)** để đảm bảo tính đẳng hướng không gian, tránh gây méo lệch hướng biên:
    * **Morphological Opening (Bán kính đĩa = 2 pixels / 20m)**: Phá vỡ các cầu nối mỏng nhân tạo, lọc sạch nhiễu hạt cát/nước nhỏ cô lập.
    * **Morphological Closing (Bán kính đĩa = 3 pixels / 30m)**: Lấp đầy các lỗ rỗng, khe nứt nhỏ trong lòng bãi cát và các vùng nước lớn.
* **Sub-phase 4.3: Connected Component & Corridor Extraction & Bridge Masking**
  * **Keep Main River Corridor**: Xác định tiêu chí giữ lại hành lang sông chính:
    * Thực hiện phân tích thành phần liên thông để xác định thành phần liên thông đại diện cho hành lang sông Hồng đang hoạt động (active Red River corridor) dựa trên tính liên thông và các ràng buộc không gian.
    * Giữ lại các thành phần phụ nếu chúng nằm trong khoảng cách giới hạn (ví dụ: 500m) so với đường tâm sông (centerline) đã số hóa để tránh bỏ sót các nhánh nhỏ quan trọng.
    * Loại bỏ hoàn toàn các vùng nước độc lập (ao hồ nội đồng ngoài đê, ao nuôi trồng thủy sản) không thuộc hệ thống thủy văn sông chính.
  * **Manual Bridge Masking (Mặt nạ cầu thủ công)**: Để tránh hiện tượng dính liền mặt nước giả tạo dưới gầm các cây cầu lớn bắc qua sông Hồng (làm sai lệch dòng chảy liên tục), hệ thống tích hợp công cụ số hóa Leaflet cục bộ (`tools/digitize_bridges.html`). Bản đồ số hóa và xuất đa giác cầu sang `data/bridges.geojson`, sau đó tải trực tiếp trong python để cắt bỏ phần nhiễu mặt nước dưới chân cầu Nhật Tân, Long Biên, Chương Dương, Vĩnh Tuy, v.v.

> [!NOTE]
> **CHECKPOINT PHASE 4: KIỂM TRA MẶT NẠ SẠCH**
> * **Chỉ số đo lường (Metric)**: Tổng số thành phần liên thông độc lập của lớp mặt nước (Water Component Count) giảm $\ge 95\%$ so với trước khi lọc.
> * **Kiểm tra trực quan (Visual)**: Không còn các đốm cát li ti trong lòng sông chính, các hồ nước nội đồng nằm ngoài đê sông Hồng bị loại bỏ hoàn toàn.

---

### PHASE 5: WATER–SAND SHARED BOUNDARY EXTRACTION
Trích xuất đường bờ sông thực tế dựa trên ranh giới tiếp xúc trực tiếp giữa nước và cát của dòng chính.

* **Sub-phase 5.1: Polygonization**
  * Chuyển đổi các vùng raster đã lọc sạch của lớp **Water** (hành lang sông chính) và lớp **Sand** thành các đa giác Vector (Polygons).
* **Sub-phase 5.2: Shared Boundary & Multi-Criteria Island Extraction**
  * Tính ranh giới chung giữa đa giác nước dòng chính sông Hồng và đa giác cát bãi bồi:
    $$\text{Shoreline} = \partial(\text{Main\_River\_Water\_Polygon}) \cap \partial(\text{Sand\_Polygon})$$
  * Giải pháp này chỉ trích xuất ranh giới trực tiếp nơi dòng chảy sông Hồng tiếp giáp với bãi cát. Nó chủ động loại bỏ các biên dạng khép kín của đảo (island boundaries) hoặc các vùng đô thị ven sông không chứa cát.
  * **Multi-Criteria Island Filtering (Bộ lọc đảo đa chỉ tiêu)**: Để loại bỏ các đảo giả lập hình thành từ nhiễu phản xạ radar hoặc ao nuôi cá ven sông, hệ thống kiểm tra hai điều kiện:
    1. *Độ tròn (Circularity)*: $\text{Circularity} = (4\pi \times \text{Area}) / \text{Perimeter}^2$. Nếu $\ge 0.8$, đảo bị loại bỏ do có dạng tròn/vuông nhân tạo.
    2. *S2 NDWI Overlap (Độ ngập nước Sentinel-2)*: Tính diện tích giao cắt giữa đa giác đảo và mặt nạ nước quang học từ Sentinel-2 NDWI. Nếu $\ge 50\%$, đảo bị coi là bãi cạn bị ngập nước trong điều kiện quang học bình thường (nhiễu ảnh radar) và bị loại bỏ khỏi danh sách đảo thực tế.
* **Sub-phase 5.3: Active Learning Hotspot Bootstrapping (Học chủ động mở rộng mẫu)**
  * Để khắc phục các điểm nóng có sai số vị trí lớn ($\ge 100\text{ m}$), thuật toán sử dụng script `scripts/expand_training_polys.py` tự động phát hiện các điểm sai số lớn từ kết quả validation, tạo các buffer polygon 30m x 30m tại các tọa độ đó. Script sau đó tự động truy cập GEE để lấy giá trị NDWI/NDVI/NDBI của Sentinel-2 sạch mây, dán nhãn tự động (Nước, Cát, Thực vật, Đô thị) và cập nhật trực tiếp vào bộ mẫu chuẩn `aoi/training_polygons.geojson`.

> [!NOTE]
> **CHECKPOINT PHASE 5: KIỂM TRA RANH GIỚI TIẾP XÚC**
> * **Chỉ số đo lường (Metric)**: Không tồn tại các đường bờ khép kín (closed loops) quanh các đảo không chứa cát hoặc các vùng đô thị ven sông.
> * **Kiểm tra trực quan (Visual)**: Đường bờ chỉ xuất hiện tại các khu vực bãi cát ven bờ và doi cát nổi giữa sông Hồng. Các rìa đê bờ đông/tây đô thị không có bãi cát sẽ không sinh ra shoreline giả.

---

### PHASE 6: SHORELINE CLEANING
Xử lý các lỗi hình học tô-pô trên các đường bờ dạng polyline thu được.

* **Sub-phase 6.1: Graph Construction**
  * Chuyển đổi tập hợp các đường ranh giới vector thành cấu trúc đồ thị (Graph Nodes & Edges).
* **Sub-phase 6.2: Spurious Segment Removal**
  * Xóa các nhánh cụt ngắn (dead-end spurs) và xóa các vòng khép kín nhỏ (loop pruning) hình thành quanh các vũng nước nhỏ trên bãi cát.
* **Sub-phase 6.3: Network Assembly & Snapping**
  * **Keep Longest Connected Network**: Giữ lại các chuỗi đường bờ dài liên kết chặt chẽ.
  * **Snap Vertices**: Ghép nối các đầu mút đường bờ bị đứt đoạn trong khoảng cách ngắn để tạo tính liên tục cho dòng chảy.

> [!NOTE]
> **CHECKPOINT PHASE 6: KIỂM TRA ĐỒ THỊ TOPOLOGY**
> * **Chỉ số đo lường (Metric)**: Thay vì chọn các con số cố định một cách tùy ý (ví dụ: cụt $< 500\text{ m}$ hoặc snap $< 150\text{ m}$), **các tham số này phải được xác định qua hiệu chuẩn thực nghiệm dựa trên các đoạn sông kiểm chứng (validation reaches) hoặc tối ưu hóa qua phân tích độ nhạy (grid search)**.
> * **Kiểm tra trực quan (Visual)**: Các nhánh đứt khúc nhỏ ven bờ bị triệt tiêu, các mút đứt gãy do bóng mây hoặc chân cầu được kết nối liền mạch.

---

### PHASE 7: SHORELINE SMOOTHING & SIMPLIFICATION
Làm mịn đường bờ để đạt tiêu chuẩn trực quan hóa bản đồ và xuất bản nghiên cứu.

* **Sub-phase 7.1: Thứ tự làm mịn (Smoothing Order Rationale)**
  * Thực hiện **Chaikin Smoothing** (2-3 vòng lặp cắt góc để bo tròn các nốt gãy góc $90^\circ$ do lưới pixel raster tạo ra) **TRƯỚC KHI** áp dụng **Douglas-Peucker Simplification**.
  * *Lý do*: Chaikin làm tăng số lượng đỉnh (vertices) bằng cách nội suy mịn tạo đường cong tự nhiên từ các pixel răng cưa ban đầu. Douglas-Peucker (DP) sau đó được sử dụng để giảm số lượng đỉnh bằng cách loại bỏ các đỉnh thừa thẳng hàng. Trình tự này bảo đảm đường bờ có dạng hình học trơn mượt vật lý và tối ưu hóa dung lượng lưu trữ vector mà không làm mất cấu trúc topo gốc.
* **Sub-phase 7.2: Douglas-Peucker Simplification**
  * Áp dụng thuật toán đơn giản hóa hình học **Douglas-Peucker** với ngưỡng dung sai nhỏ (Tolerance $2-5\text{ m}$) để giảm số lượng đỉnh dư thừa.

> [!NOTE]
> **CHECKPOINT PHASE 7: KIỂM TRA ĐỘ MƯỢT VÀ SAI LỆCH HÌNH HỌC**
> * **Chỉ số đo lường (Metric)**: Số lượng đỉnh (vertices) giảm $\ge 60\%$. Khoảng cách lệch Hausdorff cực đại giữa đường bờ gốc và đường bờ làm mịn xấp xỉ một pixel ($\approx 10\text{ m}$).
> * **Kiểm tra trực quan (Visual)**: Đường bờ mềm mại, tự nhiên, không còn răng cưa pixel.

---

### PHASE 8: FINAL QUALITY CONTROL AND SHORELINE VALIDATION
Quy trình kiểm chứng cuối cùng để xác nhận đường bờ đã đạt chất lượng nghiên cứu cao nhất trước khi xuất kết quả.

* **Sub-phase 8.1: Visual Overlay Check**
  * Chồng xếp đường bờ trích xuất lên ảnh quang học Sentinel-2 sạch mây (True Color/False Color) chụp cùng thời kỳ để kiểm tra mức độ trùng khớp tại các vùng nhạy cảm.
* **Sub-phase 8.2: Shoreline Positional Accuracy (Đo đạc sai số vị trí đường bờ)**
  * Sử dụng các chỉ số hình học chuyên dụng để đánh giá sai số vị trí đường bờ so với dữ liệu kiểm chứng thực địa hoặc ảnh quang học độ phân giải cao:
    * **Mean Distance (Khoảng cách trung bình)**: Sai lệch khoảng cách trung bình giữa hai đường bờ.
    * **RMSE (Sai số trung bình bình phương)**: Thể hiện mức độ biến động sai lệch vị trí đường bờ.
    * **Hausdorff Distance**: Khoảng cách lệch cục bộ lớn nhất giữa đường bờ trích xuất và tham chiếu.
    * **95th Percentile Distance**: Khoảng cách sai lệch tại phân vị thứ 95 để loại trừ nhiễu biên cực đoan.
* **Sub-phase 8.3: Quy trình Manual QC (Quy trình kiểm chứng thủ công)**
  * Sử dụng công cụ bản đồ tương tác (Folium/Leaflet) chồng xếp ảnh nền SAR VV, Classification Raster (có opacity slider), đường bờ thô (màu đỏ đứt nét) và đường bờ mịn (xanh lục).
  * Chuyên gia rà quét từ Sơn Tây đến Phú Xuyên ở zoom 14–16. Phát hiện các điểm nóng lỗi (như chân cầu, doi cát ngầm mùa mưa có tán xạ yếu).
  * Nếu sai lệch vượt quá $30\text{ m}$, ghi nhận tọa độ, điều chỉnh tham số lọc topo hoặc bổ sung mẫu huấn luyện tại vùng lỗi để retrain mô hình.

---

## ĐỀ XUẤT CẤU TRÚC LUẬN VĂN/PAPER: CHƯƠNG 4 – ĐÁNH GIÁ THỰC NGHIỆM (EXPERIMENTAL EVALUATION)

Để bảo đảm tính rõ ràng và mạch lạc của bài báo, các phân tích thống kê và đánh giá hiệu năng thuật toán sẽ được trình bày riêng biệt tại Chương thực nghiệm (Experiments/Results):

### 4.1 Classification Accuracy (Độ chính xác phân loại & Độ không chắc chắn)
* Trình bày kết quả kiểm chứng chéo 5-fold (5-fold CV) trên tập mẫu huấn luyện Random Forest.
* Báo cáo giá trị trung bình (Mean) và độ lệch chuẩn (Std) của Overall Accuracy, Precision, Recall, và F1-score (đặc biệt cho lớp Sand) chạy qua 10 hạt ngẫu nhiên (random seeds) khác nhau nhằm chứng minh tính ổn định của mô hình.

### 4.2 Shoreline Positional Accuracy (Độ chính xác vị trí đường bờ)
* Báo cáo chi tiết các chỉ số hình học: Mean Distance, RMSE, Hausdorff Distance, và 95th Percentile của đường bờ cuối cùng so với các đoạn sông tham chiếu để chứng thực sai số vật lý.

### 4.3 Parameter Sensitivity (Phân tích độ nhạy tham số)
* Đánh giá độ ảnh hưởng của các tham số chính đến sai số RMSE đường bờ cuối cùng:
  * Kích thước cửa sổ lọc Lee (5×5, 7×7, 9×9)
  * Cửa sổ tính GLCM (3×3, 5×5, 7×7)
  * Khoảng cách snap dọn dẹp đồ thị shoreline (50m, 100m, 150m)
  * Bán kính đĩa lọc hình thái opening và closing (ví dụ: 1–4 pixels)
* Chứng minh việc lựa chọn tham số tối ưu thông qua tìm kiếm lưới (grid search).

### 4.4 Ablation Study (Đánh giá hiệu quả từng bước xử lý)
* Phân tích vai trò và đóng góp định lượng của từng module hậu xử lý (Lọc hình thái Morphological, Connected Component dòng chảy chính, dọn dẹp đồ thị đường bờ) trong việc giảm thiểu sai số hình học và topology.

### 4.5 Multi-temporal Shoreline Analysis (Phân tích biến động đa thời gian)
* Áp dụng thuật toán trích xuất đường bờ cho chuỗi thời gian nhiều năm (2020, 2021, 2022, 2023, 2024) và phân tích biến động lòng sông/bãi bồi giữa mùa khô (Dry composites) và mùa lũ (Wet composites).
* Liên hệ kết quả với mực nước và lưu lượng từ trạm đo thủy văn để chứng thực quy luật thủy văn tự nhiên.

---

## KẾ HOẠCH TRIỂN KHAI MÃ NGUỒN

Khi bắt đầu triển khai Phase 3, chúng ta sẽ xây dựng các mô-đun mã nguồn sạch theo cấu trúc:
1. `src/classification.py`: Thực hiện huấn luyện RF, trích xuất GLCM texture và phân loại ảnh vệ tinh.
2. `src/shoreline.py`: Thực hiện hậu xử lý hình thái raster, trích xuất đường ranh giới chung và tối ưu đồ thị topo.
3. `scripts/train_classifier.py`: Script điều phối chạy mô hình huấn luyện trên GEE.
4. `scripts/extract_research_shoreline.py`: Script chạy quy trình trích xuất đường bờ nghiên cứu và so sánh biến động.
