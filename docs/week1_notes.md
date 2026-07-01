# Ghi chú kỹ thuật — Tuần 1

**Tác giả:** Vũ Đức Tùng  
**Thời gian:** 01/07/2026 – 07/07/2026  
**Mục tiêu:** Chuẩn bị dữ liệu & Thiết lập môi trường GEE

---

## 1. Cấu hình GEE

| Tham số | Giá trị |
|---|---|
| Project ID | `crested-library-500309-i2` |
| Dataset | `COPERNICUS/S1_GRD` |
| Instrument Mode | `IW` (Interferometric Wide) |
| Orbit Direction | `DESCENDING` |
| Bands | `VV`, `VH` |
| Thời gian | 2015-01-01 → 2024-12-31 |
| Resolution | 10m (native Sentinel-1) |
| CRS export | `EPSG:32648` (UTM Zone 48N) |

---

## 2. AOI — Phạm vi nghiên cứu

- File: `aoi/song_hong_aoi.geojson`
- Hệ tọa độ: WGS84 / EPSG:4326
- Đoạn sông: Sơn Tây → Phú Xuyên (~80 km)
- Buffer mỗi bên: ~2 km
- Diện tích: ~500 km²
- Các khu vực trọng điểm: Nhật Tân, Long Biên, Vĩnh Tuy

### Cách upload AOI lên GEE Assets

```bash
earthengine upload table \
  --asset_id=projects/crested-library-500309-i2/assets/aoi \
  aoi/song_hong_aoi.geojson
```

---

## 3. Pipeline tiền xử lý

### 3.1 Bộ lọc Speckle — Refined Lee (3×3)

Sentinel-1 GRD dữ liệu bị nhiễu speckle do tính chất coherent của sóng radar. Bộ lọc Lee làm giảm speckle trong khi bảo toàn biên cạnh.

**Công thức:**
```
filtered = mean + w × (pixel - mean)
w = 1 - σ²_ENL / (σ²_local/μ²_local + σ²_ENL)
ENL = 4.9 (Sentinel-1 IW)
```

### 3.2 Tính đặc trưng

| Đặc trưng | Công thức | Ý nghĩa |
|---|---|---|
| `VV` | VV band (dB) | Nhạy với bề mặt nước, nhám mặt đất |
| `VH` | VH band (dB) | Nhạy với thể tích tán xạ (cây, bãi cát) |
| `VV_VH_ratio` | VV(dB) - VH(dB) | Phân biệt nước vs đất vs thực vật |

### 3.3 Giá trị đặc trưng tham chiếu

| Lớp | VV (dB) | VH (dB) | Ratio (dB) |
|---|---|---|---|
| **Mặt nước** | < −15 | < −20 | ~5–8 |
| **Bãi bồi/Cát** | −15 đến −10 | −20 đến −15 | ~5–7 |
| **Đất/Thảm thực vật** | > −10 | > −15 | ~8–15 |
| **Khu đô thị** | > −5 | > −10 | ~8–12 |

---

## 4. Vấn đề kỹ thuật đã gặp

*(Cập nhật trong quá trình thực hiện)*

| Ngày | Vấn đề | Giải pháp |
|---|---|---|
| — | — | — |

---

## 5. Kết quả kiểm tra

*(Điền vào sau khi chạy từng script)*

### Script 00
- [ ] GEE khởi tạo thành công
- [ ] AOI hiển thị đúng trên bản đồ
- [ ] Sentinel-1 2024 có **___** ảnh

### Script 01
- [ ] Tổng ảnh 2015–2024: **___**
- [ ] Không năm nào = 0 ảnh

### Script 02
- [ ] VV mặt nước tháng 1/2024: **___** dB (cần < −15)
- [ ] VV đất tháng 1/2024: **___** dB (cần > −10)

### Script 04
- [ ] 3 export tasks submitted
- [ ] GeoTIFF download về máy
- [ ] Mở được bằng QGIS

---

## 6. References

- [Sentinel-1 GRD GEE Docs](https://developers.google.com/earth-engine/datasets/catalog/COPERNICUS_S1_GRD)
- [Refined Lee Filter GEE](https://github.com/adugnag/gee_s1_ard)
- [SAR Water Detection — Otsu Threshold](https://doi.org/10.3390/rs12010015)
- [Song Hong River Morphology Studies](https://doi.org/10.1016/j.geomorph.2020.107423)
