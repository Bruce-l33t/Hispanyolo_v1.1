import sys
import os
import asyncio
import logging
from datetime import datetime, timezone
from pathlib import Path

# Add the project root to the Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.models import Position
from src.trading.trading_system import TradingSystem

async def test_take_profit():
    # Set up logging
    logging.basicConfig(level=logging.DEBUG)
    logger = logging.getLogger('test')
    
    logger.info("Initializing trading system...")
    # Initialize trading system
    trading_system = TradingSystem()
    
    logger.info("Creating test position...")
    # Create test position for FLhNk1NJ with full token address
    test_position = Position(
        token_address="FLhNk1NJVkngyJf7Stne2nRa3BvCw5Lm7pncsuMHpump",  # Full token address
        symbol="FLhNk1NJ",
        category="MEME",
        entry_price=1.0,  # Base price
        tokens=100.0,  # Number of tokens
        entry_time=datetime.now(timezone.utc),
        take_profits=[1.6, 2.0, 2.4],  # Take profits at 60%, 100%, 140%
        current_price=1.92,  # 92% up from entry
        r_pnl=0.0,
        ur_pnl=92.0,
        status="ACTIVE"
    )
    
    logger.info("Adding position to trading system...")
    # Add position to trading system
    trading_system.position_manager.positions[test_position.token_address] = test_position
    
    # Calculate tokens to sell (25% of current position)
    tokens_to_sell = test_position.tokens * 0.25  # Sell 25% of position
    
    logger.info(f"Attempting to execute take profit, selling {tokens_to_sell} tokens at price {test_position.current_price}...")
    # Try to execute take profit
    result = await trading_system.execute_take_profit(
        token_address=test_position.token_address,
        tokens_to_sell=tokens_to_sell,  # Sell 25% of position
        target_price=test_position.current_price
    )
    logger.info(f"Take profit execution result: {result}")

if __name__ == "__main__":
    # Set up logging
    logging.basicConfig(level=logging.DEBUG)
    
    # Run the test
    asyncio.run(test_take_profit()) 