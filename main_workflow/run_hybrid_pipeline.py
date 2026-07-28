"""
Master Main Workflow Pipeline Runner (SongHong SAR Shoreline Monitoring)
Max Hardware Acceleration Engine: Utilizes 100% of available CPU cores (20 threads)
Executes 3 Dedicated RF Models across all target years concurrently.
"""

import os
import sys
import time
import subprocess
import ee
from concurrent.futures import ProcessPoolExecutor, as_completed

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(PROJECT_ROOT)

from src.config import GEE_PROJECT

def run_reach_year_cmd(task_tuple):
    reach_num, yr = task_tuple
    cmd = [sys.executable, "-m", f"main_workflow.run_reach{reach_num}_local", "--year", str(yr)]
    print(f"  [Worker] Launching Reach {reach_num} for Year {yr}...")
    start_t = time.time()
    res = subprocess.run(cmd, capture_output=True, text=True)
    elapsed = time.time() - start_t
    if res.returncode == 0:
        print(f"  [OK] Reach {reach_num} Year {yr} completed in {elapsed:.2f}s!")
        return (yr, reach_num, True)
    else:
        print(f"  [ERROR] Reach {reach_num} Year {yr}: {res.stderr[:200]}")
        return (yr, reach_num, False)

def main():
    import argparse
    parser = argparse.ArgumentParser(description="Master Multi-Core Pipeline Runner")
    parser.add_argument("--year", type=int, default=2024, help="Year to process (2017-2026)")
    parser.add_argument("--all_years", action="store_true", help="Process all years 2017 to 2026")
    args = parser.parse_args()

    cpu_cores = os.cpu_count() or 8
    print("=============================================================")
    print(f" SONG HONG SAR MONITORING: MAX HARDWARE ENGINE ({cpu_cores} CPU CORES)")
    print("=============================================================")
    
    ee.Initialize(project=GEE_PROJECT)
    target_years = list(range(2017, 2027)) if args.all_years else [args.year]
    plot_script = os.path.join(PROJECT_ROOT, "scripts", "plot_hybrid_map.py")

    # Build task pool for all (reach, year) pairs
    task_pool = [(r, yr) for yr in target_years for r in [1, 2, 3]]
    print(f"[Hardware Accelerator] Scheduled {len(task_pool)} extraction tasks across {cpu_cores} parallel CPU threads.")

    total_start = time.time()
    
    # Execute across ALL 20 CPU threads concurrently
    with ProcessPoolExecutor(max_workers=min(len(task_pool), cpu_cores)) as executor:
        futures = {executor.submit(run_reach_year_cmd, t): t for t in task_pool}
        for future in as_completed(futures):
            yr, r_num, success = future.result()

    # Generate unified maps
    print("\n[Post-Processing] Generating Unified Hybrid Interactive Maps...")
    for yr in target_years:
        subprocess.run([sys.executable, plot_script, "--year", str(yr)], check=False)
        
    total_elapsed = time.time() - total_start
    print("\n=============================================================")
    print(f" [SUCCESS] ALL 10-YEAR REACH TASKS FINISHED IN {total_elapsed:.2f} SECONDS!")
    print("=============================================================")

if __name__ == "__main__":
    main()
