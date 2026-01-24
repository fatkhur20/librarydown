#!/usr/bin/env python3
"""
Cookie validity checker for scheduled monitoring
Checks if cookies are still valid by testing a sample request
"""

import os
import sys
import subprocess
import time
from datetime import datetime, timedelta
import tempfile

sys.path.insert(0, '/root/librarydown')

def check_cookie_validity(cookie_file_path):
    """
    Check if cookie file is still valid by attempting to use it
    """
    if not os.path.exists(cookie_file_path):
        return False, "File does not exist"
    
    try:
        # Read the cookie file
        with open(cookie_file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Simple validation - check if it has valid Netscape format
        lines = content.strip().split('\n')
        valid_cookies = 0
        
        for line in lines:
            line = line.strip()
            if not line or line.startswith('#'):
                continue
                
            fields = line.split('\t')
            if len(fields) == 7:
                domain, flag, path, secure, expires, name, value = fields
                # Check if expiration is in the future
                try:
                    exp_timestamp = int(expires)
                    current_time = int(time.time())
                    
                    if exp_timestamp > current_time:
                        valid_cookies += 1
                    else:
                        # Expired cookie
                        pass
                except ValueError:
                    # Invalid timestamp
                    pass
        
        if valid_cookies > 0:
            return True, f"Valid cookies found: {valid_cookies}"
        else:
            return False, "No valid (non-expired) cookies found"
            
    except Exception as e:
        return False, f"Error reading file: {str(e)}"

def check_all_cookies():
    """
    Check validity of all cookie files in the cookies directory
    """
    cookies_dir = "/opt/librarydown/cookies"
    results = {}
    
    if not os.path.exists(cookies_dir):
        return {"error": "Cookies directory does not exist"}
    
    for filename in os.listdir(cookies_dir):
        if filename.endswith('.txt'):
            filepath = os.path.join(cookies_dir, filename)
            is_valid, message = check_cookie_validity(filepath)
            results[filename] = {
                "valid": is_valid,
                "message": message,
                "last_modified": datetime.fromtimestamp(os.path.getmtime(filepath)).isoformat()
            }
    
    return results

def generate_cookie_report():
    """
    Generate a comprehensive report of cookie status
    """
    results = check_all_cookies()
    
    report = "🔐 LibraryDown Cookie Status Report\n"
    report += "=" * 50 + "\n"
    report += f"Generated: {datetime.now().isoformat()}\n\n"
    
    if "error" in results:
        report += f"❌ Error: {results['error']}\n"
        return report
    
    expired_count = 0
    valid_count = 0
    
    for filename, status in results.items():
        icon = "✅" if status["valid"] else "❌"
        report += f"{icon} {filename}\n"
        report += f"   Status: {status['message']}\n"
        report += f"   Modified: {status['last_modified']}\n"
        
        if status["valid"]:
            valid_count += 1
        else:
            expired_count += 1
        
        report += "\n"
    
    report += f"Summary: {valid_count} valid, {expired_count} expired/invalid\n"
    
    return report

def send_alert_via_telegram(message):
    """
    Send alert message via Telegram bot if configured
    """
    # Load environment
    from dotenv import load_dotenv
    load_dotenv()
    
    token = os.getenv("TELEGRAM_BOT_TOKEN")
    user_id = os.getenv("TELEGRAM_USER_ID")
    
    if token and user_id:
        try:
            import subprocess
            subprocess.run([
                'curl', '-s', '-X', 'POST',
                f'https://api.telegram.org/bot{token}/sendMessage',
                '-d', f'chat_id={user_id}&text={message}'
            ], timeout=10)
        except:
            pass  # Ignore if sending fails

def main():
    if len(sys.argv) > 1 and sys.argv[1] == "--check-all":
        # Generate full report
        report = generate_cookie_report()
        print(report)
        
        # Check if there are expired cookies and send alert
        results = check_all_cookies()
        if "error" not in results:
            expired_cookies = [name for name, status in results.items() if not status["valid"]]
            if expired_cookies:
                alert_msg = f"⚠️ Expired Cookies Alert:\n" + "\n".join([f"- {name}" for name in expired_cookies])
                send_alert_via_telegram(alert_msg)
    else:
        # Check specific file if provided
        if len(sys.argv) > 1:
            filepath = sys.argv[1]
            is_valid, message = check_cookie_validity(filepath)
            print(f"File: {filepath}")
            print(f"Valid: {is_valid}")
            print(f"Message: {message}")
        else:
            print("Usage:")
            print("  python3 check_cookies.py <cookie_file_path>  # Check specific file")
            print("  python3 check_cookies.py --check-all         # Check all cookies and generate report")

if __name__ == "__main__":
    main()