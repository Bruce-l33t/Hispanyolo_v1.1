"""
Core models for Pirate3
"""
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Dict, List, Set, Optional
from enum import Enum
from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, Enum as SQLEnum
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

Base = declarative_base()

class WalletStatus(str, Enum):
    """Wallet activity status"""
    VERY_ACTIVE = "VERY_ACTIVE"
    ACTIVE = "ACTIVE"
    WATCHING = "WATCHING"
    ASLEEP = "ASLEEP"

# SQLAlchemy Position Model for persistence
class DBPosition(Base):
    """Database model for positions"""
    __tablename__ = 'positions'
    
    id = Column(Integer, primary_key=True)
    token_address = Column(String, unique=True, index=True)
    symbol = Column(String)
    category = Column(String)
    entry_price = Column(Float)
    tokens = Column(Float)
    entry_time = Column(DateTime)
    current_price = Column(Float, nullable=True)
    r_pnl = Column(Float, default=0.0)
    ur_pnl = Column(Float, default=0.0)
    status = Column(String, default="ACTIVE")
    take_profits = Column(String)  # Stored as JSON string
    profit_levels_hit = Column(String)  # Stored as JSON string
    
    def to_position(self) -> 'Position':
        """Convert DB model to Position dataclass"""
        import json
        return Position(
            token_address=self.token_address,
            symbol=self.symbol,
            category=self.category,
            entry_price=self.entry_price,
            tokens=self.tokens,
            entry_time=self.entry_time,
            take_profits=json.loads(self.take_profits),
            current_price=self.current_price,
            r_pnl=self.r_pnl,
            ur_pnl=self.ur_pnl,
            status=self.status,
            profit_levels_hit=set(json.loads(self.profit_levels_hit))
        )

@dataclass
class Position:
    """Trading position data"""
    token_address: str
    symbol: str
    category: str
    entry_price: float  # SOL per token
    tokens: float  # Number of tokens
    entry_time: datetime
    take_profits: list[float]
    current_price: Optional[float] = None
    r_pnl: float = 0.0  # Realized PNL in SOL
    ur_pnl: float = 0.0  # Unrealized PNL in SOL
    status: str = "ACTIVE"
    profit_levels_hit: Set[int] = field(default_factory=set)  # Track which levels hit

    @property
    def total_pnl(self) -> float:
        """Total PNL (realized + unrealized)"""
        return self.r_pnl + self.ur_pnl
        
    def to_db_model(self) -> DBPosition:
        """Convert to database model"""
        import json
        return DBPosition(
            token_address=self.token_address,
            symbol=self.symbol,
            category=self.category,
            entry_price=self.entry_price,
            tokens=self.tokens,
            entry_time=self.entry_time,
            current_price=self.current_price,
            r_pnl=self.r_pnl,
            ur_pnl=self.ur_pnl,
            status=self.status,
            take_profits=json.dumps(self.take_profits),
            profit_levels_hit=json.dumps(list(self.profit_levels_hit))
        )

# Initialize database
engine = create_engine('sqlite:///positions.db')
Base.metadata.create_all(engine)
Session = sessionmaker(bind=engine)

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
class WalletTier:
    """Wallet tracking"""
    status: WalletStatus = WalletStatus.WATCHING
    last_active: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    transaction_count: int = 0
    score: float = 0.0
