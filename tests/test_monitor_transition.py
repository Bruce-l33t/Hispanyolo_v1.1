import asyncio
import pytest
import logging
from datetime import datetime, timezone
from src.monitor.monitor import WhaleMonitor

async def test_monitoring_tasks_directly():
    monitor = WhaleMonitor()
    
    # Add just 2 test wallets
    monitor.wallet_manager.wallet_scores = {
        "wallet1": 100,
        "wallet2": 90
    }
    
    # Simulate completed initial scan
    now = datetime.now(timezone.utc)
    monitor.last_processed_time = {
        "wallet1": now,
        "wallet2": now
    }
    
    # Start monitoring directly
    monitor.is_running = True
    
    # Start just one monitoring task first
    task = asyncio.create_task(monitor.monitor_watching_wallets())
    
    # Check if it's running
    await asyncio.sleep(1)
    print(f"Task done: {task.done()}")
    
    # Stop monitoring
    monitor.is_running = False
    await task 