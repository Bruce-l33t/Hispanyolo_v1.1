"""
Trading system tests
"""
import pytest
from unittest.mock import AsyncMock, patch

from src.trading.trading_system import TradingSystem

# Test data
TEST_TOKENS = {
    'BONK': {
        'address': '5gzkkG31PQSNRSQS3bZxSUnffwoAb1cxd4xy5jbWf9ki',
        'category': 'MEME'
    },
    'GRIFT': {
        'address': 'DdWs9oFuGBTFVRbhxNkKQYYYdA6X1D3H5ZMY5TZLjhfG',
        'category': 'MEME'
    },
    'UBC': {
        'address': '9psiRdn9cXYVps4F1kFuoNjd2EtmqNJXrCPmRppJpump',
        'category': 'MEME'
    }
}

class TestTradingSystem:
    """Test trading system with mocked API calls"""
    
    @pytest.fixture
    async def mock_alchemy(self):
        """Create mock Alchemy trader"""
        with patch('src.trading.trading_system.AlchemyTrader') as mock:
            # Mock successful trade
            mock.return_value.execute_swap = AsyncMock(return_value="tx_signature")
            yield mock.return_value
            
    @pytest.fixture
    async def mock_price_service(self):
        """Create mock price service"""
        with patch('src.trading.trading_system.PriceService') as mock:
            # Mock price data
            mock.return_value.get_price = AsyncMock(return_value=1.0)
            mock.return_value.get_prices = AsyncMock(return_value={
                TEST_TOKENS['BONK']['address']: 1.0,
                TEST_TOKENS['GRIFT']['address']: 1.0,
                TEST_TOKENS['UBC']['address']: 1.0
            })
            yield mock.return_value
    
    @pytest.fixture
    async def trading_system(self, mock_alchemy, mock_price_service):
        """Create trading system with mocked dependencies"""
        system = TradingSystem()
        # Replace real services with mocks
        system.trader = mock_alchemy
        system.price_service = mock_price_service
        return system
    
    async def test_signal_handling(self, trading_system):
        """Test handling of trading signals"""
        # Create signal with real token
        signal = {
            'token_address': TEST_TOKENS['BONK']['address'],
            'symbol': 'BONK',
            'category': 'MEME',
            'score': 500.0,  # Above MEME threshold
            'confidence': 0.8
        }
        
        # Process signal
        await trading_system.handle_signal(signal)
        
        # Verify position opened
        positions = trading_system.position_manager.get_active_positions()
        assert len(positions) == 1
        position = positions[0]
        assert position.token_address == TEST_TOKENS['BONK']['address']
        assert position.category == 'MEME'
        assert position.tokens == 100  # Test amount
        assert position.entry_price == pytest.approx(1.0)
        assert position.r_pnl == pytest.approx(0.0)
        assert position.ur_pnl == pytest.approx(0.0)
        
        # Verify trade execution called
        trading_system.trader.execute_swap.assert_called_once_with(
            token_address=TEST_TOKENS['BONK']['address'],
            amount_in=0.025  # MEME position size
        )
    
    async def test_position_limits(self, trading_system):
        """Test position limit enforcement"""
        # Try to open max MEME positions
        for symbol in ['BONK', 'GRIFT']:
            signal = {
                'token_address': TEST_TOKENS[symbol]['address'],
                'symbol': symbol,
                'category': 'MEME',
                'score': 500.0,
                'confidence': 0.8
            }
            await trading_system.handle_signal(signal)
        
        # Verify can't open more MEME positions
        signal = {
            'token_address': TEST_TOKENS['UBC']['address'],
            'symbol': 'UBC',
            'category': 'MEME',
            'score': 500.0,
            'confidence': 0.8
        }
        await trading_system.handle_signal(signal)
        
        # Should still only have 2 positions
        positions = trading_system.position_manager.get_active_positions()
        assert len(positions) == 2
        
        # Verify only 2 trades executed
        assert trading_system.trader.execute_swap.call_count == 2
    
    async def test_take_profit_execution(self, trading_system):
        """Test take profit execution"""
        # Example with token amounts:
        # 1. Start with 100 tokens at 1.0 SOL each
        # 2. Price goes up 60%:
        #    - Price target hit at 1.6 SOL
        #    - Sell 25 tokens (25% of 100)
        #    - Keep 75 tokens
        #    - Realized PNL = 25 * (1.6 - 1.0) = 15 SOL
        signal = {
            'token_address': TEST_TOKENS['BONK']['address'],
            'symbol': 'BONK',
            'category': 'MEME',
            'score': 500.0,
            'confidence': 0.8
        }
        await trading_system.handle_signal(signal)
        
        # Get position
        positions = trading_system.position_manager.get_active_positions()
        assert len(positions) == 1
        position = positions[0]
        
        # Mock price increase to first take profit level (60%)
        trading_system.price_service.get_prices = AsyncMock(return_value={
            TEST_TOKENS['BONK']['address']: position.entry_price * 1.6  # 60% increase
        })
        
        # Update position prices
        await trading_system.update_positions()
        
        # Verify position state after take profit
        positions = trading_system.position_manager.get_active_positions()
        assert len(positions) == 1
        position = positions[0]
        
        # Check token amount (75 tokens remaining)
        assert position.tokens == 75
        
        # Check PNL (use approx for floating point comparison)
        assert position.r_pnl == pytest.approx(15.0)  # 25 tokens * 0.6 SOL profit each
        assert position.ur_pnl == pytest.approx(45.0)  # 75 tokens * 0.6 SOL unrealized each
        assert position.total_pnl == pytest.approx(60.0)  # 15 realized + 45 unrealized
        
    async def test_error_recovery(self, trading_system):
        """Test error recovery during trading"""
        # Mock failed trade
        trading_system.trader.execute_swap = AsyncMock(return_value=None)
        
        # Create signal
        signal = {
            'token_address': TEST_TOKENS['BONK']['address'],
            'symbol': 'BONK',
            'category': 'MEME',
            'score': 500.0,
            'confidence': 0.8
        }
        
        # Process signal (should retry on error)
        await trading_system.handle_signal(signal)
        
        # Verify no position opened due to error
        positions = trading_system.position_manager.get_active_positions()
        assert len(positions) == 0
        
        # Verify retries
        assert trading_system.trader.execute_swap.call_count == 1

if __name__ == "__main__":
    pytest.main([__file__, '-v'])
