#!/usr/bin/env python3
import sys
import subprocess
result = subprocess.run(['python3', 'scripts/batch_verify.py'], 
                       capture_output=True, text=True, cwd='.')
output = result.stdout
lines = output.split('\n')
for line in lines:
    if '总准确率' in line or '准确率:' in line or 'Balanced' in line and '准确率' in line:
        print(line)

