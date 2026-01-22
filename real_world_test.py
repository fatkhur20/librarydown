#!/usr/bin/env python3
"""
Real-world testing script for LibraryDown + Telegram Bot integration
Tests actual functionality with realistic scenarios
"""

import os
import sys
import subprocess
import tempfile
import time
from pathlib import Path

sys.path.insert(0, '/root/librarydown')

from src.bot_cookie_manager import validate_netscape_cookies, deploy_cookie_file
from dotenv import load_dotenv
load_dotenv()

def create_sample_cookies(platform):
    """Create sample cookies for testing"""
    if platform == "youtube":
        return """# Netscape HTTP Cookie File
.youtube.com	TRUE	/	FALSE	2147483647	YSC	abc123def456
.youtube.com	TRUE	/	FALSE	2147483647	SID	google123456
.youtube.com	TRUE	/	FALSE	2147483647	HSID	helper789
.googlevideo.com	TRUE	/	FALSE	2147483647	exp1	experiment123
"""
    elif platform == "instagram":
        return """# Netscape HTTP Cookie File
.instagram.com	TRUE	/	FALSE	2147483647	sessionid	insta_session_123
.instagram.com	TRUE	/	FALSE	2147483647	csrftoken	crsf_456
.instagram.com	TRUE	/	FALSE	2147483647	ds_user_id	user_789
.fbcdn.net	TRUE	/	FALSE	2147483647	dpr	device_pixel_ratio_1
"""
    elif platform == "tiktok":
        return """# Netscape HTTP Cookie File
.tiktok.com	TRUE	/	FALSE	2147483647	s_v_web_id	web_id_abc123
.tiktok.com	TRUE	/	FALSE	2147483647	ttwid	ttwid_def456
.tiktok.com	TRUE	/	FALSE	2147483647	msToken	token_ghi789
.musical.ly	TRUE	/	FALSE	2147483647	device_id	device_jkl012
"""
    else:
        return """# Netscape HTTP Cookie File
.example.com	TRUE	/	FALSE	2147483647	test_cookie	test_value123
.testsite.com	TRUE	/	FALSE	2147483647	another_cookie	another_value456
"""

