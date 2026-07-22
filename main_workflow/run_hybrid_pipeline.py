"""
Master Main Workflow Pipeline Runner (SongHong SAR Shoreline Monitoring)

Executes:
1. Reach 1 Local RF Model (Upper Reach)
2. Reach 2 & 3 Global RF Model (Middle & Lower Reaches)
3. Regenerates Unified Interactive Maps (via plot_hybrid_map.py)
"""

import os
import sys
import subprocess
import ee

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.config import GEE_PROJECT
from main_workflow.run_reach1_local import main as run_reach1
from main_workflow.run_reach2_3_global import main as run_reach2_3

def main():
    print("=============================================================")
    print(" SONG HONG SAR MONITORING: MASTER PIPELINE RUNNER")
    print("=============================================================")
    
    ee.Initialize(project=GEE_PROJECT)
    
    print("\n[Step 1/3] Running Reach 1 Local RF Model...")
    run_reach1()
    
    print("\n[Step 2/3] Running Reach 2 & 3 Global RF Model...")
    run_reach2_3()
    
    print("\n[Step 3/3] Generating Unified Hybrid Interactive Maps...")
    plot_script = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "scripts", "plot_hybrid_map.py")
    subprocess.run([sys.executable, plot_script, "--year", "2024"], check=True)
    
    print("\n[SUCCESS] Full Hybrid Pipeline execution complete for 2024 (Dry & Wet seasons)!")

if __name__ == "__main__":
    main()
