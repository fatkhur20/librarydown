import asyncio
import os
import sys
import pytest

# Add src to path
sys.path.insert(0, '/root/librarydown')

from src.engine.platforms.youtube import YouTubeDownloader
from src.core.config import settings

@pytest.mark.asyncio
async def test_youtube():
    print("🚀 Testing YouTubeDownloader...")
    downloader = YouTubeDownloader()
    url = "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
    
    try:
        print(f"📥 Fetching formats for: {url}")
        formats = await downloader.get_formats(url)
        print(f"✅ Found {len(formats['formats'])} formats")
        print(f"🎬 Title: {formats['title']}")
        
        # Test download (audio only to be fast)
        print(f"📥 Downloading audio...")
        result = await downloader.download(url, quality="audio")
        print("✅ Download completed!")
        
        # Check if file exists
        video_id = formats['url'].split('=')[-1]
        audio_file = os.path.join(settings.MEDIA_FOLDER, f"{video_id}_audio.m4a")
        if os.path.exists(audio_file):
            print(f"✅ Audio file exists at: {audio_file}")
            print(f"⚖️ Size: {os.path.getsize(audio_file) / 1024 / 1024:.2f} MB")
        else:
            print(f"❌ Audio file NOT found at: {audio_file}")
            
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    asyncio.run(test_youtube())
