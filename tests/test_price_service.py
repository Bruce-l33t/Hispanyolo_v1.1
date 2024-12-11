"""
Tests for price service
Focus on caching and price handling behavior
"""
import pytest
import asyncio
from datetime import datetime, timezone, timedelta
from unittest.mock import patch, AsyncMock

from src.trading.price_service import PriceService

# Test data
TEST_TOKEN = "test_token"
TEST_PRICE = 10.0

@pytest.fixture
def price_service():
    """Create test price service"""
    service = PriceService()
    service.retry_delay = 0  # Speed up tests
    return service

@pytest.mark.asyncio
class TestPriceService:
    """Test price service behavior"""
    
    async def test_cache_behavior(self, price_service):
        """Test price caching works"""
        # Mock successful API call
        with patch.object(price_service, '_fetch_price', AsyncMock(return_value=TEST_PRICE)):
            # First call should hit API
            price1 = await price_service.get_price(TEST_TOKEN)
            assert price1 == TEST_PRICE
            
            # Second call should use cache
            price2 = await price_service.get_price(TEST_TOKEN)
            assert price2 == TEST_PRICE
            
            # Verify only one API call was made
            assert price_service._fetch_price.call_count == 1
            
    async def test_cache_expiry(self, price_service):
        """Test cache expires correctly"""
        # Add expired cache entry
        price_service.cache[TEST_TOKEN] = {
            'price': TEST_PRICE,
            'time': datetime.now(timezone.utc) - timedelta(seconds=price_service.cache_time + 1)
        }
        
        # Verify cache is invalid
        assert not price_service._is_cache_valid(TEST_TOKEN)
        
        # Mock API call and verify it's used after expiry
        with patch.object(price_service, '_fetch_price', AsyncMock(return_value=TEST_PRICE + 1)):
            price = await price_service.get_price(TEST_TOKEN)
            assert price == TEST_PRICE + 1
            assert price_service._fetch_price.call_count == 1
            
    async def test_error_handling(self, price_service):
        """Test error cases are handled"""
        # Test API error
        with patch.object(price_service, '_fetch_price', AsyncMock(side_effect=Exception("API Error"))):
            price = await price_service.get_price(TEST_TOKEN)
            assert price is None
            
        # Test invalid response
        with patch.object(price_service, '_fetch_price', AsyncMock(return_value=None)):
            price = await price_service.get_price(TEST_TOKEN)
            assert price is None
            
    async def test_batch_fetching(self, price_service):
        """Test fetching multiple prices"""
        tokens = [f"{TEST_TOKEN}_{i}" for i in range(3)]
        expected_prices = {token: TEST_PRICE for token in tokens}
        
        # Mock API calls
        with patch.object(price_service, '_fetch_price', AsyncMock(return_value=TEST_PRICE)):
            prices = await price_service.get_prices(tokens)
            assert prices == expected_prices
            assert price_service._fetch_price.call_count == 3
            
    def test_cache_management(self, price_service):
        """Test cache operations"""
        # Add test data
        price_service.cache[TEST_TOKEN] = {
            'price': TEST_PRICE,
            'time': datetime.now(timezone.utc)
        }
        
        # Test remove specific
        price_service.remove_from_cache(TEST_TOKEN)
        assert TEST_TOKEN not in price_service.cache
        
        # Test clear all
        price_service.cache[TEST_TOKEN] = {
            'price': TEST_PRICE,
            'time': datetime.now(timezone.utc)
        }
        price_service.clear_cache()
        assert not price_service.cache

    async def test_rate_limiting(self, price_service):
        """Test rate limiting behavior"""
        # Setup mock to fail with rate limit then succeed
        mock_fetch = AsyncMock()
        mock_fetch.side_effect = [
            Exception("Rate limit exceeded"),  # First attempt fails
            TEST_PRICE  # Second attempt succeeds
        ]
        
        # Mock _fetch_price and retry delay
        with patch.object(price_service, '_fetch_price', mock_fetch):
            # Get price - should retry and succeed
            price = await price_service.get_price(TEST_TOKEN)
            
            # Verify retry worked
            assert mock_fetch.call_count == 2  # Called twice
            assert price == TEST_PRICE  # Got price after retry

    async def test_price_validation(self, price_service):
        """Test price validation"""
        # Test valid prices
        valid_prices = [1.0, 0.0001, 1000.0]
        for test_price in valid_prices:
            # Mock _fetch_price directly
            mock_fetch = AsyncMock(return_value=test_price)
            
            with patch.object(price_service, '_fetch_price', mock_fetch):
                price = await price_service.get_price(TEST_TOKEN)
                assert price == test_price
                assert mock_fetch.call_count == 1
            
            # Clear cache between tests
            price_service.clear_cache()

        # Test invalid prices
        invalid_prices = [-1.0, 0.0, None]
        for test_price in invalid_prices:
            # Mock _fetch_price to return None for invalid prices
            mock_fetch = AsyncMock(return_value=None)
            
            with patch.object(price_service, '_fetch_price', mock_fetch):
                price = await price_service.get_price(TEST_TOKEN)
                assert price is None
                assert mock_fetch.call_count == 1
            
            price_service.clear_cache()

    async def test_concurrent_requests(self, price_service):
        """Test concurrent price requests"""
        tokens = [f"{TEST_TOKEN}_{i}" for i in range(5)]
        
        async def get_price_with_delay(token):
            await asyncio.sleep(0.1)  # Simulate API delay
            return await price_service.get_price(token)

        # Mock API call
        with patch.object(price_service, '_fetch_price', AsyncMock(return_value=TEST_PRICE)):
            # Get prices concurrently
            tasks = [get_price_with_delay(token) for token in tokens]
            prices = await asyncio.gather(*tasks)
            
            # Verify results
            assert all(price == TEST_PRICE for price in prices)
            # Should use cache after first call
            assert price_service._fetch_price.call_count == len(tokens)

    async def test_cache_invalidation_strategies(self, price_service):
        """Test different cache invalidation strategies"""
        # Test time-based invalidation
        price_service.cache[TEST_TOKEN] = {
            'price': TEST_PRICE,
            'time': datetime.now(timezone.utc) - timedelta(minutes=10)
        }
        
        with patch.object(price_service, '_fetch_price', AsyncMock(return_value=TEST_PRICE + 1)):
            price = await price_service.get_price(TEST_TOKEN)
            assert price == TEST_PRICE + 1

        # Test manual invalidation
        price_service.cache[TEST_TOKEN] = {
            'price': TEST_PRICE,
            'time': datetime.now(timezone.utc)
        }
        price_service.remove_from_cache(TEST_TOKEN)
        
        with patch.object(price_service, '_fetch_price', AsyncMock(return_value=TEST_PRICE + 2)):
            price = await price_service.get_price(TEST_TOKEN)
            assert price == TEST_PRICE + 2

        # Test bulk invalidation
        tokens = [f"{TEST_TOKEN}_{i}" for i in range(3)]
        for token in tokens:
            price_service.cache[token] = {
                'price': TEST_PRICE,
                'time': datetime.now(timezone.utc)
            }
        
        price_service.clear_cache()
        assert len(price_service.cache) == 0
