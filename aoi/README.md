# AOI — Song Hong (Red River) Corridor, Ha Noi

## Thông tin file

| Thuộc tính | Giá trị |
|---|---|
| File | `song_hong_aoi.geojson` |
| Hệ tọa độ | WGS84 / EPSG:4326 |
| Diện tích ước tính | ~500 km² |
| Đoạn sông bao phủ | Sơn Tây → Phú Xuyên (~80 km) |
| Buffer hai bờ | ~2 km |

## Các khu vực trọng điểm nằm trong AOI

- **Nhật Tân** (~21.08°N, 105.83°E) — Cầu Nhật Tân, bãi bồi phía Bắc
- **Long Biên** (~21.04°N, 105.87°E) — Cầu Long Biên, biến động đường bờ rõ nét
- **Vĩnh Tuy** (~20.99°N, 105.89°E) — Cầu Vĩnh Tuy, bãi cát giữa sông

## Upload lên GEE Assets

```bash
# Dùng Earth Engine CLI
earthengine upload table \
  --asset_id=projects/crested-library-500309-i2/assets/aoi \
  aoi/song_hong_aoi.geojson
```

Hoặc vào [code.earthengine.google.com](https://code.earthengine.google.com) → **Assets** → **New** → **Shape files** → upload file này.

## Ghi chú

- Polygon được vẽ thủ công dựa trên hình thái sông từ Google Maps.
- Cần kiểm tra lại bằng `scripts/00_environment_check.py` để đảm bảo AOI phủ đủ ảnh Sentinel-1.
- Nếu cần mở rộng (ví dụ thêm đoạn Hưng Yên), chỉnh sửa trực tiếp tại [geojson.io](https://geojson.io).
