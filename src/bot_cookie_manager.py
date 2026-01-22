from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes, MessageHandler, filters
import os
import logging
import asyncio
import io
import tempfile
import shutil
from pathlib import Path
import subprocess
import re

# Load environment variables from .env file
from dotenv import load_dotenv
load_dotenv()

# Logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
WHITELISTED_USER_ID = os.getenv("TELEGRAM_USER_ID")  # Add this to restrict access

def detect_platform_from_cookies(content: str) -> str:
    """
    Detect platform from cookie content by looking for domain patterns
    """
    content_lower = content.lower()
    
    # Count platform-specific domains
    youtube_count = content_lower.count('.youtube.com') + content_lower.count('googlevideo.com')
    instagram_count = content_lower.count('.instagram.com') + content_lower.count('.fbcdn.net')
    tiktok_count = content_lower.count('.tiktok.com') + content_lower.count('musical.ly')
    twitter_count = content_lower.count('.twitter.com') + content_lower.count('.x.com')
    
    # Determine platform based on highest count
    platform_scores = {
        'youtube': youtube_count,
        'instagram': instagram_count,
        'tiktok': tiktok_count,
        'twitter': twitter_count
    }
    
    # Return platform with highest score, default to 'general'
    detected_platform = max(platform_scores, key=platform_scores.get)
    return detected_platform if platform_scores[detected_platform] > 0 else 'general'

# Paths for different cookie files
COOKIE_PATHS = {
    "youtube": "/opt/librarydown/cookies/youtube_cookies.txt",
    "instagram": "/opt/librarydown/cookies/instagram_cookies.txt", 
    "tiktok": "/opt/librarydown/cookies/tiktok_cookies.txt",
    "twitter": "/opt/librarydown/cookies/twitter_cookies.txt",
    "general": "/opt/librarydown/cookies/cookies.txt"
}

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    if WHITELISTED_USER_ID and user_id != WHITELISTED_USER_ID:
        await update.message.reply_text("❌ Access denied. You are not authorized to use this bot.")
        return
        
    await update.message.reply_text(
        "🔐 *LibraryDown Cookie Manager*\n\n"
        "Commands:\n"
        "/upload_yt - Upload YouTube cookies\n"
        "/upload_ig - Upload Instagram cookies\n"
        "/upload_tiktok - Upload TikTok cookies\n"
        "/upload_general - Upload general cookies\n"
        "/status - Check service status\n\n"
        "📤 *Send me a Netscape-format cookie file* - I'll auto-detect the platform!\n"
        "🔄 *Smart Detection*: I can identify YouTube/Instagram/TikTok cookies automatically!"
    )

def validate_netscape_cookies(content: str) -> tuple[bool, dict]:
    """
    Validate if content is in Netscape cookie format and return detailed info
    Returns: (is_valid, {details about validation})
    """
    lines = content.strip().split('\n')
    valid_lines = 0
    invalid_lines = 0
    domains_found = set()
    platforms_detected = set()
    
    for line in lines:
        line = line.strip()
        # Skip empty lines and comments
        if not line or line.startswith('#'):
            continue
            
        # Check if it has 7 fields (tab-separated Netscape format)
        fields = line.split('\t')
        if len(fields) != 7:
            invalid_lines += 1
            continue
            
        # Basic validation for Netscape format
        domain, flag, path, secure, expires, name, value = fields
        
        # Domain should not be empty
        if not domain.strip():
            invalid_lines += 1
            continue
            
        # Flag should be 0 or 1
        if flag not in ['TRUE', 'FALSE', '0', '1']:
            invalid_lines += 1
            continue
            
        # Path should start with /
        if not path.startswith('/'):
            invalid_lines += 1
            continue
            
        # Secure should be 0 or 1
        if secure not in ['TRUE', 'FALSE', '0', '1']:
            invalid_lines += 1
            continue
            
        # Expires should be numeric timestamp
        try:
            int(expires)
        except ValueError:
            invalid_lines += 1
            continue
            
        # Name and value should not be empty
        if not name.strip() or not value.strip():
            invalid_lines += 1
            continue
            
        # Valid line found
        valid_lines += 1
        domains_found.add(domain.lower())
        
        # Detect platform from domain
        if '.youtube.com' in domain or '.googlevideo.com' in domain:
            platforms_detected.add('youtube')
        elif '.instagram.com' in domain or '.fbcdn.net' in domain:
            platforms_detected.add('instagram')
        elif '.tiktok.com' in domain or '.musical.ly' in domain:
            platforms_detected.add('tiktok')
        elif '.twitter.com' in domain or '.x.com' in domain:
            platforms_detected.add('twitter')
    
    is_valid = valid_lines >= 1
    validation_details = {
        'is_valid': is_valid,
        'valid_cookies': valid_lines,
        'invalid_lines': invalid_lines,
        'total_lines': len(lines),
        'domains_found': list(domains_found),
        'platforms_detected': list(platforms_detected),
        'quality_score': (valid_lines / max(len(lines), 1)) * 100
    }
    
    return is_valid, validation_details


