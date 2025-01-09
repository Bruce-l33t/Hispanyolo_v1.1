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
from src.config import PROFIT_LEVELS

async def test_take_profit_portions():
    """Test that take profits use correct sell portions from config"""
    logging.basicConfig(level=logging.DEBUG)
    logger = logging.getLogger('test')
    
    logger.info("Testing take profit portions...")
    
    # Initialize trading system
    trading_system = TradingSystem()
    
    # Create test position with 100 tokens
    test_position = Position(
        token_address="FLhNk1NJVkngyJf7Stne2nRa3BvCw5Lm7pncsuMHpump",
        symbol="TEST",
        category="MEME",
        entry_price=1.0,
        tokens=100.0,
        entry_time=datetime.now(timezone.utc),
        take_profits=[level['increase'] for level in PROFIT_LEVELS],
        current_price=1.0,
        r_pnl=0.0,
        ur_pnl=0.0,
        status="ACTIVE"
    )
    
    # Add position to trading system
    trading_system.position_manager.positions[test_position.token_address] = test_position
    
    # Test first take profit (should sell 50%)
    logger.info("\nTesting first take profit (60% up, should sell 50%)")
    first_tp_price = test_position.entry_price * (1 + PROFIT_LEVELS[0]['increase'])
    tokens_before = test_position.tokens
    
    result = await trading_system.execute_take_profit(
        token_address=test_position.token_address,
        tokens_to_sell=round(test_position.tokens * PROFIT_LEVELS[0]['sell_portion']),
        target_price=first_tp_price
    )
    
    if result:
        logger.info(f"First TP: Tokens before: {tokens_before}, after: {test_position.tokens}")
        assert abs(test_position.tokens - (tokens_before * 0.5)) < 0.01, "Should have 50% tokens remaining"
    
    # Test second take profit (should sell 25% of remaining)
    logger.info("\nTesting second take profit (120% up, should sell 25%)")
    second_tp_price = test_position.entry_price * (1 + PROFIT_LEVELS[1]['increase'])
    tokens_before = test_position.tokens
    
    result = await trading_system.execute_take_profit(
        token_address=test_position.token_address,
        tokens_to_sell=round(test_position.tokens * PROFIT_LEVELS[1]['sell_portion']),
        target_price=second_tp_price
    )
    
    if result:
        logger.info(f"Second TP: Tokens before: {tokens_before}, after: {test_position.tokens}")
        assert abs(test_position.tokens - (tokens_before * 0.75)) < 0.01, "Should have 75% of previous tokens remaining"
    
    logger.info("\nTest complete - Check logs to verify sell portions")

if __name__ == "__main__":
    # Run the test
    asyncio.run(test_take_profit_portions()) 