import asyncio
import pytest
import logging
from datetime import datetime, timezone
from src.monitor.new_monitor import WhaleMonitor
from src.models import WalletTier, WalletStatus

@pytest.mark.asyncio
async def test_new_monitor():
    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s [%(levelname)8s] %(message)s (%(filename)s:%(lineno)s)'
    )
    
    # Create monitor instance with just one real wallet to test
    monitor = WhaleMonitor()
    
    # Add test wallet with proper initialization
    wallet = "DYtKhdXr9YQnwNHSqckqvPGnZgQyuH7tWK5Q7dgXiPtc"
    monitor.wallet_manager.wallet_scores = {wallet: 100}
    monitor.wallet_manager.wallet_tiers[wallet] = WalletTier(
        status=WalletStatus.WATCHING,
        last_active=datetime.now(timezone.utc),
        transaction_count=0,
        score=100
    )
    
    try:
        # Start monitoring
        monitor_task = asyncio.create_task(monitor.run())
        
        # Let it run for 10 seconds
        await asyncio.sleep(10)
        
        # Check the state
        assert monitor.is_running == True
        assert len(monitor.last_processed_time) > 0
        
        print("\nMonitor State:")
        print(f"Is running: {monitor.is_running}")
        print(f"Last processed times: {monitor.last_processed_time}")
        print(f"Wallet statuses: {monitor.wallet_manager.wallet_tiers}")
        
    finally:
        # Stop the monitor
        monitor.is_running = False
        await monitor_task 