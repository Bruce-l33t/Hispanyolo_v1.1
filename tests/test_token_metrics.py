import pytest
import asyncio
from datetime import datetime, timezone
from src.monitor.token_metrics import TokenMetrics

# Real tokens from transactions
TEST_TOKENS = {
    'BONK': '5gzkkG31PQSNRSQS3bZxSUnffwoAb1cxd4xy5jbWf9ki',
    'GRIFT': 'DdWs9oFuGBTFVRbhxNkKQYYYdA6X1D3H5ZMY5TZLjhfG',
    'UBC': '9psiRdn9cXYVps4F1kFuoNjd2EtmqNJXrCPmRppJpump',
    'AVB': '6d5zHW5B8RkGKd51Lpb9RqFQSqDudr9GJgZ1SgQZpump'
}

# Real wallet that traded these tokens
TEST_WALLET = "AUPQhiVX4Q9eFrF962p6P6Es777ydUksbTiS69VmQ5tT"

class TestTokenMetrics:
    """Test token metrics with real data"""
    
    @pytest.fixture
    async def metrics(self):
        """Create token metrics instance"""
        return TokenMetrics(
            token_address=TEST_TOKENS['BONK'],
            symbol='BONK',
            category='MEME'  # String instead of enum
        )
    
    async def test_wallet_contribution_limits(self, metrics):
        """Test wallet contribution limits"""
        # Add contribution from test wallet
        metrics.add_score(
            wallet_score=100.0,
            wallet_address=TEST_WALLET,
            amount=14028683.025716  # Real amount from transaction
        )
        
        # Verify contribution tracked
        assert TEST_WALLET in metrics.unique_buyers
        assert metrics.buy_count == 1
        assert metrics.sell_count == 0
        assert metrics.wallet_contributions[TEST_WALLET] == 100.0
        
        # Try adding same wallet again
        metrics.add_score(
            wallet_score=100.0,
            wallet_address=TEST_WALLET,
            amount=14028683.025716
        )
        
        # Verify no double counting
        assert len(metrics.unique_buyers) == 1
        assert metrics.buy_count == 1
        assert metrics.wallet_contributions[TEST_WALLET] == 100.0
    
    async def test_score_reduction(self, metrics):
        """Test score reduction on sell"""
        # Add initial buy
        metrics.add_score(
            wallet_score=100.0,
            wallet_address=TEST_WALLET,
            amount=14028683.025716
        )
        
        initial_score = metrics.score
        
        # Now sell
        metrics.reduce_score(
            wallet_score=100.0,
            amount=14028683.025716,
            wallet_address=TEST_WALLET
        )
        
        # Verify score reduced
        assert metrics.score < initial_score
        assert TEST_WALLET not in metrics.wallet_contributions
        assert metrics.sell_count == 1
    
    async def test_recent_changes(self, metrics):
        """Test recent changes tracking"""
        # Add buy transaction
        metrics.add_score(
            wallet_score=100.0,
            wallet_address=TEST_WALLET,
            amount=14028683.025716
        )
        
        # Verify recent change tracked
        assert len(metrics.recent_changes) == 1
        change = metrics.recent_changes[0]
        assert change['type'] == 'buy'
        assert change['amount'] == 14028683.025716
        assert 'time' in change
        
        # Add sell transaction
        metrics.reduce_score(
            wallet_score=100.0,
            amount=14028683.025716,
            wallet_address=TEST_WALLET
        )
        
        # Verify both changes tracked
        assert len(metrics.recent_changes) == 2
        assert metrics.recent_changes[0]['type'] == 'sell'
        assert metrics.recent_changes[1]['type'] == 'buy'
        
        # Verify limit of 10 recent changes
        for i in range(10):
            metrics.add_score(
                wallet_score=100.0,
                wallet_address=f"wallet_{i}",
                amount=1000.0
            )
        
        assert len(metrics.recent_changes) == 10

if __name__ == "__main__":
    pytest.main([__file__, '-v'])
