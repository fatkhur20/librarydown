#!/usr/bin/env python3
"""
Test the platform detection functionality
"""

import sys
import os
sys.path.insert(0, '/root/librarydown')

from src.bot_cookie_manager import detect_platform_from_cookies

def test_platform_detection():
    print("🔍 Testing Platform Detection Functionality\n")
    
    # Test YouTube cookies
    youtube_cookies = """# Netscape HTTP Cookie File
.youtube.com	TRUE	/	FALSE	2147483647	YSC	abc123
.youtube.com	TRUE	/	FALSE	2147483647	SID	xyz789
.googlevideo.com	TRUE	/	FALSE	2147483647	exp1	a1b2c3
"""
    
    result = detect_platform_from_cookies(youtube_cookies)
    print(f"YouTube cookies detection: {result} {'✅' if result == 'youtube' else '❌'}")
    
    # Test Instagram cookies
    instagram_cookies = """# Netscape HTTP Cookie File
.instagram.com	TRUE	/	FALSE	2147483647	sessionid	123456
.instagram.com	TRUE	/	FALSE	2147483647	csrftoken	abc123
.fbcdn.net	TRUE	/	FALSE	2147483647	dpr	1.0
"""
    
    result = detect_platform_from_cookies(instagram_cookies)
    print(f"Instagram cookies detection: {result} {'✅' if result == 'instagram' else '❌'}")
    
    # Test TikTok cookies
    tiktok_cookies = """# Netscape HTTP Cookie File
.tiktok.com	TRUE	/	FALSE	2147483647	s_v_web_id	abc123
.tiktok.com	TRUE	/	FALSE	2147483647	ttwid	xyz789
.musical.ly	TRUE	/	FALSE	2147483647	device_id	def456
"""
    
    result = detect_platform_from_cookies(tiktok_cookies)
    print(f"TikTok cookies detection: {result} {'✅' if result == 'tiktok' else '❌'}")
    
    # Test Twitter cookies
    twitter_cookies = """# Netscape HTTP Cookie File
.twitter.com	TRUE	/	FALSE	2147483647	auth_token	abc123
.x.com	TRUE	/	FALSE	2147483647	ct0	def456
"""
    
    result = detect_platform_from_cookies(twitter_cookies)
    print(f"Twitter cookies detection: {result} {'✅' if result == 'twitter' else '❌'}")
    
    # Test mixed cookies (should detect most frequent)
    mixed_cookies = """# Netscape HTTP Cookie File
.youtube.com	TRUE	/	FALSE	2147483647	YSC	abc123
.youtube.com	TRUE	/	FALSE	2147483647	SID	xyz789
.instagram.com	TRUE	/	FALSE	2147483647	sessionid	123456
.tiktok.com	TRUE	/	FALSE	2147483647	s_v_web_id	abc123
"""
    
    result = detect_platform_from_cookies(mixed_cookies)
    print(f"Mixed cookies detection: {result} (any platform is acceptable)")
    
    # Test unknown/empty cookies
    empty_cookies = """# Just comments
# No actual cookies here
"""
    
    result = detect_platform_from_cookies(empty_cookies)
    print(f"Empty cookies detection: {result} {'✅' if result == 'general' else '❌'}")
    
    print("\n🎉 Platform detection test completed!")

if __name__ == "__main__":
    test_platform_detection()