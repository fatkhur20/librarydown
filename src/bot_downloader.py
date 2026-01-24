"""Telegram bot for LibraryDown - Direct video download functionality"""

import os
import asyncio
import tempfile
from typing import Dict, Any, Optional
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder, 
    CommandHandler, 
    MessageHandler, 
    filters,
    ContextTypes,
    CallbackQueryHandler
)
from loguru import logger
from urllib.parse import urlparse
import aiohttp
import time

# Import our utilities
from src.utils.url_validator import URLValidator
from src.utils.security import security_validator
from src.engine.platforms.youtube import YouTubeDownloader
from src.engine.platforms.tiktok import TikTokDownloader
from src.engine.platforms.instagram import InstagramDownloader
from src.engine.platforms.soundcloud import SoundCloudDownloader
from src.engine.platforms.dailymotion import DailymotionDownloader
from src.engine.platforms.twitch import TwitchDownloader
from src.engine.platforms.reddit import RedditDownloader
from src.engine.platforms.vimeo import VimeoDownloader
from src.engine.platforms.facebook import FacebookDownloader
from src.engine.platforms.bilibili import BilibiliDownloader
from src.engine.platforms.linkedin import LinkedInDownloader
from src.engine.platforms.pinterest import PinterestDownloader
from src.core.config import settings


class LibraryDownBot:
    def __init__(self):
        # Check if token is properly configured
        self.token = os.getenv("TELEGRAM_BOT_TOKEN")
        if not self.token or self.token == "your_bot_token_here" or len(self.token) < 10:
            raise ValueError("TELEGRAM_BOT_TOKEN environment variable not properly set. Please configure via environment variables.")
        
        self.user_id = os.getenv("TELEGRAM_USER_ID")
        self.media_folder = settings.MEDIA_FOLDER
        
        # Platform mapping
        self.platform_mapping = {
            'youtube': YouTubeDownloader,
            'tiktok': TikTokDownloader,
            'instagram': InstagramDownloader,
            'soundcloud': SoundCloudDownloader,
            'dailymotion': DailymotionDownloader,
            'twitch': TwitchDownloader,
            'reddit': RedditDownloader,
            'vimeo': VimeoDownloader,
            'facebook': FacebookDownloader,
            'bilibili': BilibiliDownloader,
            'linkedin': LinkedInDownloader,
            'pinterest': PinterestDownloader
        }
        
        # Initialize bot
        self.application = ApplicationBuilder().token(self.token).build()
        self.setup_handlers()
    
    def setup_handlers(self):
        """Setup bot command handlers."""
        # Command handlers
        self.application.add_handler(CommandHandler("start", self.start))
        self.application.add_handler(CommandHandler("help", self.help))
        self.application.add_handler(CommandHandler("download", self.download_command))
        self.application.add_handler(CommandHandler("status", self.status))
        
        # Message handler for URLs
        self.application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_url_message))
        
        # Callback query handler for inline keyboards
        self.application.add_handler(CallbackQueryHandler(self.handle_callback_query))
    
    async def start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /start command."""
        welcome_text = """
🤖 **LibraryDown Bot - Download Videos from Social Media**

Send me a video URL from any supported platform:
• YouTube, TikTok, Instagram, SoundCloud
• Dailymotion, Twitch, Reddit, Vimeo
• Facebook, Bilibili, LinkedIn, Pinterest

**Commands:**
/start - Show this message
/download - Download a video (followed by URL)
/status - Check bot status
/help - Show help information

Just paste a URL and I'll download it for you! 🎥
        """
        await update.message.reply_text(welcome_text, parse_mode="Markdown")
    
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
3. Wait for download to complete
4. Receive the video file

**Quality Options:**
• Default: 720p
• Audio only: specify "audio" after URL

Enjoy downloading! 🚀
        """
        await update.message.reply_text(help_text, parse_mode="Markdown")
    
    async def status(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /status command."""
        status_text = f"""
📊 **LibraryDown Bot Status**

• Bot: Active ✅
• Supported Platforms: 12
• Media Folder: {self.media_folder}
• Version: 2.0.0
• Last Update: {time.strftime('%Y-%m-%d %H:%M:%S')}
        """
        await update.message.reply_text(status_text, parse_mode="Markdown")
    
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
        
        # Check if message contains a URL
        if self.is_valid_url(message_text):
            await self.process_download(update, message_text, "720p")
        else:
            await update.message.reply_text("🔗 Please send a valid video URL to download.")
    
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
        platform = URLValidator.detect_platform(url)
        if platform == "unknown":
            await update.message.reply_text("❌ Unsupported platform. Supported platforms:\nYouTube, TikTok, Instagram, SoundCloud, Dailymotion, Twitch, Reddit, Vimeo, Facebook, Bilibili, LinkedIn, Pinterest")
            return
        
        # Notify user that download is starting
        await update.message.reply_text(f"🔄 Starting download from {platform.title()}...\nURL: {url}")
        
        try:
            # Get appropriate downloader
            downloader_class = self.platform_mapping.get(platform)
            if not downloader_class:
                await update.message.reply_text(f"❌ Download not implemented for {platform}")
                return
            
            downloader = downloader_class()
            
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
                else:
                    # If file doesn't exist locally, provide alternative
                    await update.message.reply_text(
                        f"✅ Download completed but file not available for direct sending.\n\nTitle: {result.get('title', 'Video')}\nPlatform: {platform.title()}\nDuration: {result.get('duration', 'Unknown')}"
                    )
            else:
                # If no video files, send metadata
                await update.message.reply_text(
                    f"✅ Download completed but no video file available.\n\nTitle: {result.get('title', 'Video')}\nPlatform: {platform.title()}\nDuration: {result.get('duration', 'Unknown')}"
                )
        
        except Exception as e:
            logger.error(f"[BOT] Download failed for {url}: {e}")
            await update.message.reply_text(f"❌ Download failed: {str(e)}")
    
    async def handle_callback_query(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle inline keyboard callbacks."""
        query = update.callback_query
        await query.answer()
        
        # Process callback based on data
        if query.data.startswith("quality_"):
            quality = query.data.replace("quality_", "")
            # Here we could implement quality selection
            await query.edit_message_text(f"Selected quality: {quality}")
    
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
            ]
        ]
        return InlineKeyboardMarkup(keyboard)
    
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