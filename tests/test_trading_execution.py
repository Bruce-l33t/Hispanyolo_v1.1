"""
Tests for trading execution using real transactions
"""
import pytest
import logging
from decimal import Decimal

from src.trading.alchemy import AlchemyTrader
from src.config import WSOL_ADDRESS, TEST_SETTINGS

# Test data
TEST_TOKEN = TEST_SETTINGS['token_address']
TEST_AMOUNT = Decimal(str(TEST_SETTINGS['amount']))
INVALID_TOKEN = "InvalidTokenAddressFor404Error" * 2

class TestTradingExecution:
    """Test trading execution with real transactions"""
    
    @pytest.fixture
    async def trader(self):
        """Create AlchemyTrader instance"""
        trader = AlchemyTrader()
        # Set debug logging
        trader.logger.setLevel(logging.DEBUG)
        return trader
        
    async def test_valid_quote(self, trader):
        """Test getting quote for valid token"""
        quote = trader.get_jupiter_quote(
            token_address=TEST_TOKEN,
            amount_in=TEST_AMOUNT
        )
        
        assert quote is not None
        assert 'routePlan' in quote
        assert quote['inAmount'] == str(int(TEST_AMOUNT * 1_000_000_000))
        
    async def test_invalid_token(self, trader):
        """Test handling invalid token address"""
        quote = trader.get_jupiter_quote(
            token_address=INVALID_TOKEN,
            amount_in=TEST_AMOUNT
        )
        
        assert quote is None  # Should handle invalid token gracefully
        
    async def test_complete_swap(self, trader):
        """Test complete swap flow with minimal amount"""
        tx_hash = await trader.execute_swap(
            token_address=TEST_TOKEN,
            amount_in=TEST_AMOUNT
        )
        
        assert tx_hash is not None
        assert len(tx_hash) == 88  # Verify valid Solana transaction signature

if __name__ == "__main__":
    pytest.main([__file__, '-v'])
