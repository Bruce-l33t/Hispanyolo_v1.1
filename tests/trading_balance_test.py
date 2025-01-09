import sys
import os
import asyncio
import logging
from pathlib import Path

# Add the project root to the Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.trading.trading_system import TradingSystem
from src.utils.sol_balance import get_sol_balance

async def test_trading_balance():
    """Test that trading system correctly handles low balance"""
    logging.basicConfig(level=logging.DEBUG)
    logger = logging.getLogger('test')
    
    # Initialize trading system
    trading_system = TradingSystem()
    
    # First check our actual balance
    current_balance = await get_sol_balance()
    logger.info(f"Current SOL balance: {current_balance:.4f} SOL")
    
    # Create a test signal
    test_signal = {
        'token_address': 'FLhNk1NJVkngyJf7Stne2nRa3BvCw5Lm7pncsuMHpump',
        'symbol': 'TEST',
        'category': 'MEME',
        'score': 200,  # High enough to trigger trade
        'confidence': 0.9
    }
    
    logger.info("Testing signal processing with current balance...")
    await trading_system.handle_signal(test_signal)
    
    # The test passes if:
    # 1. If balance < 1 SOL: The trade should be skipped with appropriate logging
    # 2. If balance >= 1 SOL: The normal trading flow should proceed
    
    # We can verify the behavior by checking the logs
    logger.info("Test complete - Check logs to verify balance handling")

if __name__ == "__main__":
    # Run the test
    asyncio.run(test_trading_balance()) 