def deploy_cookie_file(content: str, cookie_type: str = "auto", original_filename: str = "cookies.txt") -> tuple[bool, str]:
    """
    Deploy cookie file to the appropriate location and restart services
    If cookie_type is "auto", detect platform from cookie content
    """
    try:
        # Auto-detect platform if not specified
        if cookie_type == "auto":
            detected_platform = detect_platform_from_cookies(content)
            cookie_type = detected_platform
            logging.info(f"Auto-detected platform: {detected_platform}")
        
        # Validate cookie format with detailed info
        is_valid, validation_details = validate_netscape_cookies(content)
        if not is_valid:
            return False, f"Invalid Netscape cookie format. Details: {validation_details['valid_cookies']} valid, {validation_details['invalid_lines']} invalid out of {validation_details['total_lines']} total lines."
        
        # Get destination path based on cookie type
        dest_path = COOKIE_PATHS.get(cookie_type)
        if not dest_path:
            return False, f"Unknown cookie type: {cookie_type}"
        
        # Create directory if it doesn't exist
        dest_dir = os.path.dirname(dest_path)
        os.makedirs(dest_dir, exist_ok=True)
        
        # Create temporary file first
        with tempfile.NamedTemporaryFile(mode='w', delete=False, encoding='utf-8') as tmp_file:
            tmp_file.write(content)
            temp_path = tmp_file.name
        
        # Move to destination with proper permissions
        shutil.move(temp_path, dest_path)
        os.chmod(dest_path, 0o644)  # Readable by all, writable by owner
        
        # Try to restart services (handle both systemd and Termux environments)
        restart_messages = []
        try:
            # Check if systemd is available (not available in Termux)
            result = subprocess.run(['which', 'systemctl'], 
                                 capture_output=True, text=True, timeout=5)
            has_systemctl = result.returncode == 0
            
            if has_systemctl:
                # Systemd environment
                subprocess.run(['sudo', 'systemctl', 'restart', 'librarydown-worker'], 
                             check=True, capture_output=True, timeout=30)
                subprocess.run(['sudo', 'systemctl', 'restart', 'librarydown-api'], 
                             check=True, capture_output=True, timeout=30)
                restart_messages.append("Services restarted via systemd")
            else:
                # Termux environment - notify user to restart manually
                restart_messages.append("Cookie file deployed successfully!")
                restart_messages.append("Please restart librarydown services manually if needed")
                restart_messages.append("(In Termux, you'd need to restart processes individually)")
        except subprocess.CalledProcessError as e:
            restart_messages.append(f"Warning: Service restart failed: {e}")
        except Exception as e:
            restart_messages.append(f"Note: Could not restart services: {e}")
        
        success_msg = "Cookies updated successfully!"
        if restart_messages:
            success_msg += "\n" + "\n".join(restart_messages)
        
        # Add validation details to the success message
        success_msg += f"\n\nValidation: {validation_details['valid_cookies']} valid cookies found"
        if validation_details['platforms_detected']:
            success_msg += f"\nPlatforms: {', '.join(validation_details['platforms_detected'])}"
        success_msg += f"\nDeployed to: {dest_path}\nCommand Type: {cookie_type}\nOriginal File: {original_filename}"
        
        return True, success_msg
        
    except Exception as e:
        logging.error(f"Error deploying cookie file: {e}")
        return False, f"Failed to deploy cookies: {str(e)}"

