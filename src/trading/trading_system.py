"""
Main trading system
Coordinates signal processing, position management, and execution
"""
import logging
import asyncio
from typing import Dict, Optional
from datetime import datetime, timezone

from ..events import event_bell
from .signal_processor import SignalProcessor
from .position_manager import PositionManager
from .alchemy import AlchemyTrader
from .price_service import PriceService
from ..config import PROFIT_LEVELS

TAKE_PROFIT_SELL_PORTION = 0.25  # Sell 25% at each level

class TradingSystem:
    """
    Main trading system
    Handles complete flow from signal to execution
    """
    def __init__(self):
        self.logger = logging.getLogger('trading_system')
        self.signal_processor = SignalProcessor()
        self.position_manager = PositionManager()
        self.trader = AlchemyTrader()
        self.price_service = PriceService()
        
    async def handle_signal(self, signal: dict):
        """
        Handle trading signal
        Coordinates between signal processing and position management
        """
        try:
            self.logger.info(f"Processing signal: {signal}")
            
            # 1. Process signal
            trade_params = await self.signal_processor.process_signal(signal)
            if not trade_params:
                self.logger.info("Signal did not qualify for trade")
                return
                
            # 2. Check position limits
            if not self.position_manager.can_open_position(trade_params['category']):
                self.logger.info("Position limits reached")
                return
                
            # 3. Get quote first for price info
            quote = self.trader.get_jupiter_quote(
                token_address=trade_params['token_address'],
                amount_in=trade_params['size'],
                is_sell=False  # This is a buy
            )
            if not quote:
                self.logger.error("Could not get quote")
                return

            # Calculate price directly from quote amounts
            in_amount = float(quote['inAmount']) / 1e9  # Convert lamports to SOL
            out_amount = float(quote['outAmount']) / 1e6  # Convert to actual tokens (6 decimals)
            price = in_amount / out_amount if out_amount > 0 else 0
                
            # 4. Execute trade
            self.logger.info(f"Executing trade: {trade_params}")
            signature = await self.trader.execute_swap(
                token_address=trade_params['token_address'],
                amount_in=trade_params['size'],
                is_sell=False  # This is a buy
            )
            
            if signature:
                self.logger.info(f"Trade executed: {signature}")
                
                if price > 0:
                    self.logger.info(f"Execution price: {price}")
                    
                    # Open position with quote output amount
                    tokens = out_amount
                    position = self.position_manager.open_position(
                        token_address=trade_params['token_address'],
                        symbol=trade_params['symbol'],
                        category=trade_params['category'],
                        entry_price=price,
                        tokens=tokens
                    )
                    
                    if position:
                        # Set initial current price to execution price
                        self.position_manager.update_position(
                            position.token_address,
                            price  # Use execution price as initial current price
                        )
                        
                        # Emit position update
                        await self.emit_position_update()
                else:
                    self.logger.error("Invalid price from quote")
            else:
                self.logger.error("Trade execution failed")
                
        except Exception as e:
            self.logger.error(f"Error handling signal: {e}")
            
    async def execute_take_profit(
        self,
        token_address: str,
        tokens_to_sell: float,
        target_price: float,
        max_retries: int = 10,  # More retries for take profits
        retry_delay: int = 30  # Longer delay between retries
    ) -> bool:
        """Execute take profit with retries"""
        position = self.position_manager.positions.get(token_address)
        if not position:
            return False
            
        profit_pct = ((target_price - position.entry_price) / position.entry_price) * 100
        self.logger.info(
            f"Executing take profit for {position.symbol} "
            f"at {target_price} ({profit_pct:.1f}% up) - "
            f"selling {tokens_to_sell} tokens"
        )
        
        for attempt in range(max_retries):
            # Get quote for the sell
            quote = self.trader.get_jupiter_quote(
                token_address=token_address,
                amount_in=tokens_to_sell,
                is_sell=True  # This is a sell
            )
            if not quote:
                self.logger.error("Could not get sell quote")
                continue

            # Calculate actual sell price from quote
            in_amount = float(quote['inAmount']) / 1e6  # Convert to actual tokens (6 decimals)
            out_amount = float(quote['outAmount']) / 1e9  # Convert lamports to SOL
            actual_price = out_amount / in_amount if in_amount > 0 else 0
            
            if actual_price <= 0:
                self.logger.error("Invalid sell price from quote")
                continue

            # Execute sell with the quoted amount
            signature = await self.trader.execute_swap(
                token_address=token_address,
                amount_in=tokens_to_sell,
                is_sell=True  # This is a sell
            )
            
            if signature:
                # Update realized PNL and remaining tokens using actual execution price
                self.position_manager.update_realized_pnl(
                    token_address=token_address,
                    tokens_sold=tokens_to_sell,
                    sell_price=actual_price
                )
                
                # Update unrealized PNL with current price
                self.position_manager.update_position(
                    token_address=token_address,
                    current_price=actual_price
                )
                
                if position.tokens < 1:  # Close if less than 1 token left
                    self.position_manager.close_position(token_address)
                    self.price_service.remove_from_cache(token_address)
                    self.logger.info(
                        f"Position closed - Total PNL: "
                        f"{position.total_pnl:.2f} SOL "
                        f"(r: {position.r_pnl:.2f}, ur: {position.ur_pnl:.2f})"
                    )
                else:
                    self.logger.info(
                        f"Partial take profit executed - "
                        f"Remaining tokens: {position.tokens}"
                    )
                    
                # Emit position update
                await self.emit_position_update()
                return True
                
            if attempt < max_retries - 1:
                self.logger.warning(
                    f"Take profit attempt {attempt + 1} failed for {position.symbol}, "
                    f"retrying in {retry_delay}s..."
                )
                await asyncio.sleep(retry_delay)
            else:
                self.logger.error(
                    f"Failed to execute take profit for {position.symbol} "
                    f"after {max_retries} attempts"
                )
                
        return False
            
    async def update_positions(self):
        """Update position status"""
        try:
            # Get active positions
            active_positions = self.position_manager.get_active_positions()
            if not active_positions:
                return
                
            # Get current prices
            token_addresses = [p.token_address for p in active_positions]
            prices = await self.price_service.get_prices(token_addresses)
            if not prices:
                self.logger.error("Could not get position prices")
                return
                
            # Update each position
            for position in active_positions:
                price = prices.get(position.token_address)
                if not price:
                    continue
                    
                # Update position price and unrealized PNL
                self.position_manager.update_position(
                    position.token_address,
                    price
                )
                
                # Check take profits
                for i, level in enumerate(PROFIT_LEVELS):
                    target_price = position.entry_price * (1 + level['increase'])
                    if price >= target_price and i not in position.profit_levels_hit:
                        # Sell 25% of current tokens
                        tokens_to_sell = round(position.tokens * TAKE_PROFIT_SELL_PORTION)
                        
                        # Execute take profit
                        if await self.execute_take_profit(
                            token_address=position.token_address,
                            tokens_to_sell=tokens_to_sell,
                            target_price=price
                        ):
                            position.profit_levels_hit.add(i)
                        break  # Only take one profit at a time
                    
        except Exception as e:
            self.logger.error(f"Error updating positions: {e}")
            
    async def emit_position_update(self):
        """Emit position update event"""
        try:
            # Get position summary
            summary = self.position_manager.get_position_summary()
            
            # Add active positions data
            active_positions = []
            for position in self.position_manager.get_active_positions():
                active_positions.append({
                    'token_address': position.token_address,
                    'symbol': position.symbol,
                    'category': position.category,
                    'entry_price': position.entry_price,
                    'current_price': position.current_price,
                    'tokens': position.tokens,
                    'r_pnl': position.r_pnl,
                    'ur_pnl': position.ur_pnl,
                    'total_pnl': position.total_pnl,
                    'entry_time': position.entry_time.isoformat()
                })
                
            # Emit update
            await event_bell.publish('position_update', {
                'summary': summary,
                'active_positions': active_positions,
                'timestamp': datetime.now(timezone.utc).isoformat()
            })
            
        except Exception as e:
            self.logger.error(f"Error emitting position update: {e}")
            
    async def run(self):
        """Main trading loop"""
        self.logger.info("Starting trading system...")
        
        try:
            # Subscribe to trading signals
            await event_bell.subscribe('trading_signal', self.handle_signal)
            self.logger.info("Subscribed to trading signals")
            
            # Main loop
            while True:
                # Update positions
                await self.update_positions()
                
                # Clear old price cache periodically
                self.price_service.clear_cache()
                
                # Sleep between updates
                await asyncio.sleep(60)  # Check positions every minute
                
        except Exception as e:
            self.logger.error(f"Error in trading loop: {e}")
            raise

    async def execute_take_profit(self, position, current_price):
        """Execute take profit based on current price and predefined levels"""
        take_profit_levels = [1.6, 2.4]  # Initial levels: 60%, 120%
        multiplier = 2.0  # 2x multiplier for continuous levels

        # Calculate dynamic take profit levels
        while True:
            last_level = take_profit_levels[-1]
            next_level = last_level * multiplier
            if current_price >= position.entry_price * next_level:
                take_profit_levels.append(next_level)
            else:
                break

        # Execute take profit
        for level in take_profit_levels:
            if current_price >= position.entry_price * level:
                # Sell 25% of the current position
                sell_amount = position.tokens * 0.25
                position.tokens -= sell_amount
                position.r_pnl += sell_amount * (current_price - position.entry_price)
                position.ur_pnl = (position.tokens * (current_price - position.entry_price))
                self.logger.info(f"Take profit executed at {level * 100 - 100}% - Sold {sell_amount} tokens")

                # Emit position update
                await self.emit_position_update()
