"""
Master Main Workflow Pipeline Runner (SongHong SAR Shoreline Monitoring)

Executes 3 Dedicated RF Models (1/3 River Corridor Each):
1. Reach 1 Local RF Model (Upper Reach: Ba Vi / Son Tay)
2. Reach 2 Local RF Model (Middle Reach: Urban Hanoi Corridor)
3. Reach 3 Local RF Model (Lower Reach: Agricultural Delta)
4. Regenerates Unified Interactive Maps (via plot_hybrid_map.py)
"""

import os
import sys
import subprocess
import ee

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.config import GEE_PROJECT
from main_workflow.run_reach1_local import main as run_reach1
from main_workflow.run_reach2_local import main as run_reach2
from main_workflow.run_reach3_local import main as run_reach3

def main():
    import argparse
    parser = argparse.ArgumentParser(description="Master Pipeline Runner for 3 Reaches")
    parser.add_argument("--year", type=int, default=2024, help="Year to process (2017-2026)")
    parser.add_argument("--all_years", action="store_true", help="Process all years 2017 to 2026")
    args = parser.parse_args()

    print("=============================================================")
    print(" SONG HONG SAR MONITORING: MASTER PIPELINE RUNNER (3 REACHES)")
    print("=============================================================")
    
    ee.Initialize(project=GEE_PROJECT)
    target_years = range(2017, 2027) if args.all_years else [args.year]
    plot_script = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "scripts", "plot_hybrid_map.py")

    for yr in target_years:
        print(f"\n>>> PROCESSING YEAR {yr} ACROSS ALL 3 REACHES <<<")
        print("\n[Step 1/4] Running Reach 1 Local RF Model (Upper)...")
        subprocess.run([sys.executable, "-m", "main_workflow.run_reach1_local", "--year", str(yr)], check=True)
        
        print("\n[Step 2/4] Running Reach 2 Local RF Model (Urban Hanoi)...")
        subprocess.run([sys.executable, "-m", "main_workflow.run_reach2_local", "--year", str(yr)], check=True)
        
        print("\n[Step 3/4] Running Reach 3 Local RF Model (Delta)...")
        subprocess.run([sys.executable, "-m", "main_workflow.run_reach3_local", "--year", str(yr)], check=True)
        
        print(f"\n[Step 4/4] Generating Unified Hybrid Interactive Maps for {yr}...")
        subprocess.run([sys.executable, plot_script, "--year", str(yr)], check=True)
    
    print("\n[SUCCESS] Full 3-Reach Hybrid Pipeline execution complete!")

if __name__ == "__main__":
    main()

