"""
Multi-Year Seasonal Report Generator (2017 - 2026)

Parses all .config/{year}_{season}_stats.md files or calculates validation metrics across
all 20 seasonal runs (2017-2026 Dry & Wet), generating a comprehensive publication-grade report.
"""

import os
import sys
import glob
import re
import pandas as pd

if sys.platform == 'win32':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')
    except Exception:
        pass

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(PROJECT_ROOT)

def parse_stats_file(file_path):
    if not os.path.exists(file_path):
        return None
        
    metrics = {}
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
        
    mean_m = re.search(r'- \*\*Mean Error\*\*: ([\d\.]+) m', content)
    median_m = re.search(r'- \*\*Median \(P50\) Error\*\*: ([\d\.]+) m', content)
    rmse_m = re.search(r'- \*\*RMSE\*\*: ([\d\.]+) m', content)
    hausdorff_m = re.search(r'- \*\*Hausdorff Distance\*\*: ([\d\.]+) m', content)
    p95_m = re.search(r'- \*\*95th Percentile \(P95\)\*\*: ([\d\.]+) m', content)
    
    if mean_m and rmse_m:
        metrics['Mean Error (m)'] = float(mean_m.group(1))
        metrics['Median Error (m)'] = float(median_m.group(1)) if median_m else 0.0
        metrics['RMSE (m)'] = float(rmse_m.group(1))
        metrics['Hausdorff (m)'] = float(hausdorff_m.group(1)) if hausdorff_m else 0.0
        metrics['P95 Error (m)'] = float(p95_m.group(1)) if p95_m else 0.0
        return metrics
    return None

def generate_report(start_year=2017, end_year=2026):
    config_dir = os.path.join(PROJECT_ROOT, '.config')
    outputs_dir = os.path.join(PROJECT_ROOT, 'outputs')
    records = []
    
    for yr in range(start_year, end_year + 1):
        for ssn in ['dry', 'wet']:
            csv_candidates = [
                os.path.join(outputs_dir, str(yr), f"{yr}_{ssn}", "stats", f"validation_statistics_{yr}_{ssn}.csv"),
                os.path.join(outputs_dir, str(yr), f"{yr}_{ssn}", f"validation_statistics_{yr}_{ssn}.csv"),
                os.path.join(config_dir, f"{yr}_{ssn}_stats.md")
            ]
            
            m = None
            for cp in csv_candidates:
                if os.path.exists(cp):
                    if cp.endswith(".csv"):
                        try:
                            cdf = pd.read_csv(cp)
                            if not cdf.empty:
                                row = cdf.iloc[0]
                                m = {
                                    'Mean Error (m)': float(row.get('Mean_Error_m', row.get('Mean', 0.0))),
                                    'Median Error (m)': float(row.get('Median_Error_m', row.get('Median', 0.0))),
                                    'RMSE (m)': float(row.get('RMSE_m', row.get('RMSE', 0.0))),
                                    'P95 Error (m)': float(row.get('P95_Error_m', row.get('P95', 0.0))),
                                    'Hausdorff (m)': float(row.get('Hausdorff_m', row.get('Hausdorff', 0.0)))
                                }
                                break
                        except Exception:
                            pass
                    elif cp.endswith(".md"):
                        m = parse_stats_file(cp)
                        if m:
                            break
                            
            if m:
                records.append({
                    'Year': yr,
                    'Season': ssn.upper(),
                    'Mean Error (m)': m['Mean Error (m)'],
                    'Median Error (m)': m['Median Error (m)'],
                    'RMSE (m)': m['RMSE (m)'],
                    'P95 Error (m)': m['P95 Error (m)'],
                    'Hausdorff (m)': m['Hausdorff (m)'],
                    'Status': 'SUCCESS'
                })
            else:
                records.append({
                    'Year': yr,
                    'Season': ssn.upper(),
                    'Mean Error (m)': None,
                    'Median Error (m)': None,
                    'RMSE (m)': None,
                    'P95 Error (m)': None,
                    'Hausdorff (m)': None,
                    'Status': 'PENDING'
                })
                
    df = pd.DataFrame(records)
    
    report_md = f"""# Báo Cáo Tổng Hợp Trích Xuất Đường Bờ Chuỗi Thời Gian (2017 – 2026)

Bảng tổng hợp chỉ số kiểm chứng vị trí (Positional Validation Metrics) cho 20 mùa (10 năm × 2 mùa) đối chiếu trực tiếp với dữ liệu tham chiếu Sentinel-2 MNDWI:

| Năm (Year) | Mùa (Season) | Mean Error (m) | Median Error (m) | RMSE (m) | P95 Error (m) | Hausdorff (m) | Trạng Thái |
| :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
"""
    for _, row in df.iterrows():
        if row['Mean Error (m)'] is not None:
            report_md += f"| {row['Year']} | **{row['Season']}** | {row['Mean Error (m)']:.2f} | {row['Median Error (m)']:.2f} | **{row['RMSE (m)']:.2f}** | {row['P95 Error (m)']:.2f} | {row['Hausdorff (m)']:.2f} | {row['Status']} |\n"
        else:
            report_md += f"| {row['Year']} | **{row['Season']}** | - | - | - | - | - | {row['Status']} |\n"
            
    out_path = os.path.join(PROJECT_ROOT, "outputs", "REPORT", "multiyear_shoreline_summary_report.md")
    docs_path = os.path.join(PROJECT_ROOT, "docs", "multiyear_shoreline_summary_report.md")
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    os.makedirs(os.path.dirname(docs_path), exist_ok=True)
    
    with open(out_path, 'w', encoding='utf-8') as f:
        f.write(report_md)
    with open(docs_path, 'w', encoding='utf-8') as f:
        f.write(report_md)
        
    print(f"[Report] Saved consolidated multi-year report to: {out_path} and {docs_path}")
    print("\n" + df.to_string(index=False))


if __name__ == '__main__':
    generate_report()
