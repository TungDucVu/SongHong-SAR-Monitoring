"""
SongHong-SAR-Monitoring: Unified Production Entrypoint (v1.0-OptionA-Production)

Giám sát biến động đường bờ và bãi bồi Sông Hồng (171.84 km) bằng dữ liệu Sentinel-1 SAR.

Sử dụng:
  python main.py --reach all               # Chạy toàn bộ Reach 1, 2, 3 và vẽ bản đồ Master Hybrid
  python main.py --reach 1                 # Chạy riêng Reach 1 (Thượng lưu)
  python main.py --reach 2                 # Chạy riêng Reach 2 (Trung lưu)
  python main.py --reach 3                 # Chạy riêng Reach 3 (Hạ lưu)
  python main.py --hybrid                  # Cập nhật bản đồ tương tác Hybrid Master cho toàn sông
  python main.py --full-composite --years 2017-2026 # Tự động chạy trích xuất chuỗi thời gian 10 năm
"""

import os
import sys
import argparse
import subprocess

# Ensure project root in sys.path
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.append(PROJECT_ROOT)

def run_script(script_path):
    print(f"\n🚀 Khởi chạy: {script_path}...")
    result = subprocess.run([sys.executable, script_path], cwd=PROJECT_ROOT)
    if result.returncode != 0:
        print(f"❌ Lỗi khi thực thi: {script_path}")
        sys.exit(result.returncode)

def main():
    parser = argparse.ArgumentParser(
        description="SongHong SAR Monitoring Pipeline (v1.0-OptionA-Production)"
    )
    parser.add_argument(
        '--reach', choices=['1', '2', '3', 'all'],
        help="Chọn phân đoạn sông chạy mô hình (1, 2, 3, hoặc all)"
    )
    parser.add_argument(
        '--hybrid', action='store_true',
        help="Cập nhật bản đồ tương tác Master Hybrid cho toàn bộ 3 Reach"
    )
    parser.add_argument(
        '--full-composite', action='store_true',
        help="Khởi chạy tự động trích xuất chuỗi thời gian nhiều năm (2017-2026)"
    )
    
    args = parser.parse_args()
    
    # If no argument is provided, default to --reach all
    if not any([args.reach, args.hybrid, args.full_composite]):
        print("📌 Không chỉ định tham số. Mặc định khởi chạy toàn hệ thống: --reach all")
        args.reach = 'all'

    if args.reach == '1':
        run_script(os.path.join("main_workflow", "run_reach1_local.py"))
    elif args.reach == '2':
        run_script(os.path.join("main_workflow", "run_reach2_local.py"))
    elif args.reach == '3':
        run_script(os.path.join("main_workflow", "run_reach3_local.py"))
    elif args.reach == 'all':
        run_script(os.path.join("main_workflow", "run_reach1_local.py"))
        run_script(os.path.join("main_workflow", "run_reach2_local.py"))
        run_script(os.path.join("main_workflow", "run_reach3_local.py"))
        run_script(os.path.join("scripts", "plot_hybrid_map.py"))
        
    if args.hybrid and args.reach != 'all':
        run_script(os.path.join("scripts", "plot_hybrid_map.py"))
        
    if args.full_composite:
        run_script(os.path.join("scripts", "extract_research_shoreline.py"))

    print("\n✅ Hoàn thành thực thi thành công!")

if __name__ == "__main__":
    main()
