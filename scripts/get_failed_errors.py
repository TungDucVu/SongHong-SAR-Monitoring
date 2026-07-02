import sys
import os

sys.path.insert(0, os.getcwd())

import ee
from src.config import GEE_PROJECT

ee.Initialize(project=GEE_PROJECT)
operations = ee.data.listOperations()

print("=== GEE TASK ERRORS ===")
for op in operations[:20]:
    metadata = op.get('metadata', {})
    description = metadata.get('description', 'Unknown')
    state = metadata.get('state', 'Unknown')
    error = op.get('error', {})
    error_msg = error.get('message', 'No error message')
    print(f"Task: {description} | State: {state} | Error: {error_msg}")
