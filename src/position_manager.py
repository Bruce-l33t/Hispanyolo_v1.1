import argparse
import logging
import asyncio
import os
import sys
from pathlib import Path

# Add the project root to the Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.trading.trading_system import TradingSystem

class PositionManagerCLI:
    def __init__(self):
        self.trading_system = TradingSystem()

    def check_positions(self):
        positions = self.trading_system.position_manager.get_active_positions()
        if not positions:
            print("No active positions found.")
            return
        for position in positions:
            print(f"Token: {position.symbol}, Address: {position.token_address}")
            print(f"Entry Price: {position.entry_price}, Current Price: {position.current_price}")
            print(f"Tokens Held: {position.tokens}, Unrealized PNL: {position.ur_pnl}, Realized PNL: {position.r_pnl}")

    def check_summary(self):
        summary = self.trading_system.position_manager.get_position_summary()
        if summary['active_positions'] == 0:
            print("No active positions found.")
            return
        print(f"Total Unrealized PNL: {summary['unrealized_pnl']}")
        print(f"Total Realized PNL: {summary['realized_pnl']}")
        print(f"Total PNL: {summary['total_pnl']}")

    async def execute_sell(self, ticker, percentage):
        positions = self.trading_system.position_manager.get_active_positions()
        for position in positions:
            if position.symbol == ticker:
                amount_to_sell = position.tokens * (percentage / 100)
                await self.trading_system.execute_take_profit(position.token_address, amount_to_sell, position.current_price)
                print(f"Executed sell for {ticker}, Sold {percentage}% of current position")
                return
        print(f"Position for {ticker} not found")

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Position Management CLI')
    parser.add_argument('--check', action='store_true', help='Check current positions')
    parser.add_argument('--summary', action='store_true', help='Check total positions summary')
    parser.add_argument('--sell', nargs=2, metavar=('TICKER', 'PERCENTAGE'), help='Sell a percentage of a position')
    args = parser.parse_args()

    cli = PositionManagerCLI()

    if args.check:
        cli.check_positions()
    elif args.summary:
        cli.check_summary()
    elif args.sell:
        ticker, percentage = args.sell
        asyncio.run(cli.execute_sell(ticker, float(percentage))) 