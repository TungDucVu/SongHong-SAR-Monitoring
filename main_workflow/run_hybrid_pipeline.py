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
    print("=============================================================")
    print(" SONG HONG SAR MONITORING: MASTER PIPELINE RUNNER (3 REACHES)")
    print("=============================================================")
    
    ee.Initialize(project=GEE_PROJECT)
    
    print("\n[Step 1/4] Running Reach 1 Local RF Model (Upper)...")
    run_reach1()
    
    print("\n[Step 2/4] Running Reach 2 Local RF Model (Urban Hanoi)...")
    run_reach2()
    
    print("\n[Step 3/4] Running Reach 3 Local RF Model (Delta)...")
    run_reach3()
    
    print("\n[Step 4/4] Generating Unified Hybrid Interactive Maps...")
    plot_script = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "scripts", "plot_hybrid_map.py")
    subprocess.run([sys.executable, plot_script, "--year", "2024"], check=True)
    
    print("\n[SUCCESS] Full 3-Reach Hybrid Pipeline execution complete for 2024 (Dry & Wet seasons)!")

if __name__ == "__main__":
    main()

