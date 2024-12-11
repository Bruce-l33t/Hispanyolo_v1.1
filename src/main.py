#!/usr/bin/env python3
"""
Whale Hunter Trading System
Entry point script that runs the system
"""

import asyncio
import logging
import csv
import json
from datetime import datetime
from typing import Dict, Any
from pathlib import Path
from .monitor import WhaleMonitor
from .trading import TradingSystem
from .ui_client import UIClient
from .models import WalletStatus, WalletTier
from .events import event_bell

async def load_wallet_scores(monitor: WhaleMonitor):
    """Load wallet scores from CSV"""
    csv_path = Path(__file__).parent.parent / 'crystalized_wallets.csv'
    if not csv_path.exists():
        raise FileNotFoundError(f"Wallet data not found: {csv_path}")
        
    with open(csv_path, 'r') as f:
        reader = csv.DictReader(f)
        for row in reader:
            # Extract wallet address from the URL
            wallet_url = row.get('Wallet', '')
            if wallet_url:
                wallet = wallet_url.split('/')[-1].strip()
                score = float(row.get('score', 0))
                if wallet:
                    monitor.wallet_manager.wallet_scores[wallet] = score
                    # Initialize wallet status based on score
                    if score >= 75:
                        status = WalletStatus.VERY_ACTIVE
                    elif score >= 50:
                        status = WalletStatus.ACTIVE
                    elif score >= 25:
                        status = WalletStatus.WATCHING
                    else:
                        status = WalletStatus.ASLEEP
                    # Create WalletTier object
                    monitor.wallet_manager.wallet_tiers[wallet] = WalletTier(
                        status=status,
                        score=score
                    )

async def handle_token_metrics(data: Dict[str, Any], ui: UIClient):
    """Handle token metrics update event"""
    if 'token_metrics' in data:
        logger = logging.getLogger('main')
        logger.info(f"Token metrics data: {json.dumps(data['token_metrics'], indent=2)}")
        await ui.update_token_metrics(data['token_metrics'])

async def handle_position_update(data: Dict[str, Any], ui: UIClient):
    """Handle position updates from trading system"""
    if 'active_positions' in data:
        logger = logging.getLogger('main')
        logger.info(f"Position update data: {json.dumps(data['active_positions'], indent=2)}")
        await ui.update_positions(data['active_positions'])

async def main():
    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    logger = logging.getLogger('main')
    
    try:
        # Initialize components
        logger.info("Starting Whale Hunter Trading System...")
        monitor = WhaleMonitor()
        trading = TradingSystem()
        ui = UIClient()
        
        # Load wallet data
        logger.info("Loading wallet data...")
        await load_wallet_scores(monitor)
        logger.info(f"Loaded {len(monitor.wallet_manager.wallet_scores)} wallet scores")
        
        # Connect to UI
        await ui.connect()
        
        # Subscribe to events
        await event_bell.subscribe(
            'position_update',
            lambda data: handle_position_update(data, ui)
        )
        await event_bell.subscribe(
            'token_metrics',
            lambda data: handle_token_metrics(data, ui)
        )
        
        # Start the monitor and trading system
        monitor_task = asyncio.create_task(monitor.run())
        trading_task = asyncio.create_task(trading.run())
        logger.info("Monitor and Trading System started")
        
        # Track reconnection attempts
        reconnect_delay = 1
        max_reconnect_delay = 30
        
        while True:
            try:
                if not ui.connected:
                    logger.info("Reconnecting to UI...")
                    await ui.connect()
                    reconnect_delay = 1  # Reset delay on successful connection
                
                # Get wallet status counts and convert enum keys to strings
                status_counts = monitor.wallet_manager.get_status_counts()
                status_data = {
                    status.value: count  # Use enum's string value as key
                    for status, count in status_counts.items()
                }
                
                # Update system status
                await ui.update_system_status(
                    wallet_status=status_data,
                    wallets_checked=monitor.wallet_manager.wallets_checked,
                    transactions_processed=len(monitor.token_metrics.token_metrics)
                )
                
                # Get recent transactions from token metrics
                for addr, metrics in monitor.token_metrics.token_metrics.items():
                    if metrics.recent_changes:
                        recent_change = metrics.recent_changes[0]  # Get most recent change
                        await ui.add_transaction(
                            symbol=metrics.symbol or addr[:8],  # Use symbol or address prefix
                            amount=abs(recent_change.get('amount', 0)),
                            tx_type=recent_change.get('type', 'unknown')
                        )
                
                # Short delay between updates
                await asyncio.sleep(1)
                
            except Exception as e:
                logger.error(f"Error in main loop: {e}")
                
                # Exponential backoff for reconnection
                if not ui.connected:
                    await asyncio.sleep(reconnect_delay)
                    reconnect_delay = min(reconnect_delay * 2, max_reconnect_delay)
                else:
                    await asyncio.sleep(5)  # Regular error delay
                
    except KeyboardInterrupt:
        logger.info("Shutting down gracefully...")
        monitor_task.cancel()
        trading_task.cancel()
        await ui.close()
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        raise

if __name__ == "__main__":
    asyncio.run(main())
