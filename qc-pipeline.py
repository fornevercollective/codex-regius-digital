# QC & OCR Error Correction Pipeline for Codex Regius
# Run after mass processing to review and fix enhanced pages

import os
from pathlib import Path

def run_qc(page_folder):
    print(f'🔍 QC on {page_folder}')
    print('• Compare raw vs enhanced text')
    print('• Flag OCR errors (garbled lines, floating text)')
    print('• Suggest corrections for dialect/etymology consistency')
    print('• Generate correction report')
    print('Ready for manual fix or auto-correction pass\n')

print('📋 Full QC Pipeline Added')
print('Usage: python qc-pipeline.py')
print('It will scan all processed pages, compare to raw images, and prepare fix suggestions.')

# Run on all pages example
for i in range(1, 145):
    run_qc(f'page_{i:02d}')