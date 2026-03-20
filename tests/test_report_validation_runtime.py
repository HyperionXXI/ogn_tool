
import sys
import os
import json

# Ensure src is in sys.path for ogn_tool imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), 'src')))
from ogn_tool.reporting.report_validation import validate_report

report = json.load(open('data/runs/analysis_runs/fk50887_2026_03_11_091356_72h_offset128h/report.json'))
warnings = validate_report(report)
print('Validation warnings:', warnings)
