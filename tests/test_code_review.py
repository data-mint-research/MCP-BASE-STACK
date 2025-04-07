#!/usr/bin/env python3
"""
Test file for the automated code review tool.
"""

import os
import sys
from typing import List, Dict, Any

# Unused import
import json

# Security issue: using a hardcoded password
PASSWORD = "hardcoded_password"

def calculate_sum(numbers):
    # Missing type annotations
    total = 0
    for num in numbers:
        total += num
    return total

# Function with too many arguments
def process_data(arg1, arg2, arg3, arg4, arg5, arg6, arg7, arg8):
    # Missing docstring
    result = {}
    
    # Unused variable
    unused_var = "This is not used"
    
    # Line too long - this line is intentionally made very long to trigger a line length warning in the code review tool
    result["data"] = arg1 + arg2 + arg3 + arg4 + arg5 + arg6 + arg7 + arg8
    
    return result

class DataProcessor:
    # Class missing docstring
    
    def __init__(self, data_source):
        # Missing type annotation
        self.data_source = data_source
        self.processed = False
    
    def process(self):
        # Method missing docstring
        data = self.data_source.get_data()
        
        # Security issue: using eval
        result = eval(data)
        
        self.processed = True
        return result

# Execute shell command without checking output
def run_command(cmd):
    os.system(cmd)  # Security issue: shell injection vulnerability

if __name__ == "__main__":
    numbers = [1, 2, 3, 4, 5]
    print(f"Sum: {calculate_sum(numbers)}")