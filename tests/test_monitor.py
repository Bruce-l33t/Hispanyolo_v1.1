"""
Tests for monitor components
"""
import pytest
from datetime import datetime, timezone, timedelta
from unittest.mock import Mock, AsyncMock, patch
import requests
import asyncio

from src.monitor import WhaleMonitor, TokenMetricsManager, WalletManager
from src.models import WalletTier, WalletStatus
from src.config import WSOL_ADDRESS

# Test data
TEST_WALLET = "test_wallet"
TEST_TOKEN = "test_token"
TEST_SCORE = 1000.0

class MockResponse:
    def __init__(self, status_code=200, json_data=None):
        self.status_code = status_code
        self._json_data = json_data or {}

    def json(self):
        return self._json_data

    def raise_for_status(self):
        if self.status_code != 200:
            raise requests.HTTPError(f"HTTP Error: {self.status_code}")

@pytest.fixture
def monitor():
    """Create test monitor"""
    return WhaleMonitor()

@pytest.fixture
def token_metrics():
    """Create test token metrics"""
    return TokenMetricsManager()

@pytest.fixture
def wallet_manager():
    """Create test wallet manager"""
    return WalletManager()

@pytest.mark.asyncio
class TestTokenMetrics:
    """Test token metrics tracking"""
    
    async def test_score_tracking(self, token_metrics):
        """Test score accumulation"""
        # Process buy
        await token_metrics.process_transaction(
            token_address=TEST_TOKEN,
            symbol="TEST",
            amount=1.0,
            tx_type='buy',
            wallet_address=TEST_WALLET,
            wallet_score=TEST_SCORE
        )
        
        metrics = await token_metrics.get_or_create_metrics(TEST_TOKEN, "TEST")
        assert metrics.score > 0
        assert metrics.buy_count == 1
        
        # Process sell
        await token_metrics.process_transaction(
            token_address=TEST_TOKEN,
            symbol="TEST",
            amount=0.5,
            tx_type='sell',
            wallet_address=TEST_WALLET,
            wallet_score=TEST_SCORE
        )
        
        assert metrics.sell_count == 1
        assert metrics.score < TEST_SCORE  # Score reduced by sell
        
    async def test_metrics_creation(self, token_metrics):
        """Test metrics creation"""
        metrics = await token_metrics.get_or_create_metrics(
            token_address=TEST_TOKEN,
            symbol="TEST"
        )
        
        assert metrics.symbol == "TEST"
        assert metrics.token_address == TEST_TOKEN
        assert metrics.category in ["AI", "MEME"]  # Only these categories
        
    async def test_cleanup(self, token_metrics):
        """Test old token cleanup"""
        # Add test token
        metrics = await token_metrics.get_or_create_metrics(
            token_address=TEST_TOKEN,
            symbol="TEST"
        )
        
        # Set old update time
        metrics.last_update = datetime.now(timezone.utc).replace(
            hour=0, minute=0, second=0
        )
        
        # Cleanup
        token_metrics.cleanup_old_tokens(max_age_hours=1)
        assert TEST_TOKEN not in token_metrics.token_metrics

@pytest.mark.asyncio
class TestWalletManager:
    """Test wallet management"""
    
    def test_wallet_scoring(self, wallet_manager):
        """Test wallet score tracking"""
        # Load test scores
        wallet_manager.wallet_scores = {TEST_WALLET: TEST_SCORE}
        
        score = wallet_manager.get_wallet_score(TEST_WALLET)
        assert score == TEST_SCORE
        
    async def test_status_transitions(self, wallet_manager):
        """Test wallet status changes"""
        # Initial status
        wallet_manager.wallet_scores = {TEST_WALLET: TEST_SCORE}
        wallet_manager.wallet_tiers[TEST_WALLET] = WalletTier(
            status=WalletStatus.WATCHING
        )
        
        # Update activity
        now = datetime.now(timezone.utc)
        await wallet_manager.update_wallet_activity(TEST_WALLET, now)
        
        # Should transition to VERY_ACTIVE
        assert wallet_manager.wallet_tiers[TEST_WALLET].status == WalletStatus.VERY_ACTIVE
        
    async def test_inactivity_status_update(self, wallet_manager):
        """Test status updates based on inactivity"""
        # Add test wallet as ACTIVE
        wallet_manager.wallet_scores = {TEST_WALLET: TEST_SCORE}
        wallet_manager.wallet_tiers[TEST_WALLET] = WalletTier(
            status=WalletStatus.ACTIVE,
            last_active=datetime.now(timezone.utc).replace(hour=0, minute=0, second=0)
        )
        
        # Update statuses - should become ASLEEP due to inactivity
        await wallet_manager.update_wallet_statuses()
        
        # Wallet should still exist but be ASLEEP
        assert TEST_WALLET in wallet_manager.wallet_tiers
        assert wallet_manager.wallet_tiers[TEST_WALLET].status == WalletStatus.ASLEEP
        
        # New activity should make it VERY_ACTIVE again
        await wallet_manager.update_wallet_activity(TEST_WALLET, datetime.now(timezone.utc))
        assert wallet_manager.wallet_tiers[TEST_WALLET].status == WalletStatus.VERY_ACTIVE

