"""
Wallet management and status tracking
"""
from datetime import datetime, timezone, timedelta
import logging
from typing import Dict, List, Optional

from ..models import WalletStatus, WalletTier

# Status timing thresholds
STATUS_THRESHOLDS = {
    WalletStatus.VERY_ACTIVE: timedelta(hours=1),    # 1 hour
    WalletStatus.ACTIVE: timedelta(hours=2),         # 2 hours
    WalletStatus.WATCHING: timedelta(hours=12),      # 12 hours
    WalletStatus.ASLEEP: timedelta(days=5),          # 5 days
    WalletStatus.DORMANT: timedelta(days=999)        # Effectively infinite
}

# Base check intervals
BASE_CHECK_INTERVALS = {
    WalletStatus.VERY_ACTIVE: 30 * 60,          # Every 30 mins
    WalletStatus.ACTIVE: 60 * 60,               # Every 1 hour
    WalletStatus.WATCHING: 4 * 60 * 60,         # Every 4 hours
    WalletStatus.ASLEEP: 8 * 60 * 60,          # Every 8 hours
    WalletStatus.DORMANT: 24 * 60 * 60         # Every 24 hours
}

class WalletManager:
    """Manages wallet tracking and status"""
    
    def __init__(self):
        """Initialize wallet manager"""
        self.logger = logging.getLogger('wallet_manager')
        self.wallet_scores: Dict[str, float] = {}
        self.wallet_tiers: Dict[str, WalletTier] = {}
        self.wallets_checked = 0
        self.last_check_time: Dict[str, datetime] = {}
        
    def load_wallet_scores(self):
        """Load wallet scores from file"""
        # TODO: Implement score loading
        pass
        
    def get_wallet_score(self, wallet_address: str) -> float:
        """Get wallet score, ensuring non-negative"""
        score = self.wallet_scores.get(wallet_address, 0)
        return max(0, score)  # Ensure non-negative
        
    def get_check_interval(self, wallet_address: str) -> int:
        """Get check interval in seconds based on status and score"""
        if wallet_address not in self.wallet_tiers:
            return BASE_CHECK_INTERVALS[WalletStatus.WATCHING]
            
        status = self.wallet_tiers[wallet_address].status
        score = self.get_wallet_score(wallet_address)
        base_interval = BASE_CHECK_INTERVALS[status]
        
        # Adjust interval based on score
        if score >= 75:
            return int(base_interval * 0.75)  # 25% faster for high scores
        elif score < 50:
            return int(base_interval * 1.25)  # 25% slower for low scores
        return base_interval
        
    def should_check_wallet(self, wallet_address: str) -> bool:
        """Determine if wallet should be checked based on last check time"""
        if wallet_address not in self.last_check_time:
            return True
            
        now = datetime.now(timezone.utc)
        last_check = self.last_check_time[wallet_address]
        interval = self.get_check_interval(wallet_address)
        
        return (now - last_check).total_seconds() >= interval
        
    async def update_wallet_activity(
        self,
        wallet_address: str,
        activity_time: Optional[datetime]
    ):
        """Update wallet activity status"""
        if not wallet_address or activity_time is None:
            return
            
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
        
        # Find appropriate status based on time difference
        new_status = WalletStatus.DORMANT
        for status, threshold in STATUS_THRESHOLDS.items():
            if time_diff <= threshold:
                new_status = status
                break
                
        if new_status != wallet.status:
            self.logger.info(
                f"Wallet {wallet_address[:8]} status changed: "
                f"{wallet.status.value} -> {new_status.value}"
            )
            wallet.status = new_status
            
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
