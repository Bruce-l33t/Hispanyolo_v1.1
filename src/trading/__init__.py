"""
Trading system initialization
Exposes main interfaces
"""
from .trading_system import TradingSystem
from .signal_processor import SignalProcessor
from .alchemy import AlchemyTrader

__all__ = [
    'TradingSystem',
    'SignalProcessor',
    'AlchemyTrader'
]
