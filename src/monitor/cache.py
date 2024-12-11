"""
Cache implementation for monitor components
"""
import asyncio
import logging
import time
from typing import Dict, Any, Optional, List, Callable

logger = logging.getLogger(__name__)

class MetadataCache:
    """Cache for API responses and metadata"""
    def __init__(self, ttl: int = 3600):  # 1 hour default TTL
        self.cache: Dict[str, Dict[str, Any]] = {}
        self.ttl = ttl

    def get(self, key: str) -> Optional[Any]:
        """Get value from cache if not expired"""
        if key in self.cache:
            entry = self.cache[key]
            if time.time() - entry['time'] < self.ttl:
                return entry['data']
            else:
                # Remove expired entry
                del self.cache[key]
        return None

    def set(self, key: str, value: Any) -> None:
        """Set value in cache with current timestamp"""
        self.cache[key] = {
            'data': value,
            'time': time.time()
        }

    def clear(self) -> None:
        """Clear all cached data"""
        self.cache.clear()

    def cleanup(self) -> None:
        """Remove expired entries"""
        now = time.time()
        expired = [
            key for key, entry in self.cache.items()
            if now - entry['time'] >= self.ttl
        ]
        for key in expired:
            del self.cache[key]

class BatchProcessor:
    """Process items in batches with rate limiting"""
    def __init__(self, batch_size: int = 10, delay: float = 0.1):
        self.batch_size = batch_size
        self.delay = delay  # Delay between batches in seconds

    def get_batches(self, items: list) -> list:
        """Split items into batches"""
        return [
            items[i:i + self.batch_size]
            for i in range(0, len(items), self.batch_size)
        ]

    async def process_batch(self, batch: List[Any], processor: Callable) -> None:
        """Process a batch with error handling"""
        try:
            await processor(batch)
        except Exception as e:
            # On batch failure, try processing items individually
            logger.error(f"Batch processing failed: {e}")
            for item in batch:
                try:
                    await processor([item])
                except Exception as e:
                    logger.error(f"Error processing item {item}: {e}")

    async def process_all(self, items: list, processor: Callable) -> None:
        """Process all items in batches with rate limiting"""
        batches = self.get_batches(items)
        for i, batch in enumerate(batches):
            await self.process_batch(batch, processor)
            
            # Add delay between batches (not after last batch)
            if i < len(batches) - 1:
                await asyncio.sleep(self.delay)
