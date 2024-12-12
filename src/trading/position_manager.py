"""
Position management and risk rules
"""
import logging
from typing import Dict, Optional, Set
from datetime import datetime, timezone
from dataclasses import dataclass, field

from ..config import (
    SCORE_THRESHOLDS, POSITION_SIZES,
    MAX_POSITIONS, MAX_AI_POSITIONS, MAX_MEME_POSITIONS,
    PROFIT_LEVELS
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

class PositionManager:
    """Manages trading positions and risk"""
    def __init__(self):
        self.logger = logging.getLogger('position_manager')
        self.positions: Dict[str, Position] = {}
        
    def can_open_position(self, category: str) -> bool:
        """Check if we can open a new position"""
        # Check total position limit
        if len(self.positions) >= MAX_POSITIONS:
            self.logger.info(f"At max positions: {len(self.positions)}/{MAX_POSITIONS}")
            return False
            
        # Count positions by category
        if category == "MEME":
            category_positions = len([
                p for p in self.positions.values()
                if p.category == "MEME" and p.status == "ACTIVE"
            ])
            if category_positions >= MAX_MEME_POSITIONS:
                self.logger.info(f"At max MEME positions: {category_positions}/{MAX_MEME_POSITIONS}")
                return False
        else:  # AI or HYBRID (treated as AI)
            ai_positions = len([
                p for p in self.positions.values()
                if (p.category in ["AI", "HYBRID"]) and p.status == "ACTIVE"
            ])
            if ai_positions >= MAX_AI_POSITIONS:
                self.logger.info(f"At max AI positions: {ai_positions}/{MAX_AI_POSITIONS}")
                return False
                
        return True
        
    def calculate_position_size(self, category: str) -> float:
        """Calculate position size based on category"""
        if not self.can_open_position(category):
            return 0.0
            
        return POSITION_SIZES[category]
        
    def set_take_profits(self, entry_price: float) -> list[float]:
        """Set take profit levels based on config"""
        return [
            entry_price * (1 + level['increase'])
            for level in PROFIT_LEVELS
        ]
        
    def open_position(
        self,
        token_address: str,
        symbol: str,
        category: str,
        entry_price: float,
        tokens: float  # Number of tokens
    ) -> Optional[Position]:
        """Open a new position"""
        try:
            # Verify we can open position
            if not self.can_open_position(category):
                return None
                
            # Create position - removed rounding to keep full precision
            position = Position(
                token_address=token_address,
                symbol=symbol,
                category=category,
                entry_price=entry_price,  # Keep full precision
                tokens=tokens,  # Keep full precision
                entry_time=datetime.now(timezone.utc),
                take_profits=self.set_take_profits(entry_price)
            )
            
            # Store position
            self.positions[token_address] = position
            
            self.logger.info(
                f"Opened {category} position in {symbol} "
                f"at {position.entry_price:.10f} SOL with {position.tokens:.2f} tokens"
            )
            
            return position
            
        except Exception as e:
            self.logger.error(f"Error opening position: {e}")
            return None
            
    def update_position(
        self,
        token_address: str,
        current_price: float
    ) -> Optional[Position]:
        """Update position with current price"""
        try:
            position = self.positions.get(token_address)
            if not position:
                return None
                
            # Update price and unrealized PNL - removed rounding
            position.current_price = current_price
            position.ur_pnl = position.tokens * (current_price - position.entry_price)
            
            return position
            
        except Exception as e:
            self.logger.error(f"Error updating position: {e}")
            return None
            
    def update_realized_pnl(
        self,
        token_address: str,
        tokens_sold: float,
        sell_price: float
    ) -> None:
        """Update realized PNL after selling tokens"""
        position = self.positions.get(token_address)
        if not position:
            return
            
        # Calculate PNL for sold tokens - removed rounding
        pnl = tokens_sold * (sell_price - position.entry_price)
        position.r_pnl += pnl
        
        # Update remaining tokens
        position.tokens -= tokens_sold
            
    def check_take_profits(self, position: Position) -> bool:
        """Check if position hit take profit"""
        if not position.current_price or not position.take_profits:
            return False
            
        # Check each take profit level
        for i, level in enumerate(PROFIT_LEVELS):
            target_price = position.entry_price * (1 + level['increase'])
            if position.current_price >= target_price and i not in position.profit_levels_hit:
                self.logger.info(
                    f"Take profit hit for {position.symbol} "
                    f"at {position.current_price:.10f} SOL"
                )
                return True
                
        return False
        
    def close_position(self, token_address: str) -> Optional[Position]:
        """Close an open position"""
        try:
            position = self.positions.get(token_address)
            if not position:
                return None
                
            # Mark position as closed
            position.status = "CLOSED"
            
            self.logger.info(
                f"Closed position in {position.symbol} "
                f"with total PNL: {position.total_pnl:.10f} SOL "
                f"(r: {position.r_pnl:.10f}, ur: {position.ur_pnl:.10f})"
            )
            
            return position
            
        except Exception as e:
            self.logger.error(f"Error closing position: {e}")
            return None
            
    def get_active_positions(self) -> list[Position]:
        """Get all active positions"""
        return [
            p for p in self.positions.values()
            if p.status == "ACTIVE"
        ]
        
    def get_position_summary(self) -> dict:
        """Get position summary stats"""
        active = self.get_active_positions()
        
        # Calculate PNL values without rounding
        total_pnl = sum(p.total_pnl for p in self.positions.values())
        realized_pnl = sum(p.r_pnl for p in self.positions.values())
        unrealized_pnl = sum(p.ur_pnl for p in self.positions.values())
        
        # Count AI/HYBRID positions together
        ai_positions = len([p for p in active if p.category in ["AI", "HYBRID"]])
        meme_positions = len([p for p in active if p.category == "MEME"])
        
        return {
            "total_positions": len(self.positions),
            "active_positions": len(active),
            "total_pnl": total_pnl,
            "realized_pnl": realized_pnl,
            "unrealized_pnl": unrealized_pnl,
            "by_category": {
                "AI": ai_positions,  # Includes both AI and HYBRID
                "MEME": meme_positions
            }
        }
