"""
Tests for cache and batch processing components
"""
import pytest
import asyncio
import time
from unittest.mock import Mock, AsyncMock
import logging

from src.monitor.cache import MetadataCache, BatchProcessor

logger = logging.getLogger(__name__)

@pytest.fixture
def cache():
    """Create test cache"""
    return MetadataCache(ttl=1)  # 1 second TTL for testing

@pytest.fixture
def batch_processor():
    """Create test batch processor"""
    return BatchProcessor(batch_size=2, delay=0.1)

class TestMetadataCache:
    """Test metadata caching"""

    def test_cache_get_set(self, cache):
        """Test basic cache operations"""
        # Set value
        cache.set("test_key", "test_value")
        
        # Get value
        value = cache.get("test_key")
        assert value == "test_value"
        
        # Get non-existent value
        value = cache.get("missing_key")
        assert value is None

    def test_cache_expiry(self, cache):
        """Test cache entry expiration"""
        # Set value
        cache.set("test_key", "test_value")
        
        # Value should exist
        assert cache.get("test_key") == "test_value"
        
        # Wait for expiry
        time.sleep(1.1)  # Just over TTL
        
        # Value should be expired
        assert cache.get("test_key") is None

    def test_cache_cleanup(self, cache):
        """Test expired entry cleanup"""
        # Set multiple values
        cache.set("key1", "value1")
        cache.set("key2", "value2")
        
        # Wait for expiry
        time.sleep(1.1)  # Just over TTL
        
        # Add new value
        cache.set("key3", "value3")
        
        # Cleanup
        cache.cleanup()
        
        # Check remaining entries
        assert len(cache.cache) == 1
        assert cache.get("key1") is None
        assert cache.get("key2") is None
        assert cache.get("key3") == "value3"

    def test_cache_clear(self, cache):
        """Test cache clearing"""
        # Set multiple values
        cache.set("key1", "value1")
        cache.set("key2", "value2")
        
        # Clear cache
        cache.clear()
        
        # Check cache is empty
        assert len(cache.cache) == 0
        assert cache.get("key1") is None
        assert cache.get("key2") is None

@pytest.mark.asyncio
class TestBatchProcessor:
    """Test batch processing"""

    def test_batch_splitting(self, batch_processor):
        """Test splitting items into batches"""
        items = [1, 2, 3, 4, 5]
        batches = batch_processor.get_batches(items)
        
        assert len(batches) == 3
        assert batches[0] == [1, 2]
        assert batches[1] == [3, 4]
        assert batches[2] == [5]

    async def test_batch_processing(self, batch_processor):
        """Test processing items in batches"""
        items = [1, 2, 3, 4, 5]
        processed = []
        
        async def processor(batch):
            processed.extend(batch)
        
        await batch_processor.process_all(items, processor)
        
        assert processed == items
        assert len(processed) == 5

    async def test_error_handling(self, batch_processor):
        """Test error handling during batch processing"""
        items = [1, 2, 3, 4, 5]
        processed = []
        
        async def processor(batch):
            if 3 in batch:
                raise Exception("Test error")
            processed.extend(batch)
        
        # Should continue processing despite error
        await batch_processor.process_all(items, processor)
        
        assert 1 in processed
        assert 2 in processed
        assert 4 in processed
        assert 5 in processed
        assert 3 not in processed  # Failed batch

    async def test_rate_limiting(self, batch_processor):
        """Test rate limiting between batches"""
        items = [1, 2, 3, 4]
        times = []
        
        async def processor(batch):
            times.append(time.time())
        
        start = time.time()
        await batch_processor.process_all(items, processor)
        
        # Check time between batches
        assert len(times) == 2  # Two batches
        time_between_batches = times[1] - times[0]
        assert time_between_batches >= batch_processor.delay
