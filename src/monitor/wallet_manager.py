"""
Wallet management and status tracking
"""
from datetime import datetime, timezone, timedelta
import logging
from typing import Dict, List, Optional

from ..models import WalletStatus, WalletTier

class WalletManager:
    """Manages wallet tracking and status"""
    
    def __init__(self):
        """Initialize wallet manager"""
        self.logger = logging.getLogger('wallet_manager')
        self.wallet_scores: Dict[str, float] = {}
        self.wallet_tiers: Dict[str, WalletTier] = {}
        self.wallets_checked = 0
        
    def load_wallet_scores(self):
        """Load wallet scores from file"""
        # TODO: Implement score loading
        pass
        
    def get_wallet_score(self, wallet_address: str) -> float:
        """Get wallet score, ensuring non-negative"""
        score = self.wallet_scores.get(wallet_address, 0)
        return max(0, score)  # Ensure non-negative
        
    async def update_wallet_activity(
        self,
        wallet_address: str,
        activity_time: Optional[datetime]
    ):
        """Update wallet activity status"""
        if not wallet_address:  # Empty wallet address
            return
            
        if activity_time is None:  # Invalid timestamp
            raise AttributeError("Invalid timestamp")
            
        if wallet_address not in self.wallet_tiers:
            self.wallet_tiers[wallet_address] = WalletTier(
                status=WalletStatus.WATCHING,
                last_active=activity_time,
                transaction_count=0,
                score=self.get_wallet_score(wallet_address)
            )
            
        wallet = self.wallet_tiers[wallet_address]
        wallet.transaction_count += 1
        
        # Update status based on activity time
        time_diff = datetime.now(timezone.utc) - activity_time
        
        if time_diff <= timedelta(minutes=15):
            if wallet.status != WalletStatus.VERY_ACTIVE:
                self.logger.info(
                    f"Wallet {wallet_address[:8]} status changed: "
                    f"{wallet.status.value} -> {WalletStatus.VERY_ACTIVE.value}"
                )
                wallet.status = WalletStatus.VERY_ACTIVE
        elif time_diff <= timedelta(hours=1):
            if wallet.status != WalletStatus.ACTIVE:
                self.logger.info(
                    f"Wallet {wallet_address[:8]} status changed: "
                    f"{wallet.status.value} -> {WalletStatus.ACTIVE.value}"
                )
                wallet.status = WalletStatus.ACTIVE
        elif time_diff <= timedelta(hours=4):
            if wallet.status != WalletStatus.WATCHING:
                self.logger.info(
                    f"Wallet {wallet_address[:8]} status changed: "
                    f"{wallet.status.value} -> {WalletStatus.WATCHING.value}"
                )
                wallet.status = WalletStatus.WATCHING
        else:
            if wallet.status != WalletStatus.ASLEEP:
                self.logger.info(
                    f"Wallet {wallet_address[:8]} status changed: "
                    f"{wallet.status.value} -> {WalletStatus.ASLEEP.value}"
                )
                wallet.status = WalletStatus.ASLEEP
                
        wallet.last_active = activity_time
        
    async def mark_wallet_checked(self, wallet_address: str):
        """Mark wallet as checked"""
        self.wallets_checked += 1
        
    def get_wallets_to_check(self) -> List[str]:
        """Get list of wallets to check"""
        active_wallets = [
            addr for addr, tier in self.wallet_tiers.items()
            if tier.status in [WalletStatus.VERY_ACTIVE, WalletStatus.ACTIVE]
        ]
        return active_wallets
        
    async def update_wallet_statuses(self):
        """Update wallet statuses based on activity time"""
        now = datetime.now(timezone.utc)
        
        for address, tier in self.wallet_tiers.items():
            time_diff = now - tier.last_active
            
            # Update status based on inactivity time
            if time_diff > timedelta(hours=4):
                if tier.status != WalletStatus.ASLEEP:
                    self.logger.info(
                        f"Wallet {address[:8]} status updated to ASLEEP "
                        f"(inactive for {time_diff.total_seconds() / 3600:.1f} hours)"
                    )
                    tier.status = WalletStatus.ASLEEP
            elif time_diff > timedelta(hours=1):
                if tier.status != WalletStatus.WATCHING:
                    self.logger.info(
                        f"Wallet {address[:8]} status updated to WATCHING "
                        f"(inactive for {time_diff.total_seconds() / 3600:.1f} hours)"
                    )
                    tier.status = WalletStatus.WATCHING
            elif time_diff > timedelta(minutes=15):
                if tier.status != WalletStatus.ACTIVE:
                    self.logger.info(
                        f"Wallet {address[:8]} status updated to ACTIVE "
                        f"(inactive for {time_diff.total_seconds() / 60:.1f} minutes)"
                    )
                    tier.status = WalletStatus.ACTIVE
            
    def get_status_counts(self) -> Dict[WalletStatus, int]:
        """Get counts of wallets in each status"""
        counts = {status: 0 for status in WalletStatus}
        for tier in self.wallet_tiers.values():
            counts[tier.status] += 1
        return counts
