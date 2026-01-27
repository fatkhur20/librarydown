"""Telegram bot for LibraryDown - Enhanced with menu, history, and notifications"""

import os
import asyncio
import tempfile
from typing import Dict, Any, Optional
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import (
    ApplicationBuilder, 
    CommandHandler, 
    MessageHandler, 
    filters,
    ContextTypes,
    CallbackQueryHandler,
    ConversationHandler
)
from loguru import logger
from urllib.parse import urlparse
import aiohttp
import time
import json
from datetime import datetime, timedelta
import glob

# Import our utilities
from src.utils.url_validator import URLValidator
from src.utils.security import security_validator
from src.core.platform_registry import PlatformRegistry
from src.core.config import settings
from src.utils.user_features import user_preferences


class LibraryDownBot:
    def __init__(self):
        # Check if token is properly configured
        self.token = os.getenv("TELEGRAM_BOT_TOKEN")
        if not self.token or self.token == "your_bot_token_here" or len(self.token) < 10:
            raise ValueError("TELEGRAM_BOT_TOKEN environment variable not properly set. Please configure via environment variables.")
        
        self.user_id = os.getenv("TELEGRAM_USER_ID")
        self.media_folder = settings.MEDIA_FOLDER
        self.history_file = os.path.join(self.media_folder, "bot_history.json")
        
        # Initialize bot
        self.application = ApplicationBuilder().token(self.token).build()
        self.download_history = self.load_history()
        self.setup_handlers()
    
    def load_history(self):
        """Load download history from file."""
        try:
            if os.path.exists(self.history_file):
                with open(self.history_file, 'r') as f:
                    return json.load(f)
            else:
                return []
        except Exception as e:
            logger.error(f"Error loading history: {e}")
            return []
    
    def save_history(self):
        """Save download history to file."""
        try:
            # Keep only last 100 entries
            self.download_history = self.download_history[-100:]
            
            with open(self.history_file, 'w') as f:
                json.dump(self.download_history, f, indent=2)
        except Exception as e:
            logger.error(f"Error saving history: {e}")
    
    def add_to_history(self, user_id: int, username: str, url: str, platform: str, title: str, status: str):
        """Add download to history."""
        history_item = {
            "user_id": user_id,
            "username": username,
            "url": url,
            "platform": platform,
            "title": title,
            "status": status,
            "timestamp": datetime.now().isoformat()
        }
        self.download_history.append(history_item)
        self.save_history()
    
    def setup_handlers(self):
        """Setup bot command handlers."""
        # Command handlers
        self.application.add_handler(CommandHandler("start", self.start))
        self.application.add_handler(CommandHandler("help", self.help))
        self.application.add_handler(CommandHandler("download", self.download_command))
        self.application.add_handler(CommandHandler("status", self.status))
        self.application.add_handler(CommandHandler("history", self.history))
        self.application.add_handler(CommandHandler("menu", self.menu))
        self.application.add_handler(CommandHandler("settings", self.settings))
        
        # Message handler for URLs
        self.application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_url_message))
        
        # Callback query handler for inline keyboards
        self.application.add_handler(CallbackQueryHandler(self.handle_callback_query))
    
    def get_main_menu_keyboard(self):
        """Get the main menu keyboard."""
        keyboard = [
            [
                KeyboardButton("📥 Download"),
                KeyboardButton("📜 History")
            ],
            [
                KeyboardButton("⚙️ Settings"),
                KeyboardButton("ℹ️ Help")
            ],
            [
                KeyboardButton("📊 Status")
            ]
        ]
        return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    
    def get_quality_keyboard(self) -> InlineKeyboardMarkup:
        """Get inline keyboard for quality selection."""
        keyboard = [
            [
                InlineKeyboardButton("720p", callback_data="quality_720p"),
                InlineKeyboardButton("480p", callback_data="quality_480p"),
            ],
            [
                InlineKeyboardButton("360p", callback_data="quality_360p"),
                InlineKeyboardButton("Audio Only", callback_data="quality_audio"),
            ],
            [
                InlineKeyboardButton("1080p", callback_data="quality_1080p"),
                InlineKeyboardButton("Auto", callback_data="quality_auto"),
            ]
        ]
        return InlineKeyboardMarkup(keyboard)
    
    def get_settings_keyboard(self) -> InlineKeyboardMarkup:
        """Get inline keyboard for settings."""
        keyboard = [
            [
                InlineKeyboardButton("🎬 Quality: 720p", callback_data="setting_quality"),
            ],
            [
                InlineKeyboardButton("💾 Format: mp4", callback_data="setting_format"),
            ],
            [
                InlineKeyboardButton("🔄 Notifications: On", callback_data="setting_notifications"),
            ],
            [
                InlineKeyboardButton("Back to Menu", callback_data="back_to_menu"),
            ]
        ]
        return InlineKeyboardMarkup(keyboard)
    
    async def start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /start command."""
        user = update.effective_user
        welcome_text = f"""
