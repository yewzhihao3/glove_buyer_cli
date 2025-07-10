#!/usr/bin/env python3
"""
Test script to verify the truncation function works correctly
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from utils.display import truncate_company_name

def test_truncation():
    """Test the truncation function with various company names"""
    
    test_cases = [
        ("Short Company", 30, "Short Company"),
        ("Very Long Company Name That Should Be Truncated", 30, "Very Long Company Name That Sho..."),
        ("Another Very Long Company Name With Many Words", 25, "Another Very Long Company..."),
        ("", 30, ""),
        ("Medium Company Name", 20, "Medium Company Name..."),
        ("Exact Length Company Name", 25, "Exact Length Company Name"),
    ]
    
    print("Testing truncation function:")
    print("=" * 50)
    
    for company_name, max_length, expected in test_cases:
        result = truncate_company_name(company_name, max_length)
        status = "✓" if result == expected else "✗"
        print(f"{status} Input: '{company_name}' (max: {max_length})")
        print(f"   Output: '{result}'")
        print(f"   Expected: '{expected}'")
        print()

if __name__ == "__main__":
    test_truncation() 