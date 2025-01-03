"""
Price fetching service
Handles price data for position management
"""
import logging
import asyncio
from typing import Dict, Optional
from datetime import datetime, timezone

from .alchemy import AlchemyTrader

class PriceService:
    """
    Handles price fetching and caching
    Used for position management
    """
    def __init__(self):
        self.logger = logging.getLogger('price_service')
        self.cache: Dict[str, Dict] = {}
        self.cache_time = 60  # Cache prices for 60 seconds
        self.max_retries = 3
        self.retry_delay = 1
        self.trader = AlchemyTrader()
        
    def _is_cache_valid(self, token_address: str) -> bool:
        """Check if cached price is still valid"""
        if token_address not in self.cache:
            return False
            
        cache_entry = self.cache[token_address]
        age = (datetime.now(timezone.utc) - cache_entry['time']).total_seconds()
        return age < self.cache_time
            
    async def _fetch_price(self, token_address: str, retry_count: int = 0) -> Optional[float]:
        """Fetch price from Jupiter quote"""
        try:
            # Get Jupiter quote for 1 SOL
            quote = self.trader.get_jupiter_quote(
                token_address=token_address,
                amount_in=1.0  # 1 SOL quote
            )
            
            if not quote:
                if retry_count < self.max_retries:
                    await asyncio.sleep(self.retry_delay * (retry_count + 1))
                    return await self._fetch_price(token_address, retry_count + 1)
                self.logger.error(f"Could not get quote for {token_address}")
                return None
                
            # Calculate price directly from quote amounts
            in_amount = float(quote['inAmount']) / 1e9  # Convert lamports to SOL
            out_amount = float(quote['outAmount']) / 1e6  # Convert to actual tokens (6 decimals)
            price = in_amount / out_amount if out_amount > 0 else 0
            
            return price
                    
        except Exception as e:
            self.logger.error(f"Error fetching price for {token_address}: {e}")
            if retry_count < self.max_retries:
                await asyncio.sleep(self.retry_delay * (retry_count + 1))
                return await self._fetch_price(token_address, retry_count + 1)
            return None
            
    async def get_price(self, token_address: str) -> Optional[float]:
        """Get token price with caching"""
        try:
            # Check cache
            if self._is_cache_valid(token_address):
                return self.cache[token_address]['price']
                
            # Fetch new price
            price = await self._fetch_price(token_address)
            if price is not None:
                # Update cache
                self.cache[token_address] = {
                    'price': price,
                    'time': datetime.now(timezone.utc)
                }
                return price
                
            return None
                    
        except Exception as e:
            self.logger.error(f"Error getting price for {token_address}: {e}")
            return None
            
    async def get_prices(self, token_addresses: list) -> Dict[str, float]:
        """Get prices for multiple tokens"""
        prices = {}
        uncached_tokens = []
        
        # Get cached prices
        for addr in token_addresses:
            if self._is_cache_valid(addr):
                prices[addr] = self.cache[addr]['price']
            else:
                uncached_tokens.append(addr)
                
        # Fetch uncached prices
        if uncached_tokens:
            tasks = [self._fetch_price(addr) for addr in uncached_tokens]
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            for addr, result in zip(uncached_tokens, results):
                if isinstance(result, Exception):
                    self.logger.error(f"Error fetching price for {addr}: {result}")
                elif result is not None:
                    prices[addr] = result
                    # Update cache
                    self.cache[addr] = {
                        'price': result,
                        'time': datetime.now(timezone.utc)
                    }
                    
        return prices
        
    def clear_cache(self):
        """Clear price cache"""
        self.cache.clear()
        
    def remove_from_cache(self, token_address: str):
        """Remove specific token from cache"""
        if token_address in self.cache:
            del self.cache[token_address]
