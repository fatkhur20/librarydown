#!/usr/bin/env python3
"""
Comprehensive test suite for LibraryDown + Telegram Bot integration
"""

import os
import sys
import subprocess
import time
import tempfile
from pathlib import Path

sys.path.insert(0, '/root/librarydown')

from src.bot_cookie_manager import validate_netscape_cookies, deploy_cookie_file
from dotenv import load_dotenv
load_dotenv()

def test_environment():
    """Test environment variables and configuration"""
    print("=" * 60)
    print("TEST 1: Environment Variables")
    print("=" * 60)
    
    token = os.getenv("TELEGRAM_BOT_TOKEN")
    user_id = os.getenv("TELEGRAM_USER_ID")
    
    print(f"Telegram Bot Token: {'✅ VALID' if token and len(token) > 10 else '❌ INVALID'}")
    print(f"Telegram User ID: {'✅ VALID' if user_id and len(str(user_id)) > 5 else '❌ INVALID'}")
    
    # Test if virtual environment is working
    try:
        result = subprocess.run([sys.executable, '-c', 'import telegram; print("OK")'], 
                              capture_output=True, text=True, cwd='/root/librarydown')
        print(f"Python Telegram Module: {'✅ AVAILABLE' if result.returncode == 0 else '❌ MISSING'}")
    except Exception as e:
        print(f"Python Telegram Module: ❌ ERROR - {e}")
    
    return token and user_id and len(token) > 10 and len(str(user_id)) > 5

def test_cookie_validation():
    """Test cookie validation functionality"""
    print("\n" + "=" * 60)
    print("TEST 2: Cookie Validation")
    print("=" * 60)
    
    # Valid Netscape cookie format
    valid_cookies = """# Netscape HTTP Cookie File
# This is a generated file!  Do not edit.
.example.com	TRUE	/	FALSE	2147483647	valid_cookie	test_value
.google.com	TRUE	/	TRUE	2147483647	GAPS	test123
.youtube.com	TRUE	/	FALSE	2147483647	SID	test456
"""
    
    # Invalid cookie format
    invalid_cookies = """# Invalid format
invalid
cookie
content
without proper fields
"""
    
    # Test valid cookies
    valid_result = validate_netscape_cookies(valid_cookies)
    print(f"Valid cookie test: {'✅ PASS' if valid_result else '❌ FAIL'}")
    
    # Test invalid cookies
    invalid_result = validate_netscape_cookies(invalid_cookies)
    print(f"Invalid cookie test: {'✅ PASS' if not invalid_result else '❌ FAIL'}")
    
    # Test empty content
    empty_result = validate_netscape_cookies("")
    print(f"Empty content test: {'✅ PASS' if not empty_result else '❌ FAIL'}")
    
    # Test minimal valid cookie
    minimal = ".test.com	TRUE	/	FALSE	2147483647	name	value\n"
    minimal_result = validate_netscape_cookies(minimal)
    print(f"Minimal valid cookie test: {'✅ PASS' if minimal_result else '❌ FAIL'}")
    
    return valid_result and not invalid_result and not empty_result and minimal_result

def test_cookie_deployment():
    """Test cookie deployment functionality"""
    print("\n" + "=" * 60)
    print("TEST 3: Cookie Deployment")
    print("=" * 60)
    
    # Test cookie content
    test_cookies = """.example.com	TRUE	/	FALSE	2147483647	test_cookie	value123
.test2.com	TRUE	/path	TRUE	2147483647	another_cookie	value456
"""
    
    # Test deployment to temporary location
    with tempfile.TemporaryDirectory() as temp_dir:
        # Temporarily override cookie paths for testing
        import src.bot_cookie_manager as bcm
        
        original_paths = bcm.COOKIE_PATHS.copy()
        
        # Create test paths in temp directory
        test_paths = {}
        for key, orig_path in original_paths.items():
            test_paths[key] = os.path.join(temp_dir, f"{key}_cookies.txt")
        
        bcm.COOKIE_PATHS.update(test_paths)
        
        try:
            # Test deployment
            success, message = deploy_cookie_file(test_cookies, "general")
            print(f"Cookie deployment test: {'✅ PASS' if success else '❌ FAIL'}")
            print(f"  Message: {message}")
            
            # Check if file was created
            deployed_file = os.path.join(temp_dir, "general_cookies.txt")
            file_exists = os.path.exists(deployed_file)
            print(f"File creation test: {'✅ PASS' if file_exists else '❌ FAIL'}")
            
            if file_exists:
                # Check file content
                with open(deployed_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                content_correct = test_cookies.strip() == content.strip()
                print(f"File content test: {'✅ PASS' if content_correct else '❌ FAIL'}")
            
            # Restore original paths
            bcm.COOKIE_PATHS.update(original_paths)
            
            return success and file_exists
            
        except Exception as e:
            print(f"Cookie deployment test: ❌ ERROR - {e}")
            bcm.COOKIE_PATHS.update(original_paths)
            return False

def test_directory_structure():
    """Test required directory structure"""
    print("\n" + "=" * 60)
    print("TEST 4: Directory Structure")
    print("=" * 60)
    
    required_dirs = [
        "/root/librarydown",
        "/root/librarydown/src",
        "/root/librarydown/venv",
        "/root/librarydown/logs",
        "/opt/librarydown/cookies"
    ]
    
    all_exist = True
    for dir_path in required_dirs:
        exists = os.path.exists(dir_path)
        print(f"{dir_path}: {'✅ EXISTS' if exists else '❌ MISSING'}")
        if not exists:
            all_exist = False
    
    return all_exist

def test_bot_module():
    """Test bot module imports and functions"""
    print("\n" + "=" * 60)
    print("TEST 5: Bot Module Functionality")
    print("=" * 60)
    
    try:
        from src.bot_cookie_manager import start, handle_cookie_upload, status
        print("Bot handlers import: ✅ SUCCESS")
        
        # Test that required functions exist
        functions_exist = all([
            callable(start),
            callable(handle_cookie_upload),
            callable(status)
        ])
        print(f"Required functions exist: {'✅ YES' if functions_exist else '❌ NO'}")
        
        return functions_exist
        
    except ImportError as e:
        print(f"Bot module import: ❌ FAILED - {e}")
        return False
    except Exception as e:
        print(f"Bot module test: ❌ ERROR - {e}")
        return False

def run_comprehensive_test():
    """Run all tests and report results"""
    print("🧪 RUNNING COMPREHENSIVE TEST SUITE")
    print("LibraryDown + Telegram Bot Integration")
    print("=" * 80)
    
    tests = [
        ("Environment Setup", test_environment),
        ("Cookie Validation", test_cookie_validation),
        ("Cookie Deployment", test_cookie_deployment),
        ("Directory Structure", test_directory_structure),
        ("Bot Module", test_bot_module),
    ]
    
    results = []
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"  ❌ UNEXPECTED ERROR: {e}")
            results.append((test_name, False))
    
    print("\n" + "=" * 80)
    print("📊 FINAL RESULTS")
    print("=" * 80)
    
    passed = 0
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{test_name:<30} {status}")
        if result:
            passed += 1
    
    print("-" * 80)
    print(f"TOTAL: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 ALL TESTS PASSED! System is ready for use.")
        return True
    else:
        print("⚠️  Some tests failed. Please check the configuration.")
        return False

if __name__ == "__main__":
    success = run_comprehensive_test()
    sys.exit(0 if success else 1)