def deploy_cookie_file(content: str, cookie_type: str = "auto", original_filename: str = "cookies.txt") -> tuple[bool, str]:
    """
    Deploy cookie file to the appropriate location and restart services
    If cookie_type is "auto", detect platform from cookie content
    """
    try:
        # Auto-detect platform if not specified
        if cookie_type == "auto":
            detected_platform = detect_platform_from_cookies(content)
            cookie_type = detected_platform
            logging.info(f"Auto-detected platform: {detected_platform}")
        
        # Get destination path based on cookie type
        dest_path = COOKIE_PATHS.get(cookie_type)
        if not dest_path:
            return False, f"Unknown cookie type: {cookie_type}"
        
        # Validate cookie format
        if not validate_netscape_cookies(content):
            return False, "Invalid Netscape cookie format. Please ensure the file contains properly formatted cookies."
        
        # Create directory if it doesn't exist
        dest_dir = os.path.dirname(dest_path)
        os.makedirs(dest_dir, exist_ok=True)
        
        # Create temporary file first
        with tempfile.NamedTemporaryFile(mode='w', delete=False, encoding='utf-8') as tmp_file:
            tmp_file.write(content)
            temp_path = tmp_file.name
        
        # Move to destination with proper permissions
        shutil.move(temp_path, dest_path)
        os.chmod(dest_path, 0o644)  # Readable by all, writable by owner
        
        # Try to restart services (handle both systemd and Termux environments)
        restart_messages = []
        try:
            # Check if systemd is available (not available in Termux)
            result = subprocess.run(['which', 'systemctl'], 
                                 capture_output=True, text=True, timeout=5)
            has_systemctl = result.returncode == 0
            
            if has_systemctl:
                # Systemd environment
                subprocess.run(['sudo', 'systemctl', 'restart', 'librarydown-worker'], 
                             check=True, capture_output=True, timeout=30)
                subprocess.run(['sudo', 'systemctl', 'restart', 'librarydown-api'], 
                             check=True, capture_output=True, timeout=30)
                restart_messages.append("Services restarted via systemd")
            else:
                # Termux environment - notify user to restart manually
                restart_messages.append("Cookie file deployed successfully!")
                restart_messages.append("Please restart librarydown services manually if needed")
                restart_messages.append("(In Termux, you'd need to restart processes individually)")
        except subprocess.CalledProcessError as e:
            restart_messages.append(f"Warning: Service restart failed: {e}")
        except Exception as e:
            restart_messages.append(f"Note: Could not restart services: {e}")
        
        success_msg = "Cookies updated successfully!"
        if restart_messages:
            success_msg += "\n" + "\n".join(restart_messages)
        
        success_msg += f"\n\nDeployed to: {dest_path}\nCommand Type: {cookie_type}\nOriginal File: {original_filename}"
        
        return True, success_msg
        
    except Exception as e:
        logging.error(f"Error deploying cookie file: {e}")
        return False, f"Failed to deploy cookies: {str(e)}"