@pytest.mark.asyncio
class TestMonitor:
    """Test monitor system"""
    
    async def test_monitoring_tasks(self, monitor):
        """Test separate monitoring tasks"""
        # Setup test wallets
        monitor.wallet_manager.wallet_scores = {
            "very_active": TEST_SCORE,
            "active": TEST_SCORE,
            "watching": TEST_SCORE,
            "asleep": TEST_SCORE
        }
        
        # Add wallets with different states
        now = datetime.now(timezone.utc)
        await monitor.wallet_manager.update_wallet_activity("very_active", now)
        await monitor.wallet_manager.update_wallet_activity(
            "active", 
            now - timedelta(minutes=30)
        )
        await monitor.wallet_manager.update_wallet_activity(
            "watching",
            now - timedelta(hours=2)
        )
        await monitor.wallet_manager.update_wallet_activity(
            "asleep",
            now - timedelta(hours=12)
        )
        
        # Mock transaction processing
        processed_wallets = set()
        
        async def mock_process_wallet(wallet, initial_scan=False):
            processed_wallets.add(wallet)
        
        with patch.object(monitor, 'process_wallet', mock_process_wallet):
            # Start monitoring
            monitor.is_running = True
            tasks = [
                asyncio.create_task(monitor.monitor_active_wallets()),
                asyncio.create_task(monitor.monitor_watching_wallets()),
                asyncio.create_task(monitor.monitor_asleep_wallets())
            ]
            
            # Let it run briefly
            await asyncio.sleep(0.1)
            
            # Stop monitoring
            monitor.is_running = False
            for task in tasks:
                task.cancel()
            await asyncio.gather(*tasks, return_exceptions=True)
            
            # Verify wallets were processed according to status
            assert "very_active" in processed_wallets
            assert "active" in processed_wallets
            assert "watching" in processed_wallets
            assert "asleep" in processed_wallets
    
    async def test_swap_detection(self, monitor):
        """Test real swap detection"""
        # Valid swap
        tx = {
            'balanceChange': [
                {
                    'address': WSOL_ADDRESS,
                    'amount': -1000000000  # 1 SOL
                },
                {
                    'address': TEST_TOKEN,
                    'amount': 1000000
                }
            ]
        }
        assert monitor._is_real_swap(tx)
        
        # Not a swap
        tx = {
            'balanceChange': [
                {
                    'address': WSOL_ADDRESS,
                    'amount': 0
                }
            ]
        }
        assert not monitor._is_real_swap(tx)
        
    async def test_transaction_processing(self, monitor):
        """Test transaction processing"""
        # Setup test wallet
        monitor.wallet_manager.wallet_scores = {TEST_WALLET: TEST_SCORE}
        monitor.wallet_manager.wallet_tiers[TEST_WALLET] = WalletTier(
            status=WalletStatus.WATCHING
        )
        
        # Test transaction
        tx = {
            'blockTime': datetime.now(timezone.utc).isoformat(),
            'balanceChange': [
                {
                    'address': WSOL_ADDRESS,
                    'amount': -1000000000,  # 1 SOL
                    'decimals': 9
                },
                {
                    'address': TEST_TOKEN,
                    'amount': 1000000,
                    'decimals': 6,
                    'symbol': 'TEST'
                }
            ]
        }
        
        await monitor.process_transaction(tx, TEST_WALLET)
        
        # Verify wallet updated
        assert TEST_WALLET in monitor.wallet_manager.wallet_tiers
        assert monitor.wallet_manager.wallet_tiers[TEST_WALLET].transaction_count == 1

    async def test_wallet_transactions_retry(self, monitor):
        """Test wallet transaction fetching with retries"""
        # Mock API response
        mock_response = {
            'data': {
                'solana': [
                    {
                        'blockTime': datetime.now(timezone.utc).isoformat(),
                        'balanceChange': []
                    }
                ]
            }
        }

        # Mock requests to fail twice then succeed
        with patch('requests.get') as mock_get:
            mock_get.side_effect = [
                Exception("API Error"),  # First attempt fails
                Exception("API Error"),  # Second attempt fails
                Mock(
                    raise_for_status=Mock(),
                    json=Mock(return_value=mock_response)
                )  # Third attempt succeeds
            ]

            # Should succeed after retries
            result = await monitor.get_wallet_transactions(TEST_WALLET)
            assert result == mock_response
            assert mock_get.call_count == 3  # Verify retry count

    async def test_initial_scan_filtering(self, monitor):
        """Test initial scan transaction filtering"""
        now = datetime.now(timezone.utc)
        old_tx_time = (now - timedelta(minutes=30)).isoformat()
        recent_tx_time = (now - timedelta(minutes=5)).isoformat()

        mock_response = {
            'data': {
                'solana': [
                    {
                        'blockTime': old_tx_time,
                        'balanceChange': []
                    },
                    {
                        'blockTime': recent_tx_time,
                        'balanceChange': []
                    }
                ]
            }
        }

        with patch('requests.get') as mock_get:
            mock_get.return_value = Mock(
                raise_for_status=Mock(),
                json=Mock(return_value=mock_response)
            )

            # Get transactions with initial scan filtering
            result = await monitor.get_wallet_transactions(TEST_WALLET, initial_scan=True)
            
            # Should only include recent transaction
            assert len(result['data']['solana']) == 1
            assert result['data']['solana'][0]['blockTime'] == recent_tx_time

    async def test_error_handling(self, monitor):
        """Test error handling in transaction processing"""
        # Setup test wallet
        monitor.wallet_manager.wallet_scores = {TEST_WALLET: TEST_SCORE}
        monitor.wallet_manager.wallet_tiers[TEST_WALLET] = WalletTier(
            status=WalletStatus.WATCHING
        )

        # Invalid transaction format
        invalid_tx = {
            'blockTime': 'invalid_time',
            'balanceChange': 'invalid_changes'
        }

        # Should handle error gracefully
        await monitor.process_transaction(invalid_tx, TEST_WALLET)
        
        # Wallet should still exist but not be updated
        assert TEST_WALLET in monitor.wallet_manager.wallet_tiers
        assert monitor.wallet_manager.wallet_tiers[TEST_WALLET].transaction_count == 0

    async def test_batch_processing(self, monitor):
        """Test batch processing of wallets"""
        # Setup test wallets
        test_wallets = [f"{TEST_WALLET}_{i}" for i in range(5)]
        for wallet in test_wallets:
            monitor.wallet_manager.wallet_scores[wallet] = TEST_SCORE
            monitor.wallet_manager.wallet_tiers[wallet] = WalletTier(
                status=WalletStatus.WATCHING
            )

        # Mock get_wallet_transactions to return empty data
        async def mock_get_transactions(*args, **kwargs):
            return {'data': {'solana': []}}

        with patch.object(monitor, 'get_wallet_transactions', side_effect=mock_get_transactions):
            # Process wallet batch
            await monitor.process_wallet_batch(test_wallets)

            # Verify all wallets were marked as checked
            for wallet in test_wallets:
                assert monitor.wallet_manager.wallet_tiers[wallet].transaction_count == 0

    async def test_batch_size(self, monitor):
        """Test wallet batch size calculation"""
        test_wallets = [f"{TEST_WALLET}_{i}" for i in range(25)]
        batches = monitor.get_wallet_batches(test_wallets)

        # Should split into batches of 10
        assert len(batches) == 3
        assert len(batches[0]) == 10  # First batch
        assert len(batches[1]) == 10  # Second batch
        assert len(batches[2]) == 5   # Last batch (remainder)

    async def test_rate_limit_handling(self, monitor):
        """Test API rate limit handling"""
        # Mock rate limit response
        rate_limit_response = MockResponse(status_code=429)
        success_response = MockResponse(
            status_code=200,
            json_data={'data': {'solana': []}}
        )

        with patch('requests.get') as mock_get:
            mock_get.side_effect = [
                requests.exceptions.HTTPError("429 Rate Limited"),  # First attempt
                rate_limit_response,  # Second attempt
                success_response  # Third attempt after backoff
            ]

            # Should handle rate limit and succeed after backoff
            result = await monitor.get_wallet_transactions(TEST_WALLET)
            assert result == success_response._json_data
            assert mock_get.call_count == 3

    async def test_connection_error_recovery(self, monitor):
        """Test connection error recovery"""
        # Mock connection errors then success
        success_response = {'data': {'solana': []}}

        with patch('requests.get') as mock_get:
            mock_get.side_effect = [
                requests.exceptions.ConnectionError(),  # First attempt
                requests.exceptions.ConnectionError(),  # Second attempt
                Mock(
                    raise_for_status=Mock(),
                    json=Mock(return_value=success_response)
                )  # Third attempt
            ]

            # Should recover from connection errors
            result = await monitor.get_wallet_transactions(TEST_WALLET)
            assert result == success_response
            assert mock_get.call_count == 3

    async def test_state_recovery(self, monitor):
        """Test state recovery after errors"""
        # Setup test wallet
        monitor.wallet_manager.wallet_scores = {TEST_WALLET: TEST_SCORE}
        monitor.wallet_manager.wallet_tiers[TEST_WALLET] = WalletTier(
            status=WalletStatus.WATCHING
        )

        # Simulate error during processing
        with patch.object(monitor, 'process_transaction', side_effect=Exception("Processing error")):
            # Process batch should handle error and continue
            await monitor.process_wallet_batch([TEST_WALLET])

            # Wallet state should be preserved
            assert TEST_WALLET in monitor.wallet_manager.wallet_tiers
            assert monitor.wallet_manager.wallet_tiers[TEST_WALLET].status == WalletStatus.WATCHING

        # System should recover and process next batch
        next_wallet = f"{TEST_WALLET}_next"
        monitor.wallet_manager.wallet_scores[next_wallet] = TEST_SCORE
        monitor.wallet_manager.wallet_tiers[next_wallet] = WalletTier(
            status=WalletStatus.WATCHING
        )

        await monitor.process_wallet_batch([next_wallet])
        assert next_wallet in monitor.wallet_manager.wallet_tiers