def test_real_world_scenarios():
    """Test realistic usage scenarios"""
    print("=" * 70)
    print("🧪 REAL-WORLD TESTING SCENARIOS")
    print("=" * 70)
    
    test_results = []
    
    # Scenario 1: Upload YouTube cookies via command
    print("\n📋 Scenario 1: YouTube Cookie Upload (via /upload_yt)")
    print("-" * 50)
    
    youtube_cookies = create_sample_cookies("youtube")
    success, message = deploy_cookie_file(youtube_cookies, "youtube", "user_youtube_cookies.txt")
    
    print(f"Upload Result: {'✅ SUCCESS' if success else '❌ FAILED'}")
    print(f"Message: {message}")
    
    # Check if file exists in expected location
    expected_path = "/opt/librarydown/cookies/youtube_cookies.txt"
    file_exists = os.path.exists(expected_path)
    print(f"File Created: {'✅ YES' if file_exists else '❌ NO'}")
    
    # Verify content
    if file_exists:
        with open(expected_path, 'r', encoding='utf-8') as f:
            content = f.read()
        content_valid = validate_netscape_cookies(content)
        print(f"Content Valid: {'✅ YES' if content_valid else '❌ NO'}")
    else:
        content_valid = False
    
    scenario1_passed = success and file_exists and content_valid
    test_results.append(("YouTube Upload", scenario1_passed))
    print(f"Overall: {'✅ PASSED' if scenario1_passed else '❌ FAILED'}")
    
    # Scenario 2: Upload Instagram cookies via command
    print("\n📋 Scenario 2: Instagram Cookie Upload (via /upload_ig)")
    print("-" * 50)
    
    instagram_cookies = create_sample_cookies("instagram")
    success, message = deploy_cookie_file(instagram_cookies, "instagram", "ig_cookies.txt")
    
    print(f"Upload Result: {'✅ SUCCESS' if success else '❌ FAILED'}")
    print(f"Message: {message}")
    
    # Check if file exists in expected location
    expected_path = "/opt/librarydown/cookies/instagram_cookies.txt"
    file_exists = os.path.exists(expected_path)
    print(f"File Created: {'✅ YES' if file_exists else '❌ NO'}")
    
    # Verify content
    if file_exists:
        with open(expected_path, 'r', encoding='utf-8') as f:
            content = f.read()
        content_valid = validate_netscape_cookies(content)
        print(f"Content Valid: {'✅ YES' if content_valid else '❌ NO'}")
    else:
        content_valid = False
    
    scenario2_passed = success and file_exists and content_valid
    test_results.append(("Instagram Upload", scenario2_passed))
    print(f"Overall: {'✅ PASSED' if scenario2_passed else '❌ FAILED'}")
    
    # Scenario 3: Auto-detection
    print("\n📋 Scenario 3: Auto-detection (no specific command)")
    print("-" * 50)
    
    tiktok_cookies = create_sample_cookies("tiktok")
    success, message = deploy_cookie_file(tiktok_cookies, "auto", "random_cookies.txt")
    
    print(f"Detection Result: {'✅ SUCCESS' if success else '❌ FAILED'}")
    print(f"Message: {message}")
    
    # Check if file exists in expected location
    expected_path = "/opt/librarydown/cookies/tiktok_cookies.txt"
    file_exists = os.path.exists(expected_path)
    print(f"Correct Path: {'✅ YES' if file_exists else '❌ NO'}")
    
    # Verify content
    if file_exists:
        with open(expected_path, 'r', encoding='utf-8') as f:
            content = f.read()
        content_valid = validate_netscape_cookies(content)
        print(f"Content Valid: {'✅ YES' if content_valid else '❌ NO'}")
    else:
        content_valid = False
    
    scenario3_passed = success and file_exists and content_valid
    test_results.append(("Auto-detection", scenario3_passed))
    print(f"Overall: {'✅ PASSED' if scenario3_passed else '❌ FAILED'}")
    
    # Scenario 4: Error handling - invalid format
    print("\n📋 Scenario 4: Error Handling (invalid format)")
    print("-" * 50)
    
    invalid_cookies = "This is not a valid cookie format\nJust random text\nNo tabs or proper structure"
    success, message = deploy_cookie_file(invalid_cookies, "youtube", "invalid_cookies.txt")
    
    print(f"Upload Result: {'❌ EXPECTED FAILURE' if not success else '❌ UNEXPECTED SUCCESS'}")
    print(f"Error Message: {message}")
    
    scenario4_passed = not success  # Should fail for invalid cookies
    test_results.append(("Error Handling", scenario4_passed))
    print(f"Overall: {'✅ PASSED' if scenario4_passed else '❌ FAILED'}")
    
    # Scenario 5: Empty file handling
    print("\n📋 Scenario 5: Empty File Handling")
    print("-" * 50)
    
    empty_cookies = ""
    success, message = deploy_cookie_file(empty_cookies, "general", "empty.txt")
    
    print(f"Upload Result: {'❌ EXPECTED FAILURE' if not success else '❌ UNEXPECTED SUCCESS'}")
    print(f"Error Message: {message}")
    
    scenario5_passed = not success  # Should fail for empty cookies
    test_results.append(("Empty File Handling", scenario5_passed))
    print(f"Overall: {'✅ PASSED' if scenario5_passed else '❌ FAILED'}")
    
    return test_results

