"""
Position management and risk rules
"""
import logging
import json
from typing import Dict, Optional, Set, List
from datetime import datetime, timezone
from dataclasses import dataclass, field

from ..models import Position, Session, DBPosition
from ..config import (
    SCORE_THRESHOLDS, POSITION_SIZES,
    MAX_POSITIONS, MAX_AI_POSITIONS, MAX_MEME_POSITIONS,
    PROFIT_LEVELS
)

class PositionManager:
    """Manages trading positions and risk"""
    def __init__(self):
        self.logger = logging.getLogger('position_manager')
        self._load_positions()
        
    def _load_positions(self):
        """Load positions from database"""
        self.positions: Dict[str, Position] = {}
        session = Session()
        try:
            db_positions = session.query(DBPosition).all()
            for db_pos in db_positions:
                self.positions[db_pos.token_address] = db_pos.to_position()
        finally:
            session.close()
            
    def _save_position(self, position: Position):
        """Save position to database"""
        session = Session()
        try:
            db_position = position.to_db_model()
            existing = session.query(DBPosition).filter_by(
                token_address=position.token_address
            ).first()
            
            if existing:
                # Update existing
                for key, value in db_position.__dict__.items():
                    if key != '_sa_instance_state':
                        setattr(existing, key, value)
            else:
                # Add new
                session.add(db_position)
                
            session.commit()
        except Exception as e:
            self.logger.error(f"Error saving position: {e}")
            session.rollback()
            raise
        finally:
            session.close()
            
    def can_open_position(self, category: str) -> bool:
        """Track position counts without enforcing limits"""
        active_positions = [p for p in self.positions.values() if p.status == "ACTIVE"]
        
        # Log total positions (no limit enforced)
        self.logger.info(f"Current total positions: {len(active_positions)}")
            
        # Count and log positions by category (no limits enforced)
        if category == "MEME":
            category_positions = len([
                p for p in active_positions
                if p.category == "MEME"
            ])
            self.logger.info(f"Current MEME positions: {category_positions}")
        else:  # AI or HYBRID (treated as AI)
            ai_positions = len([
                p for p in active_positions
                if p.category in ["AI", "HYBRID"]
            ])
            self.logger.info(f"Current AI/HYBRID positions: {ai_positions}")
                
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
        tokens: float
    ) -> Optional[Position]:
        """Open a new position"""
        try:
            # Verify we can open position
            if not self.can_open_position(category):
                return None
                
            # Create position
            position = Position(
                token_address=token_address,
                symbol=symbol,
                category=category,
                entry_price=entry_price,
                tokens=tokens,
                entry_time=datetime.now(timezone.utc),
                take_profits=self.set_take_profits(entry_price)
            )
            
            # Store position
            self.positions[token_address] = position
            self._save_position(position)
            
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
                
            # Update price and unrealized PNL
            position.current_price = current_price
            position.ur_pnl = position.tokens * (current_price - position.entry_price)
            
            # Save updates
            self._save_position(position)
            
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
            
        # Calculate PNL for sold tokens
        pnl = tokens_sold * (sell_price - position.entry_price)
        position.r_pnl += pnl
        
        # Update remaining tokens
        position.tokens -= tokens_sold
        
        # Save updates
        self._save_position(position)
            
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
                position.profit_levels_hit.add(i)
                self._save_position(position)
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
            self._save_position(position)
            
            self.logger.info(
                f"Closed position in {position.symbol} "
                f"with total PNL: {position.total_pnl:.10f} SOL "
                f"(r: {position.r_pnl:.10f}, ur: {position.ur_pnl:.10f})"
            )
            
            return position
            
        except Exception as e:
            self.logger.error(f"Error closing position: {e}")
            return None
            
    def get_active_positions(self) -> List[Position]:
        """Get all active positions"""
        return [
            p for p in self.positions.values()
            if p.status == "ACTIVE"
        ]
        
    def get_position_summary(self) -> dict:
        """Get position summary stats"""
        active = self.get_active_positions()
        
        # Calculate PNL values
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
