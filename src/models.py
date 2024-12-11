"""
Core models for Pirate3
"""
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Dict, List, Set, Optional
from enum import Enum

class WalletStatus(str, Enum):
    """Wallet activity status"""
    VERY_ACTIVE = "VERY_ACTIVE"
    ACTIVE = "ACTIVE"
    WATCHING = "WATCHING"
    ASLEEP = "ASLEEP"

@dataclass
class Transaction:
    """Transaction model"""
    symbol: str
    amount: float
    tx_type: str  # 'buy' or 'sell'
    timestamp: datetime
    token_address: str
    wallet_address: str

    def to_dict(self) -> dict:
        """Convert to dict for UI"""
        return {
            'symbol': self.symbol,
            'amount': self.amount,
            'tx_type': self.tx_type,
            'timestamp': self.timestamp.isoformat(),
            'token_address': self.token_address,
            'wallet_address': self.wallet_address
        }

@dataclass
class TokenMetrics:
    """Token metrics tracking"""
    symbol: str
    token_address: str
    category: str = ""
    confidence: float = 0.0
    score: float = 0.0
    buy_count: int = 0
    sell_count: int = 0
    total_volume: float = 0.0
    unique_buyers: Set[str] = field(default_factory=set)
    recent_changes: List[dict] = field(default_factory=list)
    last_update: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    wallet_contributions: Dict[str, float] = field(default_factory=dict)  # Track each wallet's score

    def add_score(self, wallet_score: float, wallet_address: str, amount: float):
        """Add to token score from a buy"""
        if wallet_address not in self.wallet_contributions:  # Only add if not contributed
            self.wallet_contributions[wallet_address] = wallet_score
            self.score += wallet_score
            self.buy_count += 1
            self.total_volume += amount
            self.unique_buyers.add(wallet_address)
            self.last_update = datetime.now(timezone.utc)
            
            # Track recent change
            self.recent_changes.insert(0, {
                'type': 'buy',
                'amount': amount,
                'time': self.last_update.isoformat()
            })
            self.recent_changes = self.recent_changes[:10]  # Keep last 10

    def reduce_score(self, wallet_score: float, amount: float, wallet_address: str):
        """Reduce token score from a sell"""
        if wallet_address in self.wallet_contributions:  # Remove exact contribution
            self.score -= self.wallet_contributions[wallet_address]
            del self.wallet_contributions[wallet_address]
        
        self.sell_count += 1
        self.total_volume += amount
        self.last_update = datetime.now(timezone.utc)
        
        # Track recent change
        self.recent_changes.insert(0, {
            'type': 'sell',
            'amount': amount,
            'time': self.last_update.isoformat()
        })
        self.recent_changes = self.recent_changes[:10]  # Keep last 10

@dataclass
class Position:
    """Trading position"""
    token_address: str
    symbol: str
    category: str
    entry_price: float
    current_price: float
    size: float
    entry_time: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    realized_profit: float = 0.0
    profit_levels_hit: Set[float] = field(default_factory=set)  # Track hit levels by percentage

    @property
    def profit_percentage(self) -> float:
        """Calculate current profit percentage"""
        if self.entry_price == 0:
            return 0.0
        return ((self.current_price - self.entry_price) / self.entry_price) * 100

    def to_dict(self) -> dict:
        """Convert to dict for UI"""
        return {
            'token_address': self.token_address,
            'symbol': self.symbol,
            'category': self.category,
            'entry_price': self.entry_price,
            'current_price': self.current_price,
            'size': self.size,
            'profit_percentage': self.profit_percentage,
            'entry_time': self.entry_time.isoformat(),
            'realized_profit': self.realized_profit,
            'profit_levels_hit': list(self.profit_levels_hit)
        }

@dataclass
class WalletTier:
    """Wallet tracking"""
    status: WalletStatus = WalletStatus.WATCHING
    last_active: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    transaction_count: int = 0
    score: float = 0.0
