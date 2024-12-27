#!/usr/bin/env python3
"""
Whale Hunter Trading System
Entry point script that runs the system
"""

import asyncio
import logging
import csv
from datetime import datetime
from typing import Dict, Any
from pathlib import Path
from .monitor import WhaleMonitor
from .trading import TradingSystem
from .models import WalletStatus, WalletTier

async def load_wallet_scores(monitor: WhaleMonitor):
    """Load wallet scores from CSV"""
    csv_path = Path(__file__).parent.parent / 'crystalized_wallets.csv'
    if not csv_path.exists():
        raise FileNotFoundError(f"Wallet data not found: {csv_path}")
        
    # Load all scores first
    wallet_data = []
    with open(csv_path, 'r') as f:
        reader = csv.DictReader(f)
        for row in reader:
            wallet_url = row.get('Wallet', '')
            if wallet_url:
                wallet = wallet_url.split('/')[-1].strip()
                score = float(row.get('score', 0))
                if wallet:
                    wallet_data.append((wallet, score))
    
    # Sort by score (highest first)
    wallet_data.sort(key=lambda x: x[1], reverse=True)
    
    # Initialize wallets
    for wallet, score in wallet_data:
        monitor.wallet_manager.wallet_scores[wallet] = score
        # All wallets start as WATCHING
        monitor.wallet_manager.wallet_tiers[wallet] = WalletTier(
            status=WalletStatus.WATCHING,
            score=score
        )

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
        
        # Load wallet data
        logger.info("Loading wallet data...")
        await load_wallet_scores(monitor)
        logger.info(f"Loaded {len(monitor.wallet_manager.wallet_scores)} wallet scores")
        
        # Start the monitor and trading system
        monitor_task = asyncio.create_task(monitor.run())
        trading_task = asyncio.create_task(trading.run())
        logger.info("Monitor and Trading System started")
        
        while True:
            try:
                # Get wallet status counts
                status_counts = monitor.wallet_manager.get_status_counts()
                
                # Log system status
                logger.info(
                    f"System Status - "
                    f"Wallets: {monitor.wallet_manager.wallets_checked}, "
                    f"Transactions: {len(monitor.token_metrics.token_metrics)}, "
                    f"Status Counts: {status_counts}"
                )
                
                # Short delay between updates
                await asyncio.sleep(5)
                
            except Exception as e:
                logger.error(f"Error in main loop: {e}")
                await asyncio.sleep(5)
                
    except KeyboardInterrupt:
        logger.info("Shutting down gracefully...")
        monitor_task.cancel()
        trading_task.cancel()
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        raise

if __name__ == "__main__":
    asyncio.run(main())
