"""
Token metadata analysis using Birdeye API
"""
import logging
from typing import Dict, Optional, Tuple
import requests
from datetime import datetime, timedelta
from dontshare import birdeye_api_key

# API Settings
BIRDEYE_SETTINGS = {
    "base_url": "https://public-api.birdeye.so",
    "endpoints": {
        "token_metadata": "/defi/v3/token/meta-data/single"
    },
    "headers": {
        "X-API-KEY": birdeye_api_key,
        "accept": "application/json",
        "x-chain": "solana"
    }
}

# Cache settings
CACHE_SETTINGS = {
    "metadata_ttl": 3600,  # 1 hour
    "max_size": 1000      # Maximum number of items to cache
}

class MetadataAnalyzer:
    """Analyzes token metadata from Birdeye"""
    
    def __init__(self):
        self.logger = logging.getLogger('metadata_analyzer')
        self.metadata_cache: Dict[str, Dict] = {}
        self.cache_timestamps: Dict[str, datetime] = {}
        
        # AI signals - if any of these are found, it's potentially an AI token
        self.ai_signals = {
            'primary': [
                'ai', 'artificial intelligence', 'gpt', 'claude', 'llm',
                'backroom', 'base model', 'latent space', 'ai16z'
            ],
            'secondary': [
                'neural', 'autonomous', 'model', 'intelligence',
                'existential', 'infinite', 'stealth', 'synthetic',
                'consciousness', 'hyperspace', 'mindscape', 'sentient'
            ]
        }
        
    def _clean_cache(self):
        """Remove expired cache entries"""
        now = datetime.now()
        expired_keys = [
            key for key, timestamp in self.cache_timestamps.items()
            if (now - timestamp).total_seconds() > CACHE_SETTINGS['metadata_ttl']
        ]
        for key in expired_keys:
            self.metadata_cache.pop(key, None)
            self.cache_timestamps.pop(key, None)
            
    def get_metadata(self, token_address: str) -> Optional[dict]:
        """Get token metadata from Birdeye with caching"""
        # Clean expired cache entries
        self._clean_cache()
        
        # Check cache
        if token_address in self.metadata_cache:
            return self.metadata_cache[token_address]
            
        # Fetch from API
        url = f"{BIRDEYE_SETTINGS['base_url']}{BIRDEYE_SETTINGS['endpoints']['token_metadata']}"
        headers = BIRDEYE_SETTINGS['headers']
        params = {"address": token_address}
        
        try:
            response = requests.get(url, headers=headers, params=params)
            response.raise_for_status()
            
            data = response.json()
            if not data.get('success', False):
                self.logger.warning(f"API returned success=false for {token_address[:8]}")
                return None
                
            token_data = data.get('data')
            if not token_data:
                self.logger.warning(f"No data field in response for {token_address[:8]}")
                return None
                
            # Verify required fields
            required_fields = ['address', 'name', 'symbol']
            if not all(field in token_data for field in required_fields):
                self.logger.warning(f"Missing required fields in metadata for {token_address[:8]}")
                return None
                
            # Cache the result
            self.metadata_cache[token_address] = token_data
            self.cache_timestamps[token_address] = datetime.now()
            
            return token_data
            
        except requests.exceptions.RequestException as e:
            self.logger.error(f"Request error fetching metadata for {token_address[:8]}: {str(e)}")
            return None
        except Exception as e:
            self.logger.error(f"Error processing metadata for {token_address[:8]}: {str(e)}")
            return None
            
    def analyze_text(self, text: str) -> Tuple[bool, float, dict]:
        """
        Analyze text for AI signals
        Returns: (is_ai, confidence, details)
        """
        if not text:
            return False, 0.0, {'matches': {'primary': [], 'secondary': []}, 'text_analyzed': ''}
            
        text = text.lower()
        matches = {
            'primary': [],
            'secondary': []
        }
        
        # Check each signal category
        for category in ['primary', 'secondary']:
            for signal in self.ai_signals[category]:
                if signal in text:
                    matches[category].append(signal)
                    self.logger.debug(f"Found {category} AI signal: '{signal}' in text")
        
        # Calculate initial confidence
        primary_weight = 0.7
        secondary_weight = 0.3
        
        confidence = 0.0
        if matches['primary']:
            confidence += primary_weight * (len(matches['primary']) / len(self.ai_signals['primary']))
        if matches['secondary']:
            confidence += secondary_weight * (len(matches['secondary']) / len(self.ai_signals['secondary']))
            
        confidence = min(confidence, 1.0)
        
        return bool(matches['primary']), confidence, {
            'matches': matches,
            'text_analyzed': text
        }
        
    def analyze_token(self, token_address: str, symbol: str) -> Tuple[bool, float, dict]:
        """
        Analyze token metadata for AI signals
        Returns: (is_ai, confidence, details)
        """
        metadata = None
        try:
            metadata = self.get_metadata(token_address)
            if not metadata:
                self.logger.warning(f"No metadata for {symbol} ({token_address[:4]})")
                return False, 0.0, {'error': 'No metadata available'}
                
            name = metadata.get('name', '')
            symbol = metadata.get('symbol', symbol)  # Use provided symbol as fallback
            
            # Handle null extensions safely
            extensions = metadata.get('extensions') or {}
            description = extensions.get('description', '')
            twitter = extensions.get('twitter', '')
            
            # Analyze all available text
            text = f"{name} {symbol} {description}"
            is_ai, confidence, details = self.analyze_text(text)
            
            # Add metadata to details
            details['metadata'] = {
                'name': name,
                'symbol': symbol,
                'description': description[:100] + '...' if description else 'N/A'
            }
            
            # Add Twitter URL if available
            if twitter:
                details['twitter_url'] = twitter
                
            return is_ai, confidence, details
            
        except Exception as e:
            self.logger.error(f"Error analyzing token {symbol} ({token_address[:4]}): {str(e)}")
            # Return safe default values with what we know
            return False, 0.0, {
                'error': str(e),
                'metadata': {
                    'name': metadata.get('name', 'N/A') if metadata else 'N/A',
                    'symbol': symbol,
                    'description': 'N/A'
                }
            } 