from typing import Any, Dict, Optional, List
import json
import httpx
import re
import os
import asyncio
from src.engine.base_downloader import BaseDownloader
from src.engine.extractor import BaseExtractor
from src.core.config import settings

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36',
    'Referer': 'https://www.tiktok.com/'
}

def find_item_struct_recursive(data: Any) -> Optional[Dict[str, Any]]:
    """Recursively searches for a key named 'itemStruct'."""
    if isinstance(data, dict):
        if 'itemStruct' in data and isinstance(data['itemStruct'], dict):
            return data['itemStruct']
        for value in data.values():
            found = find_item_struct_recursive(value)
            if found: return found
    elif isinstance(data, list):
        for item in data:
            found = find_item_struct_recursive(item)
            if found: return found
    return None

class TikTokExtractor(BaseExtractor):
    def __init__(self, json_data: Dict[str, Any]):
        self.json_data = json_data
        self.item = json_data
        self.author = self.item.get('author', {})
        self.stats = self.item.get('stats', {})
        self.music = self.item.get('music', {})
    
    def _extract_base_data(self) -> Dict[str, Any]:
        return {
            "platform": "tiktok",
            "source_url": f"https://www.tiktok.com/@{self.author.get('uniqueId')}/video/{self.item.get('id')}",
            "fetched_at": self.item.get('createTime'),
            "id": self.item.get('id'),
            "caption": self.item.get('desc'),
            "hashtags": [tag.get('hashtagName') for tag in self.item.get('textExtra', []) if tag.get('hashtagName')],
            "created_at": self.item.get('createTime'),
            "author": {
                "username": self.author.get('uniqueId'),
                "display_name": self.author.get('nickname'),
                "profile_url": f"https://www.tiktok.com/@{self.author.get('uniqueId')}",
                "avatar_url": self.author.get('avatarThumb'),
                "is_verified": self.author.get('verified'),
                "followers_count": self.author.get('followerCount'),
                "following_count": self.author.get('followingCount')
            },
            "statistics": {
                "views": self.stats.get('playCount'),
                "likes": self.stats.get('diggCount'),
                "comments": self.stats.get('commentCount'),
                "shares": self.stats.get('shareCount')
            },
            "extra": {
                "music": {
                    "title": self.music.get('title'),
                    "author": self.music.get('authorName'),
                    "url": self.music.get('playUrl')
                },
                "region": self.item.get('region')
            }
        }
    
    def extract_all_data(self) -> Dict[str, Any]:
        base_data = self._extract_base_data()
        video_data = self.item.get('video')
        image_post_data = self.item.get('imagePost')
        
        if video_data:
            base_data.update({
                "content_type": "video",
                "duration": video_data.get('duration'),
                "media": {
                    "video": [{
                        "quality": f"{video_data.get('height')}p",
                        "codec": video_data.get('codecType'),
                        "direct_url": video_data.get('playAddr'),
                        "size": video_data.get('videoApi', {}).get('size')
                    }],
                    "thumbnail": video_data.get('cover')
                }
            })
        elif image_post_data:
            images = []
            thumbnail = None
            for image in image_post_data.get('images', []):
                if image.get('imageURL', {}).get('urlList'):
                    images.append({
                        "url": image['imageURL']['urlList'][0],
                        "width": image.get('imageWidth'),
                        "height": image.get('imageHeight')
                    })
            if image_post_data.get('cover', {}).get('urlList'):
                thumbnail = image_post_data['cover']['urlList'][0]
            base_data.update({
                "content_type": "carousel",
                "duration": None,
                "media": {
                    "images": images,
                    "thumbnail": thumbnail
                }
            })
        else:
            print(f"[{base_data.get('platform')}] Warning: No video or image data found for ID {base_data.get('id')}. Returning partial metadata.")
            base_data['content_type'] = 'unknown'
            base_data['media'] = {}
        return base_data

