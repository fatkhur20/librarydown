"""
YouTube Cipher/Signature Decryption Module
Pure Python implementation without js2py dependency
Handles YouTube's obfuscated signature decryption for video URLs
"""

import re
import httpx
from typing import Dict, Optional, List
from loguru import logger
from urllib.parse import parse_qs, unquote

class YouTubeCipher:
    def __init__(self):
        self.player_url: Optional[str] = None
        self.js_code: Optional[str] = None
        self.transform_plan: List = []
        self.var_name: Optional[str] = None
    
    async def get_player_url(self, video_page_html: str) -> str:
        """Extract player JavaScript URL from video page"""
        patterns = [
            r'"jsUrl"\s*:\s*"([^"]+)"',
            r'"PLAYER_JS_URL"\s*:\s*"([^"]+)"',
            r'<script\s+src="([^"]+)"[^>]*name="player_ias',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, video_page_html)
            if match:
                player_url = match.group(1)
                # Handle escaped forward slashes
                player_url = player_url.replace('\\/', '/')
                if player_url.startswith('/'):
                    player_url = f"https://www.youtube.com{player_url}"
                logger.info(f"[Cipher] Found player URL: {player_url[:50]}...")
                return player_url
        
        raise ValueError("Could not find player URL in video page")
    
    async def fetch_player_js(self, player_url: str) -> str:
        """Fetch the player JavaScript code"""
        async with httpx.AsyncClient() as client:
            response = await client.get(player_url, timeout=30.0)
            response.raise_for_status()
            return response.text
    
    def _get_initial_function_name(self, js_code: str) -> str:
        """Get the name of the main signature function"""
        patterns = [
            # Pattern for signature decipher function
            r'\.sig\|\|([a-zA-Z0-9$]+)\(',
            r'\bc\s*&&\s*[adf]\.set\([^,]+\s*,\s*encodeURIComponent\s*\(\s*([a-zA-Z0-9$]+)\(',
            r'\b[a-zA-Z0-9]+\s*&&\s*[a-zA-Z0-9]+\.set\([^,]+\s*,\s*encodeURIComponent\s*\(\s*([a-zA-Z0-9$]+)\(',
            # Look for function that splits, manipulates, and joins
            r'([a-zA-Z0-9$]{2,})\s*=\s*function\([a-zA-Z]\)\{[a-zA-Z]=\1\.split\(""\)',
            r',([a-zA-Z0-9$]{2,})\([a-zA-Z],\d+\);',
            # Alternative patterns
            r'\.sig\|\|([a-zA-Z0-9$]+)\(',
            r'yt\.akamaized\.net/\)\s*\|\|\s*.*?\s*[cs]\s*&&\s*[adf]\.set\([^,]+\s*,\s*(?:encodeURIComponent\s*\()?\s*([a-zA-Z0-9$]+)\(',
        ]
        
        for pattern in patterns:
            matches = re.finditer(pattern, js_code)
            for match in matches:
                func_name = match.group(1)
                # Skip built-in functions
                if func_name in ['decodeURIComponent', 'encodeURIComponent', 'parseInt', 'parseFloat']:
                    continue
                # Check if this is actually a function definition
                if re.search(rf'{re.escape(func_name)}\s*=\s*function', js_code):
                    logger.info(f"[Cipher] Found function name: {func_name}")
                    return func_name
        
        raise ValueError("Could not find initial function name")
    
    def _get_transform_object(self, js_code: str, func_name: str) -> str:
        """Get the transform object name"""
        # Find the function definition
        func_pattern = rf'{re.escape(func_name)}\s*=\s*function\([a-zA-Z0-9]+\)\s*\{{([^}}]+)\}}'
        match = re.search(func_pattern, js_code)
        
        if not match:
            func_pattern = rf'function\s+{re.escape(func_name)}\([a-zA-Z0-9]+\)\s*\{{([^}}]+)\}}'
            match = re.search(func_pattern, js_code)
        
        if not match:
            raise ValueError(f"Could not find function definition for {func_name}")
        
        func_body = match.group(1)
        
        # Extract the object name used for transformations
        obj_pattern = r'([a-zA-Z0-9$]+)\.[a-zA-Z0-9]+\([a-zA-Z0-9]+,\d+\)'
        match = re.search(obj_pattern, func_body)
        
        if match:
            obj_name = match.group(1)
            logger.info(f"[Cipher] Found transform object: {obj_name}")
            return obj_name
        
        raise ValueError("Could not find transform object")
    
    def _parse_function(self, js_code: str, func_name: str) -> List[tuple]:
        """Parse the decipher function and extract operations"""
        # Find function body
        func_pattern = rf'{re.escape(func_name)}\s*=\s*function\([a-zA-Z0-9]+\)\s*\{{(.*?)\}}'
        match = re.search(func_pattern, js_code, re.DOTALL)
        
        if not match:
            func_pattern = rf'function\s+{re.escape(func_name)}\([a-zA-Z0-9]+\)\s*\{{(.*?)\}}'
            match = re.search(func_pattern, js_code, re.DOTALL)
        
        if not match:
            raise ValueError(f"Could not parse function: {func_name}")
        
        func_body = match.group(1)
        operations = []
        
        # Match operations like: ab.cd(a,123)
        pattern = r'([a-zA-Z0-9$]+)\.([a-zA-Z0-9]+)\([a-zA-Z0-9]+,(\d+)\)'
        
        for match in re.finditer(pattern, func_body):
            obj_name = match.group(1)
            method_name = match.group(2)
            argument = int(match.group(3))
            operations.append((obj_name, method_name, argument))
        
        logger.info(f"[Cipher] Found {len(operations)} operations")
        return operations
    
    def _get_transform_map(self, js_code: str, obj_name: str) -> Dict[str, str]:
        """Extract transformation methods from the object"""
        # Find the object definition
        obj_pattern = rf'var\s+{re.escape(obj_name)}\s*=\s*\{{([^}}]+)\}}'
        match = re.search(obj_pattern, js_code, re.DOTALL)
        
        if not match:
            obj_pattern = rf'{re.escape(obj_name)}\s*=\s*\{{([^}}]+)\}}'
            match = re.search(obj_pattern, js_code, re.DOTALL)
        
        if not match:
            raise ValueError(f"Could not find object definition: {obj_name}")
        
        obj_body = match.group(1)
        transform_map = {}
        
        # Parse each method
        # Pattern: methodName:function(a,b){...}
        method_pattern = r'([a-zA-Z0-9$]+)\s*:\s*function\([a-zA-Z0-9,\s]+\)\s*\{([^}]+)\}'
        
        for match in re.finditer(method_pattern, obj_body):
            method_name = match.group(1)
            method_body = match.group(2)
            
            # Identify operation type
            if 'reverse' in method_body:
                transform_map[method_name] = 'reverse'
            elif 'splice' in method_body:
                transform_map[method_name] = 'splice'
            else:
                # Swap operation
                transform_map[method_name] = 'swap'
        
        logger.info(f"[Cipher] Transform map: {transform_map}")
        return transform_map
    
    def _apply_transform(self, sig_array: List[str], operation: str, argument: int) -> List[str]:
        """Apply a single transformation to the signature array"""
        if operation == 'reverse':
            sig_array.reverse()
        elif operation == 'splice':
            sig_array = sig_array[argument:]
        elif operation == 'swap':
            idx = argument % len(sig_array)
            sig_array[0], sig_array[idx] = sig_array[idx], sig_array[0]
        
        return sig_array
    
    async def initialize(self, video_page_html: str):
        """Initialize cipher with video page HTML"""
        try:
            # Get player URL and fetch JS
            self.player_url = await self.get_player_url(video_page_html)
            self.js_code = await self.fetch_player_js(self.player_url)
            
            # Get function name
            func_name = self._get_initial_function_name(self.js_code)
            
            # Get transform object name
            obj_name = self._get_transform_object(self.js_code, func_name)
            self.var_name = obj_name
            
            # Parse operations
            operations = self._parse_function(self.js_code, func_name)
            
            # Get transform map
            transform_map = self._get_transform_map(self.js_code, obj_name)
            
            # Build transform plan
            self.transform_plan = []
            for obj, method, arg in operations:
                if method in transform_map:
                    self.transform_plan.append((transform_map[method], arg))
            
            logger.info(f"[Cipher] Initialized with {len(self.transform_plan)} transforms")
            
        except Exception as e:
            logger.error(f"[Cipher] Initialization failed: {e}")
            raise
    
    def decipher(self, signature: str) -> str:
        """Decipher a signature"""
        if not self.transform_plan:
            raise ValueError("Cipher not initialized")
        
        sig_array = list(signature)
        
        for operation, argument in self.transform_plan:
            sig_array = self._apply_transform(sig_array, operation, argument)
        
        return ''.join(sig_array)
    
    def get_video_url(self, cipher_data: str) -> str:
        """Extract and decipher video URL from cipher string"""
        # Parse the cipher string
        params = {}
        
        # Handle both URL format and direct cipher format
        if cipher_data.startswith('http'):
            # It's already a working URL
            return cipher_data
        
        for param in cipher_data.split('&'):
            if '=' in param:
                key, value = param.split('=', 1)
                params[key] = unquote(value)
        
        # Check if signature needs deciphering
        if 's' in params:
            # Signature needs deciphering
            encrypted_sig = params['s']
            decrypted_sig = self.decipher(encrypted_sig)
            
            base_url = params.get('url', '')
            sig_param = params.get('sp', 'signature')
            
            separator = '&' if '?' in base_url else '?'
            final_url = f"{base_url}{separator}{sig_param}={decrypted_sig}"
            
            logger.info("[Cipher] Successfully deciphered URL")
            return final_url
        
        elif 'url' in params:
            # No signature, just return URL
            return params['url']
        
        else:
            # Return as-is
            return cipher_data

