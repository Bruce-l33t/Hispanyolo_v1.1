"""
Integration tests for WhaleMonitor using real data
"""
import pytest
import asyncio
from datetime import datetime, timezone, timedelta
import logging

from src.monitor.monitor import WhaleMonitor
from src.models import WalletStatus

# Configure logging
logging.basicConfig(level=logging.INFO)

# Real test data
TEST_WALLETS = {
    # Known active whale wallet
    "FWcjxiv1KA8G1499CWdRZnSrGYb8yKfynTyUTSj3AZX3": 1000,  # Score of 1000
    # Another active wallet
    "AUPQhiVX4Q9eFrF962p6P6Es777ydUksbTiS69VmQ5tT": 500   # Score of 500
}

@pytest.fixture
async def monitor():
    """Create WhaleMonitor instance"""
    monitor = WhaleMonitor()
    # Load test wallet scores
    monitor.wallet_manager.wallet_scores = TEST_WALLETS.copy()
    monitor.is_running = True
    yield monitor
    monitor.is_running = False

async def test_initial_scan():
    """Test initial scan with time window"""
    monitor = WhaleMonitor()
    monitor.wallet_manager.wallet_scores = TEST_WALLETS.copy()
    
    # Do initial scan
    for wallet in TEST_WALLETS:
        txs = await monitor.get_wallet_transactions(wallet, initial_scan=True)
        assert txs is not None, f"Should get transactions for {wallet}"
        
        if 'data' in txs and 'solana' in txs['data']:
            for tx in txs['data']['solana']:
                # Verify time window
                tx_time = datetime.fromisoformat(
                    tx['blockTime'].replace('Z', '+00:00')
                )
                time_diff = datetime.now(timezone.utc) - tx_time
                assert time_diff <= timedelta(minutes=15), \
                    "Initial scan should only include transactions from last 15 minutes"

async def test_regular_scan():
    """Test regular scan respects last processed time"""
    monitor = WhaleMonitor()
    monitor.wallet_manager.wallet_scores = TEST_WALLETS.copy()
    
    # First scan to establish last_processed_time
    for wallet in TEST_WALLETS:
        txs = await monitor.get_wallet_transactions(wallet, initial_scan=True)
        assert wallet in monitor.last_processed_time, \
            "Should set last_processed_time after first scan"
    
    # Wait briefly
    await asyncio.sleep(2)
    
    # Second scan should only get newer transactions
    for wallet in TEST_WALLETS:
        initial_time = monitor.last_processed_time[wallet]
        txs = await monitor.get_wallet_transactions(wallet, initial_scan=False)
        
        if 'data' in txs and 'solana' in txs['data']:
            for tx in txs['data']['solana']:
                tx_time = datetime.fromisoformat(
                    tx['blockTime'].replace('Z', '+00:00')
                )
                assert tx_time > initial_time, \
                    "Regular scan should only include transactions after last processed time"

async def test_sol_amount_handling():
    """Test SOL amount extraction and usage"""
    monitor = WhaleMonitor()
    monitor.wallet_manager.wallet_scores = TEST_WALLETS.copy()
    
    # Process transactions for test wallets
    for wallet in TEST_WALLETS:
        txs = await monitor.get_wallet_transactions(wallet, initial_scan=True)
        if txs and 'data' in txs and 'solana' in txs['data']:
            for tx in txs['data']['solana']:
                if monitor._is_real_swap(tx):
                    # Get SOL amount
                    sol_amount = monitor._get_sol_amount(tx)
                    
                    # Verify amount calculation
                    for change in tx['balanceChange']:
                        if change['address'] == monitor.WSOL_ADDRESS:
                            expected = abs(float(change['amount'])) / 10 ** change['decimals']
                            assert sol_amount == expected, \
                                "SOL amount should match balance change"
                    
                    # Verify minimum amount filter
                    if sol_amount >= monitor.MIN_SOL_AMOUNT:
                        # Process transaction and verify metrics
                        await monitor.process_transaction(tx, wallet)
                        
                        # Find the token address that changed
                        token_address = None
                        token_amount = 0
                        for change in tx['balanceChange']:
                            if change['address'] not in [monitor.WSOL_ADDRESS, monitor.USDC_ADDRESS]:
                                token_address = change['address']
                                token_amount = float(change['amount'])
                                break
                        
                        if token_address:
                            metrics = monitor.token_metrics.token_metrics.get(token_address)
                            if metrics:
                                # Verify the transaction was recorded
                                assert metrics.total_volume > 0, \
                                    "Transaction should be recorded in metrics"
                                
                                # Verify correct amount was used
                                recent_change = metrics.recent_changes[0]
                                assert abs(recent_change['amount'] - sol_amount) < 0.000001, \
                                    "Metrics should use SOL amount"

async def test_wallet_score_application():
    """Test wallet scores are correctly applied"""
    monitor = WhaleMonitor()
    monitor.wallet_manager.wallet_scores = TEST_WALLETS.copy()
    
    # Process transactions and verify scores
    for wallet, expected_score in TEST_WALLETS.items():
        txs = await monitor.get_wallet_transactions(wallet, initial_scan=True)
        if txs and 'data' in txs and 'solana' in txs['data']:
            for tx in txs['data']['solana']:
                if monitor._is_real_swap(tx):
                    await monitor.process_transaction(tx, wallet)
                    
                    # Find affected token
                    token_address = None
                    for change in tx['balanceChange']:
                        if change['address'] not in [monitor.WSOL_ADDRESS, monitor.USDC_ADDRESS]:
                            token_address = change['address']
                            break
                    
                    if token_address:
                        metrics = monitor.token_metrics.token_metrics.get(token_address)
                        if metrics and wallet in metrics.wallet_contributions:
                            assert metrics.wallet_contributions[wallet] == expected_score, \
                                f"Wallet {wallet} should contribute its score of {expected_score}"

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