class TikTokDownloader(BaseDownloader):
    @property
    def platform(self) -> str: return "tiktok"

    async def get_formats(self, url: str) -> Dict[str, Any]:
        """Get available formats for a TikTok video without downloading
        
        Args:
            url: TikTok video URL
            
        Returns:
            Dict containing video metadata and available formats
            
        Note: TikTok provides fixed quality formats, not multiple resolutions like YouTube
        """
        async with httpx.AsyncClient(headers=HEADERS, follow_redirects=True) as client:
            try:
                # Get page content
                response = await client.get(url, timeout=30.0)
                response.raise_for_status()
                match = re.search(r'<script id="__UNIVERSAL_DATA_FOR_REHYDRATION__" type="application/json">(.*?)</script>', response.text)
                if not match:
                    raise ValueError("Could not find data script in HTML response.")
                
                json_data = json.loads(match.group(1))
                scope = json_data.get('__DEFAULT_SCOPE__', {})
                
                # Find item data
                item_struct = find_item_struct_recursive(scope)
                
                if not item_struct:
                    if scope.get('webapp.error-page'):
                        raise ValueError("Content not available. The page is an error page.")
                    raise ValueError("Could not find any 'itemStruct' in the page data.")

                extractor = TikTokExtractor(item_struct)
                data = extractor.extract_all_data()
                
                # Extract format info
                formats = []
                if data.get('content_type') == 'video':
                    video_data = item_struct.get('video', {})
                    filesize = video_data.get('videoApi', {}).get('size')
                    formats.append({
                        'format_id': 'default',
                        'quality': f"{video_data.get('height')}p" if video_data.get('height') else 'unknown',
                        'ext': 'mp4',
                        'filesize_mb': round(filesize / (1024 * 1024), 2) if filesize else None,
                        'height': video_data.get('height'),
                        'width': video_data.get('width'),
                        'fps': None,
                        'vcodec': video_data.get('codecType'),
                        'acodec': 'aac',
                        'format_note': None
                    })
                elif data.get('content_type') == 'carousel':
                    # For carousel, return image info
                    for i, img in enumerate(data.get('media', {}).get('images', [])):
                        formats.append({
                            'format_id': f'image_{i+1}',
                            'quality': f"{img.get('height')}p" if img.get('height') else 'unknown',
                            'ext': 'jpeg',
                            'filesize_mb': None,
                            'height': img.get('height'),
                            'width': img.get('width'),
                            'fps': None,
                            'vcodec': None,
                            'acodec': None,
                            'format_note': 'image'
                        })
                
                return {
                    'platform': 'tiktok',
                    'url': url,
                    'title': data.get('caption', '')[:100],
                    'thumbnail': data.get('media', {}).get('thumbnail'),
                    'duration': data.get('duration'),
                    'formats': formats
                }
                
            except Exception as e:
                raise

    async def _download_asset(self, client: httpx.AsyncClient, asset_url: str, local_filename: str, asset_type: str) -> Optional[str]:
        """Download a single asset (video, image, thumbnail, etc.) and return its public URL"""
        if not asset_url or not isinstance(asset_url, str):
            return None
        
        local_filepath = os.path.join(settings.MEDIA_FOLDER, local_filename)
        try:
            async with client.stream('GET', asset_url, headers=HEADERS, timeout=60.0) as response:
                if response.status_code >= 400:
                    return None
                with open(local_filepath, 'wb') as f:
                    async for chunk in response.aiter_bytes():
                        f.write(chunk)
            return f"{settings.API_BASE_URL}/{settings.MEDIA_FOLDER}/{local_filename}"
        except httpx.RequestError:
            return None

    async def download(self, url: str, quality: str = "720p") -> Dict[str, Any]:
        """
        Download TikTok content
        
        Args:
            url: TikTok video URL
            quality: Desired quality (TikTok provides what's available, this is for API consistency)
        
        Note: TikTok videos come in fixed qualities from their API.
        The quality parameter is accepted but may not affect the actual download
        as TikTok serves specific formats.
        """
        async with httpx.AsyncClient(headers=HEADERS, follow_redirects=True) as client:
            try:
                # 1. Get page content
                response = await client.get(url, timeout=30.0); response.raise_for_status()
                match = re.search(r'<script id="__UNIVERSAL_DATA_FOR_REHYDRATION__" type="application/json">(.*?)</script>', response.text)
                if not match: raise ValueError("Could not find data script in HTML response.")
                
                json_data = json.loads(match.group(1))
                scope = json_data.get('__DEFAULT_SCOPE__', {})
                
                # 2. Use the recursive search to find the item data
                print(f"[{self.platform}] Searching for item data in JSON response...")
                item_struct = find_item_struct_recursive(scope)
                
                if not item_struct:
                    if scope.get('webapp.error-page'):
                        raise ValueError("Content not available. The page is an error page.")
                    raise ValueError("Could not find any 'itemStruct' in the page data.")

                print(f"[{self.platform}] Found item data successfully.")
                extractor = TikTokExtractor(item_struct)
                data = extractor.extract_all_data()
                
                # 3. Download assets
                content_id = data.get('id'); author_id = data.get('author', {}).get('username')
                if not content_id or not author_id: raise ValueError("Extracted data is missing essential 'id' or 'author' fields.")
                
                common_tasks = {"thumbnail": self._download_asset(client, data.get('media', {}).get('thumbnail'), f"{content_id}_thumb.jpeg", "thumbnail"), "avatar": self._download_asset(client, data.get('author', {}).get('avatar_url'), f"{author_id}_avatar.jpeg", "avatar"), "music": self._download_asset(client, data.get('extra', {}).get('music', {}).get('url'), f"{content_id}_music.mp3", "music")}
                if data.get('content_type') == 'video':
                    video_url = data.get('media', {}).get('video', [{}])[0].get('direct_url')
                    common_tasks['video'] = self._download_asset(client, video_url, f"{content_id}.mp4", "video")
                elif data.get('content_type') == 'carousel':
                    for i, img in enumerate(data.get('media', {}).get('images', [])):
                        common_tasks[f'image_{i}'] = self._download_asset(client, img.get('url'), f"{content_id}_image_{i+1}.jpeg", f"image {i+1}")
                
                results = await asyncio.gather(*common_tasks.values())
                result_map = dict(zip(common_tasks.keys(), results))

                if result_map.get('thumbnail'): data['media']['thumbnail'] = result_map['thumbnail']
                if result_map.get('avatar'): data['author']['avatar_url'] = result_map['avatar']
                if result_map.get('music'): data['extra']['music']['url'] = result_map['music']
                if data['content_type'] == 'video' and result_map.get('video'):
                    data['media']['video'][0]['direct_url'] = result_map['video']
                elif data['content_type'] == 'carousel':
                    final_image_urls: List[Dict[str, Any]] = []
                    for i, original_img in enumerate(data['media']['images']):
                        new_url = result_map.get(f'image_{i}')
                        final_image_urls.append({"url": new_url if new_url else original_img.get('url'), "width": original_img.get('width'), "height": original_img.get('height')})
                    data['media']['images'] = final_image_urls
                
                return data
            except Exception:
                raise
