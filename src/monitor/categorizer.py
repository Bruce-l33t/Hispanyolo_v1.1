"""
Token categorization system
Detects AI signals in token metadata
"""
import logging
from typing import Dict, List, Tuple, Optional
import requests

from ..config import BIRDEYE_SETTINGS
import dontshare as d

class SignalDetector:
    """Detects AI signals in token metadata"""
    def __init__(self):
        self.logger = logging.getLogger('signal_detector')
        
        # AI signals - if any of these are found, it's an AI token
        self.ai_signals = [
            # Primary signals
            'ai', 'artificial intelligence', 'gpt', 'claude', 'llm',
            'backroom', 'base model', 'latent space', 'ai16z',
            # Secondary signals
            'neural', 'autonomous', 'model', 'intelligence',
            'existential', 'infinite', 'stealth', 'synthetic',
            'consciousness', 'hyperspace', 'mindscape', 'sentient',
            'glitch', 'entropy', 'fragmentation', 'digital',
            'cybernetic', 'distortion',
            # Context signals
            'pattern', 'simulation', 'manifold', 'entropy',
            'metameme', 'egregore', 'metacognition',
            'dreamtime', 'semiotic', 'recursive',
            'adjacent possible', 'performance artist',
            'shattered', 'reality', 'void', 'digital being',
            'emergence', 'collective consciousness'
        ]

    def analyze_text(self, text: str) -> bool:
        """Analyze text for AI signals"""
        text = text.lower()
        
        # Check each signal
        for signal in self.ai_signals:
            if signal in text:
                self.logger.info(f"Found AI signal: '{signal}' in text: '{text}'")
                return True
                
        return False

class TokenCategorizer:
    """Manages token categorization and metadata"""
    def __init__(self):
        self.logger = logging.getLogger('token_categorizer')
        self.signal_detector = SignalDetector()
        self.metadata_cache: Dict[str, Dict] = {}
        self.pending_tokens: List[str] = []  # Tokens waiting for metadata fetch
        self.batch_size = 100  # Maximum tokens per request
        
    def get_token_metadata(self, token_address: str) -> Optional[dict]:
        """Get token metadata from Birdeye"""
        if token_address in self.metadata_cache:
            return self.metadata_cache[token_address]
            
        url = f"{BIRDEYE_SETTINGS['base_url']}{BIRDEYE_SETTINGS['endpoints']['token_metadata_single']}"
        headers = {
            **BIRDEYE_SETTINGS['headers'],
            "X-API-KEY": d.birdeye_api_key,
            "accept": "application/json",
            "x-chain": "solana"
        }
        params = {"address": token_address}
        
        try:
            response = requests.get(url, headers=headers, params=params)
            response.raise_for_status()  # Raise exception for non-200 status codes
            
            data = response.json()
            if not data.get('success', False):
                self.logger.warning(f"API returned success=false for {token_address[:8]}")
                return None
                
            token_data = data.get('data')
            if not token_data:
                self.logger.warning(f"No data field in response for {token_address[:8]}")
                return None
                
            # Verify required fields
            required_fields = ['address', 'name', 'symbol', 'decimals']
            if not all(field in token_data for field in required_fields):
                self.logger.warning(f"Missing required fields in metadata for {token_address[:8]}")
                return None
                
            # Cache and return valid metadata
            self.metadata_cache[token_address] = token_data
            return token_data
            
        except requests.exceptions.RequestException as e:
            self.logger.error(f"Request error fetching metadata for {token_address[:8]}: {str(e)}")
            return None
        except Exception as e:
            self.logger.error(f"Error processing metadata for {token_address[:8]}: {str(e)}")
            return None

    def categorize_token(self, token_address: str, symbol: str) -> Tuple[str, float]:
        """Categorize token and return (category, confidence)"""
        metadata = self.get_token_metadata(token_address)
        if not metadata:
            self.logger.warning(f"No metadata for {symbol} ({token_address[:4]})")
            return "MEME", 0.0  # Default to MEME if no metadata

        name = metadata.get('name', '')
        # Get description from extensions
        description = metadata.get('extensions', {}).get('description', '')
        
        # Debug log the metadata we're analyzing
        self.logger.debug(
            f"Analyzing token {symbol}:\n"
            f"Name: {name}\n"
            f"Description: {description}"
        )
        
        # Analyze all available text
        text = f"{name} {symbol} {description}"
        is_ai = self.signal_detector.analyze_text(text)

        # Simple categorization - if it has AI signals, it's AI
        if is_ai:
            category = "AI"
            confidence = 1.0
        else:
            category = "MEME"
            confidence = 0.0
            
        self.logger.info(
            f"Categorized {symbol} as {category} "
            f"(confidence: {confidence:.2f})"
        )
        return category, confidence
