"""
Simple event system for Pirate3
Direct event emission and subscription, no middleware
"""
import logging
from typing import Dict, List, Callable, Any
import asyncio

logger = logging.getLogger('events')

class EventSystem:
    """
    Simple pub/sub event system
    No middleware, no complex forwarding
    Direct event emission and subscription
    """
    def __init__(self):
        self.subscribers: Dict[str, List[Callable]] = {}
        self.logger = logging.getLogger('events')
        # Set debug level for events
        self.logger.setLevel(logging.DEBUG)

    async def publish(self, event_type: str, data: Dict[str, Any]):
        """
        Publish event directly to subscribers
        No transformations, no middleware
        """
        if event_type not in self.subscribers:
            self.logger.debug(f"No subscribers for event type: {event_type}")
            return

        self.logger.debug(f"Publishing {event_type} event with data: {data}")
        
        # Direct emission to subscribers
        for subscriber in self.subscribers[event_type]:
            try:
                self.logger.debug(f"Calling subscriber for {event_type}: {subscriber.__name__ if hasattr(subscriber, '__name__') else str(subscriber)}")
                await subscriber(data)
            except Exception as e:
                self.logger.error(f"Error in subscriber for {event_type}: {e}", exc_info=True)

    async def subscribe(self, event_type: str, callback: Callable):
        """Subscribe to event type"""
        if event_type not in self.subscribers:
            self.subscribers[event_type] = []
            
        self.subscribers[event_type].append(callback)
        self.logger.info(f"Subscribed to event: {event_type}")

    async def unsubscribe(self, event_type: str, callback: Callable):
        """Unsubscribe from event type"""
        if event_type in self.subscribers and callback in self.subscribers[event_type]:
            self.subscribers[event_type].remove(callback)
            self.logger.info(f"Unsubscribed from event: {event_type}")

# Single event system instance
event_bell = EventSystem()

# Core event types
EVENT_TYPES = {
    # Trading events
    'trading_signal',     # Trading signals
    'position_update',    # Position changes (used for logging and monitoring)
    'trade_executed',     # Trade execution
    
    # Token events
    'token_metrics',      # Token metrics updates
    'transaction'         # New transactions
}
