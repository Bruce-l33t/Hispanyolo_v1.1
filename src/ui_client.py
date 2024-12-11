import asyncio
import websockets
import json
from datetime import datetime
from typing import Dict, List, Any

class UIClient:
    def __init__(self, uri: str = "ws://localhost:8000"):
        self.uri = uri
        self.websocket = None
        self.connected = False
        self.reconnect_delay = 1
        self.max_reconnect_delay = 30
        # For testing - track last sent data
        self.last_sent_data = None

    async def connect(self):
        """Connect to WebSocket server with retry"""
        while True:
            try:
                self.websocket = await websockets.connect(
                    self.uri,
                    ping_interval=20,  # Send ping every 20 seconds
                    ping_timeout=10    # Wait 10 seconds for pong
                )
                self.connected = True
                print("Connected to UI server")
                self.reconnect_delay = 1  # Reset delay on successful connection
                break
            except Exception as e:
                print(f"Failed to connect to UI server: {e}")
                self.connected = False
                await asyncio.sleep(self.reconnect_delay)
                self.reconnect_delay = min(self.reconnect_delay * 2, self.max_reconnect_delay)

    async def send_update(self, data: Dict[str, Any], max_retries: int = 3):
        """Send update to UI with retry"""
        # For testing - track sent data
        self.last_sent_data = data
        
        for attempt in range(max_retries):
            if not self.connected:
                await self.connect()
            
            if self.connected:
                try:
                    await self.websocket.send(json.dumps(data))
                    return  # Success
                except Exception as e:
                    print(f"Failed to send update (attempt {attempt + 1}): {e}")
                    self.connected = False
                    if attempt < max_retries - 1:
                        await asyncio.sleep(1)  # Wait before retry
                    continue

    async def update_token_metrics(self, metrics: Dict[str, Any]):
        """Update token metrics"""
        await self.send_update({"token_metrics": metrics})

    async def update_positions(self, positions: Dict[str, Any]):
        """Update positions"""
        await self.send_update({"active_positions": positions})  # Using active_positions key

    async def add_transaction(self, symbol: str, amount: float, tx_type: str):
        """Add new transaction"""
        transaction = {
            "symbol": symbol,
            "amount": amount,
            "type": tx_type,
            "timestamp": datetime.now().isoformat()
        }
        await self.send_update({
            "recent_transactions": [transaction]
        })

    async def update_system_status(self, wallet_status: Dict[str, int], 
                                 wallets_checked: int, 
                                 transactions_processed: int):
        """Update system status"""
        await self.send_update({
            "wallet_status": wallet_status,
            "wallets_checked": wallets_checked,
            "transactions_processed": transactions_processed
        })

    async def close(self):
        """Close WebSocket connection"""
        if self.websocket:
            try:
                await self.websocket.close()
            except:
                pass  # Ignore errors during close
            finally:
                self.connected = False
