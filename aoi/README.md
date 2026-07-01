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

## Tự động upload lên GEE Assets

Mô-đun `src/aoi.py` tích hợp sẵn phương thức tải GeoJSON này lên GEE Asset của dự án thông qua Python API. Khi chạy notebook `week1_pipeline.ipynb`, AOI sẽ tự động được kiểm tra và upload nếu chưa tồn tại.
