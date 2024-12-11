"""
Tests for signal processing
"""
import pytest
from unittest.mock import Mock, AsyncMock
from datetime import datetime, timezone

from src.trading.signal_processor import SignalProcessor
from src.config import SCORE_THRESHOLDS, POSITION_SIZES

# Test data
TEST_TOKEN = "test_token"
TEST_SYMBOL = "TEST"
TEST_PRICE = 10.0
TEST_SIZE = 0.05

@pytest.fixture
def processor():
    """Create test signal processor"""
    return SignalProcessor()

@pytest.mark.asyncio
class TestSignalProcessor:
    """Test signal processing functionality"""
    
    async def test_valid_signal(self, processor):
        """Test valid signal processing"""
        signal = {
            'token_address': TEST_TOKEN,
            'symbol': TEST_SYMBOL,
            'category': 'AI',
            'score': 200  # Above threshold
        }
        
        trade_params = await processor.process_signal(signal)
        assert trade_params is not None
        assert trade_params['token_address'] == TEST_TOKEN
        assert trade_params['symbol'] == TEST_SYMBOL
        assert trade_params['category'] == 'AI'
        assert trade_params['size'] == POSITION_SIZES['AI']
        
    async def test_invalid_signal(self, processor):
        """Test invalid signal handling"""
        # Score below threshold
        signal = {
            'token_address': TEST_TOKEN,
            'symbol': TEST_SYMBOL,
            'category': 'AI',
            'score': 100  # Below threshold
        }
        
        trade_params = await processor.process_signal(signal)
        assert trade_params is None
        
        # Invalid category
        signal = {
            'token_address': TEST_TOKEN,
            'symbol': TEST_SYMBOL,
            'score': 200
        }
        
        trade_params = await processor.process_signal(signal)
        assert trade_params is None
        
    async def test_score_thresholds(self, processor):
        """Test score threshold validation"""
        for category, threshold in SCORE_THRESHOLDS.items():
            # Test score at threshold
            signal = {
                'token_address': TEST_TOKEN,
                'symbol': TEST_SYMBOL,
                'category': category,
                'score': threshold
            }
            trade_params = await processor.process_signal(signal)
            assert trade_params is not None
            
            # Test score below threshold
            signal['score'] = threshold - 1
            trade_params = await processor.process_signal(signal)
            assert trade_params is None
            
    async def test_position_sizing(self, processor):
        """Test position size calculation"""
        for category, size in POSITION_SIZES.items():
            signal = {
                'token_address': TEST_TOKEN,
                'symbol': TEST_SYMBOL,
                'category': category,
                'score': SCORE_THRESHOLDS[category] + 1  # Above threshold
            }
            trade_params = await processor.process_signal(signal)
            assert trade_params is not None
            assert trade_params['size'] == size
            
    async def test_error_handling(self, processor):
        """Test error handling"""
        # Missing required fields
        signal = {
            'token_address': TEST_TOKEN
        }
        trade_params = await processor.process_signal(signal)
        assert trade_params is None
        
        # Invalid data types
        signal = {
            'token_address': TEST_TOKEN,
            'symbol': TEST_SYMBOL,
            'category': 'AI',
            'score': 'invalid'  # Should be number
        }
        trade_params = await processor.process_signal(signal)
        assert trade_params is None
        
    async def test_timestamp_inclusion(self, processor):
        """Test timestamp included in trade params"""
        signal = {
            'token_address': TEST_TOKEN,
            'symbol': TEST_SYMBOL,
            'category': 'AI',
            'score': 200
        }
        
        trade_params = await processor.process_signal(signal)
        assert trade_params is not None
        assert 'timestamp' in trade_params
        timestamp = datetime.fromisoformat(trade_params['timestamp'].replace('Z', '+00:00'))
        assert isinstance(timestamp, datetime)
        assert timestamp.tzinfo == timezone.utc
