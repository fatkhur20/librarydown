#!/usr/bin/env python3
"""
Test script to verify cookie validation functionality
"""

import sys
import os
sys.path.insert(0, '/root/librarydown')

from src.bot_cookie_manager import validate_netscape_cookies

def test_cookie_validation():
    # Test cases for Netscape cookie format
    valid_cookie_content = """# Netscape HTTP Cookie File
# This is a generated file!  Do not edit.
.youtube.com	TRUE	/	FALSE	2147483647	SID	abc123def456
.youtube.com	TRUE	/	FALSE	2147483647	HSID	def456ghi789
.google.com	TRUE	/	TRUE	2147483647	GAPS	xyz789abc123
"""
    
    invalid_cookie_content = """# This is not a netscape format
invalid
cookie
content
"""
    
    mixed_content = """# Netscape HTTP Cookie File
.youtube.com	TRUE	/	FALSE	2147483647	SID	abc123def456
invalid_line
.google.com	TRUE	/	TRUE	2147483647	GAPS	xyz789abc123
"""
    
    print("Testing cookie validation...")
    
    print("\n1. Testing valid cookie content:")
    result = validate_netscape_cookies(valid_cookie_content)
    print(f"Result: {result} (Expected: True)")
    
    print("\n2. Testing invalid cookie content:")
    result = validate_netscape_cookies(invalid_cookie_content)
    print(f"Result: {result} (Expected: False)")
    
    print("\n3. Testing mixed content:")
    result = validate_netscape_cookies(mixed_content)
    print(f"Result: {result} (Expected: True - has at least 1 valid cookie)")
    
    # Test edge cases
    print("\n4. Testing minimal valid cookie:")
    minimal = ".example.com	TRUE	/	FALSE	2147483647	name	value\n"
    result = validate_netscape_cookies(minimal)
    print(f"Result: {result} (Expected: True)")
    
    print("\n5. Testing empty content:")
    result = validate_netscape_cookies("")
    print(f"Result: {result} (Expected: False)")
    
    print("\n6. Testing just comments:")
    comments_only = "# Comment 1\n# Comment 2\n# Comment 3\n"
    result = validate_netscape_cookies(comments_only)
    print(f"Result: {result} (Expected: False)")

if __name__ == "__main__":
    test_cookie_validation()
    print("\nCookie validation test completed!")