async def upload_youtube(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    if WHITELISTED_USER_ID and user_id != WHITELISTED_USER_ID:
        await update.message.reply_text("❌ Access denied. You are not authorized to use this bot.")
        return
        
    await update.message.reply_text(
        "📤 Please send me the YouTube cookies file (.txt format with Netscape cookie format).\n\n"
        "You can export this from your browser's developer tools under Application/Cookies."
    )

async def upload_instagram(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    if WHITELISTED_USER_ID and user_id != WHITELISTED_USER_ID:
        await update.message.reply_text("❌ Access denied. You are not authorized to use this bot.")
        return
        
    await update.message.reply_text(
        "📸 Please send me the Instagram cookies file (.txt format with Netscape cookie format).\n\n"
        "You can export this from your browser's developer tools under Application/Cookies."
    )

async def upload_tiktok(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    if WHITELISTED_USER_ID and user_id != WHITELISTED_USER_ID:
        await update.message.reply_text("❌ Access denied. You are not authorized to use this bot.")
        return
        
    await update.message.reply_text(
        "🎵 Please send me the TikTok cookies file (.txt format with Netscape cookie format).\n\n"
        "You can export this from your browser's developer tools under Application/Cookies."
    )

async def upload_general(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    if WHITELISTED_USER_ID and user_id != WHITELISTED_USER_ID:
        await update.message.reply_text("❌ Access denied. You are not authorized to use this bot.")
        return
        
    await update.message.reply_text(
        "📋 Please send me the general cookies file (.txt format with Netscape cookie format).\n\n"
        "This will be used as the default cookie file for the downloader."
    )

async def handle_cookie_upload(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Handle cookie file uploads based on command context or document upload
    """
    user_id = str(update.effective_user.id)
    if WHITELISTED_USER_ID and user_id != WHITELISTED_USER_ID:
        await update.message.reply_text("❌ Access denied. You are not authorized to use this bot.")
        return
    
    # Determine cookie type from command or default to auto-detection
    cookie_type = "auto"  # Default to auto-detection
    if context.args and len(context.args) > 0:
        cmd_type = context.args[0].lower()
        if cmd_type in COOKIE_PATHS:
            cookie_type = cmd_type
    elif hasattr(update.message, 'reply_to_message') and update.message.reply_to_message:
        # Check if this is a reply to a command
        replied_text = update.message.reply_to_message.text or ""
        if '/upload_yt' in replied_text:
            cookie_type = "youtube"
        elif '/upload_ig' in replied_text:
            cookie_type = "instagram"
        elif '/upload_tiktok' in replied_text:
            cookie_type = "tiktok"
        elif '/upload_general' in replied_text:
            cookie_type = "general"
    
    # Handle document upload
    if update.message.document:
        try:
            await update.message.reply_chat_action(action="upload_document")
            
            # Get file info
            file = await update.message.document.get_file()
            file_name = update.message.document.file_name or "cookies.txt"
            
            # Download file content
            byte_array = await file.download_as_bytearray()
            content = byte_array.decode('utf-8')
            
            # Deploy cookies with original filename
            success, message = await asyncio.get_event_loop().run_in_executor(
                None, deploy_cookie_file, content, cookie_type, file_name
            )
            
            if success:
                await update.message.reply_text(f"✅ {message}")
            else:
                await update.message.reply_text(f"❌ {message}")
                
        except Exception as e:
            await update.message.reply_text(f"❌ Error processing file: {str(e)}")
    
    # Handle text message (in case someone pastes cookie content)
    elif update.message.text and not update.message.text.startswith('/'):
        try:
            await update.message.reply_chat_action(action="typing")
            
            content = update.message.text
            
            # Deploy cookies with generic filename for text input
            success, message = await asyncio.get_event_loop().run_in_executor(
                None, deploy_cookie_file, content, cookie_type, "pasted_cookies.txt"
            )
            
            if success:
                await update.message.reply_text(f"✅ {message}")
            else:
                await update.message.reply_text(f"❌ {message}")
                
        except Exception as e:
            await update.message.reply_text(f"❌ Error processing text: {str(e)}")

async def status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    if WHITELISTED_USER_ID and user_id != WHITELISTED_USER_ID:
        await update.message.reply_text("❌ Access denied. You are not authorized to use this bot.")
        return
    
    try:
        # Check if systemctl is available (Termux doesn't have it)
        import shutil
        has_systemctl = shutil.which('systemctl') is not None
        
        api_state = "unknown"
        worker_state = "unknown"
        
        if has_systemctl:
            # Systemd environment
            api_status = subprocess.run(['sudo', 'systemctl', 'is-active', 'librarydown-api'], 
                                      capture_output=True, text=True, timeout=10)
            worker_status = subprocess.run(['sudo', 'systemctl', 'is-active', 'librarydown-worker'], 
                                         capture_output=True, text=True, timeout=10)
            
            api_state = api_status.stdout.strip() if api_status.returncode == 0 else "unknown"
            worker_state = worker_status.stdout.strip() if worker_status.returncode == 0 else "unknown"
        else:
            # Termux environment - check for running processes
            try:
                # Check for API process
                api_ps = subprocess.run(['pgrep', '-f', 'uvicorn.*8001'], 
                                      capture_output=True, text=True, timeout=5)
                api_state = "running" if api_ps.returncode == 0 else "stopped"
                
                # Check for worker process
                worker_ps = subprocess.run(['pgrep', '-f', 'celery.*worker'], 
                                         capture_output=True, text=True, timeout=5)
                worker_state = "running" if worker_ps.returncode == 0 else "stopped"
            except:
                api_state = "unknown (Termux)"
                worker_state = "unknown (Termux)"
        
        # Check cookie files
        cookie_status = "📋 Cookie Files:\n"
        for name, path in COOKIE_PATHS.items():
            exists = "✅" if os.path.exists(path) else "❌"
            cookie_status += f"  {exists} {name}: {path}\n"
        
        status_msg = (
            f"📊 *LibraryDown Service Status*\n\n"
            f"API Service: *{api_state.upper()}*\n"
            f"Worker Service: *{worker_state.upper()}*\n\n"
            f"{cookie_status}\n"
            f"Environment: *{'Termux' if not has_systemctl else 'Systemd'}*\n"
            f"Last updated: {os.getenv('LAST_UPDATE', 'Never')}"
        )
        
        await update.message.reply_text(status_msg, parse_mode="Markdown")
        
    except Exception as e:
        await update.message.reply_text(f"❌ Error checking status: {str(e)}")

def main():
    if not TOKEN:
        print("TELEGRAM_BOT_TOKEN not set")
        return

    app = ApplicationBuilder().token(TOKEN).build()
    
    # Add handlers for cookie upload commands
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("upload_yt", upload_youtube))
    app.add_handler(CommandHandler("upload_ig", upload_instagram))
    app.add_handler(CommandHandler("upload_tiktok", upload_tiktok))
    app.add_handler(CommandHandler("upload_general", upload_general))
    app.add_handler(CommandHandler("status", status))
    
    # Handle document uploads and text messages
    app.add_handler(MessageHandler(filters.Document.ALL, handle_cookie_upload))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_cookie_upload))
    
    print("Cookie manager bot started...")
    app.run_polling()

if __name__ == '__main__':
    main()