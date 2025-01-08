"""
Core monitoring system
Combines wallet tracking, token metrics, and transaction processing
"""
import asyncio
import logging
from datetime import datetime, timezone, timedelta
import json
from typing import Dict, List, Optional
import requests
import random

from ..config import (
    WSOL_ADDRESS, USDC_ADDRESS, IGNORED_TOKENS,
    MIN_SOL_AMOUNT, BIRDEYE_SETTINGS
)
from ..models import WalletStatus
from .wallet_manager import WalletManager
from .token_metrics import TokenMetricsManager
import dontshare as d

class WhaleMonitor:
    """Core whale monitoring system"""
    def __init__(self):
        self.logger = logging.getLogger('whale_monitor')
        self.wallet_manager = WalletManager()
        self.token_metrics = TokenMetricsManager()
        self.start_time = datetime.now(timezone.utc)
        self.batch_size = 10  # Process wallets in batches of 10
        self.monitoring_tasks = []  # Track running tasks
        self.is_running = False
        self.last_processed_time: Dict[str, datetime] = {}  # Track last processed time per wallet
        self.last_api_call = datetime.now()  # Track last API call for rate limiting
        
        self.logger.info("Initializing WhaleMonitor...")
        
    def _get_start_time(self, wallet: str, initial_scan: bool) -> datetime:
        """Get appropriate start time for transaction fetching"""
        now = datetime.now(timezone.utc)
        
        if initial_scan:
            # For initial scan, look back 15 minutes
            start_time = now - timedelta(minutes=15)
            self.logger.info(f"Initial scan for {wallet[:8]}, looking back 15 minutes")
        elif wallet not in self.last_processed_time:
            # For new wallets, look back 15 minutes
            start_time = now - timedelta(minutes=15)
            self.logger.info(f"New wallet {wallet[:8]}, looking back 15 minutes")
        else:
            # For regular scans, look back to last processed time
            start_time = self.last_processed_time[wallet]
            self.logger.info(
                f"Regular scan for {wallet[:8]}, looking back to "
                f"{start_time.isoformat()}"
            )
            
        return start_time
        
    async def get_wallet_transactions(
        self, 
        wallet: str, 
        initial_scan: bool = False
    ) -> Optional[dict]:
        """Get wallet transactions with retry logic"""
        max_retries = 3
        retry_delay = 2  # seconds
        start_time = self._get_start_time(wallet, initial_scan)
        
        for attempt in range(max_retries):
            try:
                # Add small delay between API calls to prevent rate limiting
                since_last_call = (datetime.now() - self.last_api_call).total_seconds()
                if since_last_call < 0.1:  # 100ms minimum delay between calls
                    await asyncio.sleep(0.1 - since_last_call)
                
                url = f"{BIRDEYE_SETTINGS['base_url']}{BIRDEYE_SETTINGS['endpoints']['tx_list']}"
                params = {
                    "wallet": wallet,
                    "limit": 100
                }
                headers = {
                    **BIRDEYE_SETTINGS['headers'],
                    "X-API-KEY": d.birdeye_api_key
                }
                
                self.last_api_call = datetime.now()
                self.logger.debug(f"Fetching transactions for {wallet[:8]}")
                response = requests.get(url, params=params, headers=headers)
                response.raise_for_status()
                data = response.json()
                
                # Filter transactions by time
                filtered_txs = []
                if 'data' in data and 'solana' in data['data']:
                    for tx in data['data']['solana']:
                        tx_time = datetime.fromisoformat(
                            tx['blockTime'].replace('Z', '+00:00')
                        )
                        if tx_time > start_time:
                            filtered_txs.append(tx)
                    
                    data['data']['solana'] = filtered_txs
                    
                    if filtered_txs:
                        self.logger.info(
                            f"Found {len(filtered_txs)} new transactions "
                            f"for {wallet[:8]}"
                        )
                    else:
                        self.logger.debug(f"No new transactions for {wallet[:8]}")
                
                return data
                
            except Exception as e:
                if attempt == max_retries - 1:  # Last attempt
                    self.logger.error(f"API Error for {wallet[:8]}: {str(e)}")
                    return None
                else:
                    self.logger.warning(f"Retry {attempt + 1}/{max_retries} for {wallet[:8]}")
                    await asyncio.sleep(retry_delay * (attempt + 1))
                    continue

    def _is_real_swap(self, tx: dict) -> bool:
        """Determine if transaction is a real token swap"""
        if 'balanceChange' not in tx:
            return False
            
        sol_change = False
        usdc_change = False
        token_change = False
        
        for change in tx.get('balanceChange', []):
            amount = float(change.get('amount', 0))
            address = change.get('address', '')
            
            if address == WSOL_ADDRESS and amount != 0:
                sol_change = True
            elif address == USDC_ADDRESS and amount != 0:
                usdc_change = True
            elif address not in IGNORED_TOKENS:
                token_change = True
                
        return token_change and (sol_change or usdc_change)

    def _get_sol_amount(self, tx: dict) -> float:
        """Extract SOL amount from transaction"""
        for change in tx.get('balanceChange', []):
            if change.get('address') == WSOL_ADDRESS:
                return abs(float(change.get('amount', 0))) / 10 ** change.get('decimals', 9)
        return 0.0

    async def process_transaction(self, tx: dict, wallet_address: str):
        """Process a single transaction"""
        try:
            tx_time = datetime.fromisoformat(tx['blockTime'].replace('Z', '+00:00'))
            
            # Update wallet activity
            await self.wallet_manager.update_wallet_activity(wallet_address, tx_time)
            wallet_score = self.wallet_manager.get_wallet_score(wallet_address)
            
            # Get SOL amount first
            sol_amount = self._get_sol_amount(tx)
            if sol_amount < MIN_SOL_AMOUNT:
                self.logger.debug(f"Skipping transaction, SOL amount {sol_amount} below minimum")
                return
                
            # Track token changes
            for change in tx.get('balanceChange', []):
                address = change.get('address', '')
                if address not in [WSOL_ADDRESS, USDC_ADDRESS] and address not in IGNORED_TOKENS:
                    amount = float(change.get('amount', 0))
                    symbol = change.get('symbol', '') or address[:8]
                    
                    if amount < 0:  # Token out (sell)
                        self.logger.info(
                            f"Processing sell: {symbol} "
                            f"(Amount: {sol_amount:.4f} SOL)"
                        )
                        await self.token_metrics.process_transaction(
                            token_address=address,
                            symbol=symbol,
                            amount=sol_amount,  # Always use SOL amount
                            tx_type='sell',
                            wallet_address=wallet_address,
                            wallet_score=wallet_score
                        )
                        
                    elif amount > 0:  # Token in (buy)
                        self.logger.info(
                            f"Processing buy: {symbol} "
                            f"(Amount: {sol_amount:.4f} SOL)"
                        )
                        await self.token_metrics.process_transaction(
                            token_address=address,
                            symbol=symbol,
                            amount=sol_amount,  # Always use SOL amount
                            tx_type='buy',
                            wallet_address=wallet_address,
                            wallet_score=wallet_score
                        )

        except Exception as e:
            self.logger.error(f"Error processing transaction: {e}")
            self.logger.error(f"Transaction data: {json.dumps(tx, indent=2)}")

    async def process_wallet(self, wallet: str, initial_scan: bool = False):
        """Process a single wallet's transactions"""
        try:
            now = datetime.now(timezone.utc)
            txs = await self.get_wallet_transactions(wallet, initial_scan)
            
            if txs and 'data' in txs and 'solana' in txs['data']:
                tx_count = len(txs['data']['solana'])
                if tx_count > 0:
                    self.logger.debug(f"Processing {tx_count} transactions for {wallet[:8]}")
                    
                    # Process transactions
                    latest_tx_time = now  # Default to current time
                    for tx in txs['data']['solana']:
                        if self._is_real_swap(tx):
                            await self.process_transaction(tx, wallet)
                            # Update latest transaction time
                            tx_time = datetime.fromisoformat(
                                tx['blockTime'].replace('Z', '+00:00')
                            )
                            latest_tx_time = max(latest_tx_time, tx_time)
                    
                    # Update last processed time to latest transaction time
                    self.last_processed_time[wallet] = latest_tx_time
                    self.logger.debug(
                        f"Updated last processed time for {wallet[:8]} "
                        f"to {latest_tx_time.isoformat()}"
                    )
                else:
                    # No transactions found, update to current time
                    self.last_processed_time[wallet] = now
                    self.logger.debug(
                        f"No transactions for {wallet[:8]}, "
                        f"setting last processed time to {now.isoformat()}"
                    )
                    
            await self.wallet_manager.mark_wallet_checked(wallet)
            
        except Exception as e:
            self.logger.error(f"Error processing wallet {wallet[:8]}: {e}")
            # Even on error, update last processed time to current time
            self.last_processed_time[wallet] = now
            self.logger.debug(
                f"Error processing {wallet[:8]}, "
                f"setting last processed time to {now.isoformat()}"
            )

    async def process_wallet_batch(self, wallets: List[str], initial_scan: bool = False):
        """Process a batch of wallets"""
        tasks = []
        for wallet in wallets:
            # Add small delay between wallet processing to prevent rate limiting
            since_last_call = (datetime.now() - self.last_api_call).total_seconds()
            if since_last_call < 0.1:  # 100ms minimum delay between calls
                await asyncio.sleep(0.1 - since_last_call)
            tasks.append(self.process_wallet(wallet, initial_scan))
            
        await asyncio.gather(*tasks)
        self.logger.info(f"Processed batch of {len(wallets)} wallets")

    def get_wallet_batches(self, wallets: List[str]) -> List[List[str]]:
        """Split wallets into batches for processing"""
        return [wallets[i:i + self.batch_size] for i in range(0, len(wallets), self.batch_size)]

    async def monitor_very_active_wallets(self):
        """Monitor VERY_ACTIVE wallets every 15 minutes"""
        self.logger.info("Starting very active wallet monitoring...")
        while self.is_running:
            try:
                # Get very active wallets
                very_active_wallets = [
                    addr for addr, tier in self.wallet_manager.wallet_tiers.items()
                    if tier.status == WalletStatus.VERY_ACTIVE
                ]
                
                if very_active_wallets:
                    batches = self.get_wallet_batches(very_active_wallets)
                    for batch in batches:
                        await self.process_wallet_batch(batch)
                        await asyncio.sleep(1)  # Small delay between batches
                
                # 15 minute gap for very active wallets
                await asyncio.sleep(900)  # 15 minutes
                
            except Exception as e:
                self.logger.error(f"Error in very active wallet monitoring: {e}")
                await asyncio.sleep(5)  # Brief pause on error

    async def monitor_active_wallets(self):
        """Monitor ACTIVE wallets every 30 minutes"""
        self.logger.info("Starting active wallet monitoring...")
        while self.is_running:
            try:
                # Get active wallets
                active_wallets = [
                    addr for addr, tier in self.wallet_manager.wallet_tiers.items()
                    if tier.status == WalletStatus.ACTIVE
                ]
                
                if active_wallets:
                    batches = self.get_wallet_batches(active_wallets)
                    for batch in batches:
                        await self.process_wallet_batch(batch)
                        await asyncio.sleep(1)  # Small delay between batches
                
                # 10 minute gap for active wallets
                await asyncio.sleep(600)  # 10 minutes
                
            except Exception as e:
                self.logger.error(f"Error in active wallet monitoring: {e}")
                await asyncio.sleep(5)  # Brief pause on error

    async def monitor_watching_wallets(self):
        """Monitor WATCHING wallets every 1 hour"""
        self.logger.info("Starting watching wallet monitoring...")
        while self.is_running:
            try:
                # Get watching wallets
                watching_wallets = [
                    addr for addr, tier in self.wallet_manager.wallet_tiers.items()
                    if tier.status == WalletStatus.WATCHING
                ]
                
                if watching_wallets:
                    batches = self.get_wallet_batches(watching_wallets)
                    for batch in batches:
                        await self.process_wallet_batch(batch)
                        await asyncio.sleep(1)  # Small delay between batches
                
                # 30 minute gap for watching wallets
                await asyncio.sleep(1800)  # 30 minutes
                
            except Exception as e:
                self.logger.error(f"Error in watching wallet monitoring: {e}")
                await asyncio.sleep(60)  # Longer pause on error

    async def monitor_asleep_wallets(self):
        """Monitor ASLEEP wallets"""
        self.logger.info("Starting asleep wallet monitoring...")
        while self.is_running:
            try:
                # Get asleep wallets
                asleep_wallets = [
                    addr for addr, tier in self.wallet_manager.wallet_tiers.items()
                    if tier.status == WalletStatus.ASLEEP
                ]
                
                if asleep_wallets:
                    batches = self.get_wallet_batches(asleep_wallets)
                    for batch in batches:
                        await self.process_wallet_batch(batch)
                        await asyncio.sleep(2)  # Even longer delay between batches
                
                # Check asleep wallets every 4 hours
                await asyncio.sleep(14400)  # 4 hour gap
                
            except Exception as e:
                self.logger.error(f"Error in asleep wallet monitoring: {e}")
                await asyncio.sleep(300)  # 5 minute pause on error

    async def maintenance_task(self):
        """Periodic maintenance operations"""
        self.logger.info("Starting maintenance task...")
        while self.is_running:
            try:
                # Update wallet statuses
                await self.wallet_manager.update_wallet_statuses()
                
                # Cleanup old token data
                self.token_metrics.cleanup_old_tokens()
                
                # Run maintenance every hour
                await asyncio.sleep(3600)
                
            except Exception as e:
                self.logger.error(f"Error in maintenance task: {e}")
                await asyncio.sleep(60)

    async def run(self):
        """Main monitoring loop with separate tasks for each status type"""
        try:
            self.logger.info("Starting WhaleMonitor...")
            self.is_running = True
            
            # Load wallet scores
            self.wallet_manager.load_wallet_scores()
            
            # Get list of wallets to monitor
            wallets_to_monitor = list(self.wallet_manager.wallet_scores.keys())
            
            # Initial scan
            self.logger.info("Starting initial scan...")
            initial_scan_batch = wallets_to_monitor  # Scan all wallets
            
            # Process initial scan in batches
            self.logger.info(f"Scanning {len(initial_scan_batch)} wallets for recent activity...")
            initial_batches = self.get_wallet_batches(initial_scan_batch)
            for batch in initial_batches:
                await self.process_wallet_batch(batch, True)
            self.logger.info("Initial scan complete")
            
            # Start monitoring tasks
            self.monitoring_tasks = [
                asyncio.create_task(self.monitor_very_active_wallets()),
                asyncio.create_task(self.monitor_active_wallets()),
                asyncio.create_task(self.monitor_watching_wallets()),
                asyncio.create_task(self.monitor_asleep_wallets()),
                asyncio.create_task(self.maintenance_task())
            ]
            
            self.logger.info("All monitoring tasks started")
            
            # Wait for tasks to complete (they shouldn't unless there's an error)
            await asyncio.gather(*self.monitoring_tasks)
            
        except Exception as e:
            self.logger.error(f"Error in main loop: {e}")
            raise
            
        finally:
            # Cleanup on exit
            self.is_running = False
            for task in self.monitoring_tasks:
                if not task.done():
                    task.cancel()
            
            # Wait for tasks to finish
            await asyncio.gather(*self.monitoring_tasks, return_exceptions=True)
            self.logger.info("WhaleMonitor shutdown complete")
