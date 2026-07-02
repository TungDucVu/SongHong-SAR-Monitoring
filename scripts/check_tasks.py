import sys
import os

sys.path.insert(0, os.getcwd())

import ee
from src.config import GEE_PROJECT

ee.Initialize(project=GEE_PROJECT)
operations = ee.data.listOperations()

print("=== RECENT GEE TASKS ===")
for op in operations[:20]:
    metadata = op.get('metadata', {})
    description = metadata.get('description', 'Unknown')
    state = metadata.get('state', 'Unknown')
    task_id = op.get('name', '').split('/')[-1]
    print(f"Task: {description} | State: {state} | ID: {task_id}")
