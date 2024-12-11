"""
Tests for wallet management functionality
"""
import pytest
from datetime import datetime, timezone, timedelta
from unittest.mock import Mock, AsyncMock

from src.models import WalletStatus
from src.monitor.wallet_manager import WalletManager

# Test data
TEST_WALLET = "test_wallet"
TEST_SCORE = 1000.0
TEST_TIME = datetime.now(timezone.utc)

@pytest.fixture
def wallet_manager():
    """Create test wallet manager"""
    manager = WalletManager()
    manager.wallet_scores = {TEST_WALLET: TEST_SCORE}
    return manager

@pytest.mark.asyncio
class TestWalletManager:
    """Test wallet management functionality"""
    
    async def test_status_transitions(self, wallet_manager):
        """Test wallet status transitions"""
        # Initial state
        assert TEST_WALLET not in wallet_manager.wallet_tiers
        
        # First activity - should become VERY_ACTIVE
        await wallet_manager.update_wallet_activity(TEST_WALLET, TEST_TIME)
        assert wallet_manager.wallet_tiers[TEST_WALLET].status == WalletStatus.VERY_ACTIVE
        
        # After delay - should become ACTIVE
        old_time = TEST_TIME - timedelta(minutes=30)
        await wallet_manager.update_wallet_activity(TEST_WALLET, old_time)
        assert wallet_manager.wallet_tiers[TEST_WALLET].status == WalletStatus.ACTIVE
        
        # After longer delay - should become WATCHING
        old_time = TEST_TIME - timedelta(hours=2)
        await wallet_manager.update_wallet_activity(TEST_WALLET, old_time)
        assert wallet_manager.wallet_tiers[TEST_WALLET].status == WalletStatus.WATCHING
        
        # After very long delay - should become ASLEEP
        old_time = TEST_TIME - timedelta(hours=12)
        await wallet_manager.update_wallet_activity(TEST_WALLET, old_time)
        assert wallet_manager.wallet_tiers[TEST_WALLET].status == WalletStatus.ASLEEP
        
        # New activity - should become VERY_ACTIVE again
        await wallet_manager.update_wallet_activity(TEST_WALLET, TEST_TIME)
        assert wallet_manager.wallet_tiers[TEST_WALLET].status == WalletStatus.VERY_ACTIVE
    
    async def test_score_calculation(self, wallet_manager):
        """Test wallet score calculation"""
        # Initial score
        score = wallet_manager.get_wallet_score(TEST_WALLET)
        assert score == TEST_SCORE
        
        # Unknown wallet
        score = wallet_manager.get_wallet_score("unknown")
        assert score == 0
        
        # Score updates
        wallet_manager.wallet_scores[TEST_WALLET] = 500.0
        score = wallet_manager.get_wallet_score(TEST_WALLET)
        assert score == 500.0
        
        # Score validation
        wallet_manager.wallet_scores[TEST_WALLET] = -100.0
        score = wallet_manager.get_wallet_score(TEST_WALLET)
        assert score == 0  # Should not allow negative scores
    
    async def test_status_updates(self, wallet_manager):
        """Test wallet status update scenarios"""
        # Setup test wallets
        active_wallet = "active_wallet"
        inactive_wallet = "inactive_wallet"
        
        # Add wallets with different states
        await wallet_manager.update_wallet_activity(active_wallet, TEST_TIME)
        old_time = TEST_TIME - timedelta(hours=24)
        await wallet_manager.update_wallet_activity(inactive_wallet, old_time)
        
        # Verify initial states
        assert wallet_manager.wallet_tiers[active_wallet].status == WalletStatus.VERY_ACTIVE
        assert wallet_manager.wallet_tiers[inactive_wallet].status == WalletStatus.ASLEEP
        
        # Update statuses
        await wallet_manager.update_wallet_statuses()
        
        # Both wallets should still exist but with updated statuses
        assert active_wallet in wallet_manager.wallet_tiers
        assert inactive_wallet in wallet_manager.wallet_tiers
        assert wallet_manager.wallet_tiers[inactive_wallet].status == WalletStatus.ASLEEP
    
    async def test_wallet_tracking(self, wallet_manager):
        """Test wallet activity tracking"""
        # Track new wallet
        await wallet_manager.update_wallet_activity(TEST_WALLET, TEST_TIME)
        assert TEST_WALLET in wallet_manager.wallet_tiers
        
        # Update existing wallet
        new_time = TEST_TIME + timedelta(minutes=5)
        await wallet_manager.update_wallet_activity(TEST_WALLET, new_time)
        wallet = wallet_manager.wallet_tiers[TEST_WALLET]
        assert wallet.last_active == new_time
        
        # Check transaction count
        assert wallet.transaction_count == 2
    
    async def test_batch_processing(self, wallet_manager):
        """Test processing multiple wallets"""
        wallets = ["wallet1", "wallet2", "wallet3"]
        scores = {w: 100.0 for w in wallets}
        wallet_manager.wallet_scores = scores
        
        # Update all wallets
        for wallet in wallets:
            await wallet_manager.update_wallet_activity(wallet, TEST_TIME)
        
        # Verify all tracked
        for wallet in wallets:
            assert wallet in wallet_manager.wallet_tiers
            assert wallet_manager.wallet_tiers[wallet].status == WalletStatus.VERY_ACTIVE
    
    async def test_error_handling(self, wallet_manager):
        """Test error handling scenarios"""
        # Invalid wallet address
        await wallet_manager.update_wallet_activity("", TEST_TIME)
        assert "" not in wallet_manager.wallet_tiers
        
        # Invalid timestamp
        with pytest.raises(AttributeError):
            await wallet_manager.update_wallet_activity(TEST_WALLET, None)
    
    async def test_status_counts(self, wallet_manager):
        """Test wallet status counting"""
        # Add wallets with different states
        await wallet_manager.update_wallet_activity("very_active", TEST_TIME)
        
        active_time = TEST_TIME - timedelta(minutes=30)
        await wallet_manager.update_wallet_activity("active", active_time)
        
        watching_time = TEST_TIME - timedelta(hours=2)
        await wallet_manager.update_wallet_activity("watching", watching_time)
        
        asleep_time = TEST_TIME - timedelta(hours=12)
        await wallet_manager.update_wallet_activity("asleep", asleep_time)
        
        # Get status counts
        counts = wallet_manager.get_status_counts()
        
        # Verify counts
        assert counts[WalletStatus.VERY_ACTIVE] == 1
        assert counts[WalletStatus.ACTIVE] == 1
        assert counts[WalletStatus.WATCHING] == 1
        assert counts[WalletStatus.ASLEEP] == 1
    
    async def test_monitoring_frequency(self, wallet_manager):
        """Test wallet monitoring frequency based on status"""
        # Setup wallet
        await wallet_manager.update_wallet_activity(TEST_WALLET, TEST_TIME)
        assert TEST_WALLET in wallet_manager.get_wallets_to_check()  # VERY_ACTIVE wallets checked
        
        # After inactivity, should be checked less frequently
        old_time = TEST_TIME - timedelta(hours=2)
        await wallet_manager.update_wallet_activity(TEST_WALLET, old_time)
        await wallet_manager.update_wallet_statuses()
        assert TEST_WALLET not in wallet_manager.get_wallets_to_check()  # WATCHING wallets not checked
        
        # New activity should restore frequent checking
        await wallet_manager.update_wallet_activity(TEST_WALLET, TEST_TIME)
        assert TEST_WALLET in wallet_manager.get_wallets_to_check()  # Back to being checked
