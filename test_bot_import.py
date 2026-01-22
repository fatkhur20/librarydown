#!/usr/bin/env python3
"""
Quick test to verify bot module can be imported
"""

import sys
import os

# Add the librarydown directory to Python path
sys.path.insert(0, '/root/librarydown')

try:
    from src.bot_cookie_manager import validate_netscape_cookies, deploy_cookie_file
    print("✅ Successfully imported bot modules")
    
    # Test basic functionality
    test_cookie = ".test.com	TRUE	/	FALSE	2147483647	test	value\n"
    result = validate_netscape_cookies(test_cookie)
    print(f"✅ Cookie validation test: {result}")
    
    print("\n✅ Bot module verification successful!")
    print("The bot is ready to be started with: python3 -m src.bot_cookie_manager")
    
except ImportError as e:
    print(f"❌ Import error: {e}")
    print("Make sure telegram library is installed: pip3 install python-telegram-bot")
    
except Exception as e:
    print(f"❌ Error: {e}")