def run_api_connectivity_test():
    """Test if API endpoints are reachable"""
    print("\n" + "=" * 70)
    print("🔌 API CONNECTIVITY TEST")
    print("=" * 70)
    
    try:
        # Check if processes are running
        result = subprocess.run(['pgrep', '-f', 'uvicorn.*8001'], 
                              capture_output=True, text=True, timeout=5)
        api_running = result.returncode == 0
        print(f"LibraryDown API (port 8001): {'✅ RUNNING' if api_running else '❌ STOPPED'}")
        
        result = subprocess.run(['pgrep', '-f', 'uvicorn.*8000'], 
                              capture_output=True, text=True, timeout=5)
        apichecker_running = result.returncode == 0
        print(f"API Checker (port 8000): {'✅ RUNNING' if apichecker_running else '❌ STOPPED'}")
        
        return api_running, apichecker_running
        
    except Exception as e:
        print(f"API connectivity test error: {e}")
        return False, False

def check_cookie_files_integrity():
    """Check integrity of deployed cookie files"""
    print("\n" + "=" * 70)
    print("🍪 COOKIE FILES INTEGRITY CHECK")
    print("=" * 70)
    
    cookie_paths = [
        "/opt/librarydown/cookies/youtube_cookies.txt",
        "/opt/librarydown/cookies/instagram_cookies.txt", 
        "/opt/librarydown/cookies/tiktok_cookies.txt",
        "/opt/librarydown/cookies/twitter_cookies.txt",
        "/opt/librarydown/cookies/cookies.txt"
    ]
    
    integrity_results = []
    
    for path in cookie_paths:
        exists = os.path.exists(path)
        print(f"{path}: {'✅ EXISTS' if exists else '❌ MISSING'}", end="")
        
        if exists:
            try:
                with open(path, 'r', encoding='utf-8') as f:
                    content = f.read()
                is_valid = validate_netscape_cookies(content)
                print(f" | Format: {'✅ VALID' if is_valid else '❌ INVALID'}")
                integrity_results.append((path, exists, is_valid))
            except Exception as e:
                print(f" | Error reading: {e}")
                integrity_results.append((path, exists, False))
        else:
            print()
            integrity_results.append((path, exists, False))
    
    return integrity_results

def main():
    print("🚀 LIBRARYDOWN REAL-WORLD TESTING SUITE")
    print("Testing actual functionality with realistic scenarios")
    print("=" * 80)
    
    # Run main scenarios
    scenario_results = test_real_world_scenarios()
    
    # Run API connectivity test
    api_running, checker_running = run_api_connectivity_test()
    
    # Check cookie file integrity
    integrity_results = check_cookie_files_integrity()
    
    # Generate summary
    print("\n" + "=" * 80)
    print("📊 TESTING SUMMARY")
    print("=" * 80)
    
    print("\n🎯 Scenario Tests:")
    passed_scenarios = 0
    for name, passed in scenario_results:
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"  {name:<20} {status}")
        if passed:
            passed_scenarios += 1
    
    print(f"\nAPI Status:")
    print(f"  LibraryDown API:     {'✅ RUNNING' if api_running else '❌ STOPPED'}")
    print(f"  API Checker:         {'✅ RUNNING' if checker_running else '❌ STOPPED'}")
    
    print(f"\n🍪 Cookie Integrity:")
    valid_cookies = sum(1 for _, exists, valid in integrity_results if exists and valid)
    total_cookies = len(integrity_results)
    print(f"  Valid Cookie Files:  {valid_cookies}/{total_cookies}")
    
    print(f"\n📈 Overall Results:")
    total_tests = len(scenario_results)
    print(f"  Scenarios Passed:    {passed_scenarios}/{total_tests}")
    
    if passed_scenarios == total_tests:
        print("\n🎉 ALL REAL-WORLD TESTS PASSED!")
        print("✅ System is ready for production use")
        print("✅ Bot can handle actual cookie uploads")
        print("✅ Files are deployed correctly for API consumption")
        return True
    else:
        print(f"\n⚠️  {total_tests - passed_scenarios} scenario(s) failed")
        print("Please review the test results above")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)