🤖 **LibraryDown Bot - Download Videos from Social Media**

Welcome {user.first_name}! 

Send me a video URL from any supported platform:
• YouTube, TikTok, Instagram, SoundCloud
• Dailymotion, Twitch, Reddit, Vimeo
• Facebook, Bilibili, LinkedIn, Pinterest

**Commands:**
/start - Show this message
/download - Download a video (followed by URL)
/history - View download history
/settings - Change bot settings
/menu - Show interactive menu
/status - Check bot status
/help - Show help information

Just paste a URL and I'll download it for you! 🎥
        """
        await update.message.reply_text(welcome_text, parse_mode="Markdown", reply_markup=self.get_main_menu_keyboard())
    
    async def menu(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Show interactive menu."""
        menu_text = """
🎮 **LibraryDown Bot Menu**

Choose an option:
• 📥 Download - Download a video
• 📜 History - View download history  
• ⚙️ Settings - Change bot settings
• ℹ️ Help - Show help information
• 📊 Status - Check bot status

Send a URL directly to start downloading!
        """
        await update.message.reply_text(menu_text, parse_mode="Markdown", reply_markup=self.get_main_menu_keyboard())
    
    async def settings(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Show settings menu."""
        settings_text = """
⚙️ **LibraryDown Bot Settings**

Current Settings:
• Quality: 720p (default)
• Format: MP4 (default) 
• Notifications: Enabled (default)

Tap on any setting to change it:
        """
        await update.message.reply_text(settings_text, parse_mode="Markdown", reply_markup=self.get_settings_keyboard())
    
    async def help(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /help command."""
        help_text = """
📚 **LibraryDown Bot Help**

**Supported Platforms:**
• YouTube (youtube.com, youtu.be)
• TikTok (tiktok.com)
• Instagram (instagram.com)
• SoundCloud (soundcloud.com)
• Dailymotion (dailymotion.com)
• Twitch (twitch.tv)
• Reddit (reddit.com)
• Vimeo (vimeo.com)
• Facebook (facebook.com)
• Bilibili (bilibili.com)
• LinkedIn (linkedin.com)
• Pinterest (pinterest.com)

**How to use:**
1. Send a video URL directly
2. Or use /download URL
3. Choose quality if prompted
4. Wait for download to complete
5. Receive the video file

**Quality Options:**
• Auto (default): Best available
• 720p: HD quality
• 480p: Medium quality  
• 360p: Low quality
• Audio only: Extract audio

Enjoy downloading! 🚀
        """
        await update.message.reply_text(help_text, parse_mode="Markdown")
    
    async def status(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /status command."""
        # Get some stats
        total_downloads = len(self.download_history)
        recent_downloads = len([item for item in self.download_history 
                               if datetime.fromisoformat(item['timestamp']) > datetime.now() - timedelta(days=1)])
        
        status_text = f"""
📊 **LibraryDown Bot Status**

• Bot: Active ✅
• Supported Platforms: 12
• Media Folder: {self.media_folder}
• Total Downloads: {total_downloads}
• Downloads Today: {recent_downloads}
• Version: 2.1.0
• Uptime: {time.strftime('%Y-%m-%d %H:%M:%S')}
        """
        await update.message.reply_text(status_text, parse_mode="Markdown")
    
    async def history(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /history command."""
        user_id = update.effective_user.id
        user_history = [item for item in self.download_history if item['user_id'] == user_id]
        
        if not user_history:
            await update.message.reply_text("📜 Your download history is empty.")
            return
        
        # Show last 10 downloads
        history_items = user_history[-10:]
        history_text = "📜 *Your Recent Downloads:*\n\n"
        
        for item in reversed(history_items):
            timestamp = datetime.fromisoformat(item['timestamp']).strftime('%m/%d %H:%M')
            history_text += f"• [{item['platform'].title()}]({item['url']}) - `{item['title'][:30]}...` ({item['status']}) - {timestamp}\n"
        
        await update.message.reply_text(history_text, parse_mode="Markdown")
    
    async def download_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /download command with URL."""
        if not context.args:
            await update.message.reply_text("❌ Please provide a URL after /download command.\n\nExample: `/download https://youtube.com/watch?v=xxx`", parse_mode="Markdown")
            return
        
        url = context.args[0]
        quality = "720p"  # Default quality
        if len(context.args) > 1:
            quality = context.args[1]
        
        await self.process_download(update, url, quality)
    
    async def handle_url_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle URL messages directly."""
        message_text = update.message.text.strip()
        
        # Check if message is a command from our keyboard
        if message_text in ["📥 Download", "📜 History", "⚙️ Settings", "ℹ️ Help", "📊 Status"]:
            if message_text == "📥 Download":
                await update.message.reply_text("🔗 Please send a video URL to download.")
            elif message_text == "📜 History":
                await self.history(update, context)
            elif message_text == "⚙️ Settings":
                await self.settings(update, context)
            elif message_text == "ℹ️ Help":
                await self.help(update, context)
            elif message_text == "📊 Status":
                await self.status(update, context)
            return
        
        # Check if message contains a URL
        if self.is_valid_url(message_text):
            await self.process_download(update, message_text, "720p")
        else:
            await update.message.reply_text("🔗 Please send a valid video URL to download or use the menu buttons.")
    
    def is_valid_url(self, text: str) -> bool:
        """Check if text contains a valid URL."""
        try:
            parsed = urlparse(text)
            return bool(parsed.netloc and parsed.scheme in ['http', 'https'])
        except Exception:
            return False
    
    async def process_download(self, update: Update, url: str, quality: str = "720p"):
        """Process download request."""
        user = update.effective_user
        chat_id = update.effective_chat.id
        
        logger.info(f"[BOT] Download request from {user.username} (ID: {user.id}): {url}")
        
        # Validate URL security
        is_valid, error = security_validator.validate_url(url)
        if not is_valid:
            await update.message.reply_text(f"❌ Security validation failed: {error}")
            return
        
        # Detect platform
        platform = PlatformRegistry.detect_platform(url)
        if platform == "unknown":
            await update.message.reply_text("❌ Unsupported platform. Supported platforms:\nYouTube, TikTok, Instagram, SoundCloud, Dailymotion, Twitch, Reddit, Vimeo, Facebook, Bilibili, LinkedIn, Pinterest")
            return
        
        # Notify user that download is starting
        await update.message.reply_text(f"🔄 Starting download from {platform.title()}...\nURL: {url}")
        
        try:
            # Get appropriate downloader
            try:
                downloader = PlatformRegistry.get_downloader_by_platform(platform)
            except ValueError:
                await update.message.reply_text(f"❌ Download not implemented for {platform}")
                return
            
            # Notify download in progress
            await update.message.reply_text("⏳ Downloading... This may take a moment.")
            
            # Perform download
            result = await downloader.download(url, quality=quality)
            
            # Extract file information
            video_files = result.get('media', {}).get('video', [])
            
            if video_files:
                # Send the first available file
                first_file = video_files[0]
                file_url = first_file.get('url', '')
                
                # Extract filename from URL
                filename = file_url.split('/')[-1] if file_url else f"download_{platform}.mp4"
                
                # Construct local file path
                local_file_path = os.path.join(self.media_folder, filename)
                
                # Check if file exists locally
                if os.path.exists(local_file_path):
                    # Send file to user
                    with open(local_file_path, 'rb') as video_file:
                        await update.message.reply_video(
                            video=video_file,
                            caption=f"✅ Download completed!\nPlatform: {platform.title()}\nTitle: {result.get('title', 'Video')[:50]}..."
                        )
                    
                    logger.info(f"[BOT] Download sent to {user.username}: {local_file_path}")
                    
                    # Add to history
                    self.add_to_history(user.id, user.username or str(user.id), url, platform, 
                                      result.get('title', 'Unknown'), 'SUCCESS')
                    
                    # Send notification
                    await update.message.reply_text("🎉 Your download is complete! Enjoy your video.")
                else:
                    # If file doesn't exist locally, provide alternative
                    await update.message.reply_text(
                        f"✅ Download completed but file not available for direct sending.\n\nTitle: {result.get('title', 'Video')}\nPlatform: {platform.title()}\nDuration: {result.get('duration', 'Unknown')}"
                    )
                    
                    # Add to history
                    self.add_to_history(user.id, user.username or str(user.id), url, platform, 
                                      result.get('title', 'Unknown'), 'PARTIAL')
            else:
                # If no video files, send metadata
                await update.message.reply_text(
                    f"✅ Download completed but no video file available.\n\nTitle: {result.get('title', 'Video')}\nPlatform: {platform.title()}\nDuration: {result.get('duration', 'Unknown')}"
                )
                
                # Add to history
                self.add_to_history(user.id, user.username or str(user.id), url, platform, 
                                  result.get('title', 'Unknown'), 'METADATA_ONLY')
        
        except Exception as e:
            logger.error(f"[BOT] Download failed for {url}: {e}")
            await update.message.reply_text(f"❌ Download failed: {str(e)}")
            
            # Add to history as failed
            self.add_to_history(user.id, user.username or str(user.id), url, platform, 
                              'Download Failed', 'FAILED')
    
    async def handle_callback_query(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle inline keyboard callbacks."""
        query = update.callback_query
        await query.answer()
        
        # Process callback based on data
        if query.data.startswith("quality_"):
            quality = query.data.replace("quality_", "")
            await query.edit_message_text(f"Selected quality: {quality}. Send a URL to download with this quality.")
        elif query.data.startswith("setting_"):
            setting = query.data.replace("setting_", "")
            if setting == "quality":
                await query.edit_message_text("Select download quality:", reply_markup=self.get_quality_keyboard())
            elif setting == "notifications":
                await query.edit_message_text("Notifications setting toggled.")
            elif setting == "format":
                await query.edit_message_text("Select output format: MP4, MP3, etc.")
        elif query.data == "back_to_menu":
            await query.edit_message_text("Choose an option:", reply_markup=self.get_main_menu_keyboard())
    
    async def run(self):
        """Start the bot."""
        logger.info("🚀 Starting LibraryDown Telegram Bot...")
        await self.application.initialize()
        await self.application.start()
        await self.application.updater.start_polling()
        
        logger.info("Telegram Bot is running! Press Ctrl+C to stop.")
        
        # Keep the bot running
        try:
            while True:
                await asyncio.sleep(1)
        except KeyboardInterrupt:
            logger.info("🛑 Stopping LibraryDown Telegram Bot...")
            await self.application.stop()
            await self.application.shutdown()


def main():
    """Main function to run the bot."""
    # Check if required environment variables are set
    bot_token = os.getenv("TELEGRAM_BOT_TOKEN")
    if not bot_token or bot_token == "your_bot_token_here" or len(bot_token) < 10:
        print("❌ ERROR: TELEGRAM_BOT_TOKEN environment variable not properly set!")
        print("💡 SOLUTION:")
        print("   1. Get a bot token from @BotFather on Telegram")
        print("   2. Set the environment variable:")
        print("      export TELEGRAM_BOT_TOKEN='your_actual_token_here'")
        print("      export TELEGRAM_USER_ID='your_user_id_here'")
        print("   3. Run the bot again")
        return
    
    if not os.getenv("TELEGRAM_USER_ID"):
        print("⚠️  WARNING: TELEGRAM_USER_ID environment variable not set (optional for single-user mode)")
    
    try:
        # Initialize and run the bot
        bot = LibraryDownBot()
        asyncio.run(bot.run())
    except ValueError as e:
        print(f"❌ Configuration Error: {e}")
        print("💡 Please check your environment variables and try again.")
    except Exception as e:
        print(f"❌ Bot failed to start: {e}")
        print("💡 Make sure your bot token is valid and network connection is available.")


if __name__ == "__main__":
    main()