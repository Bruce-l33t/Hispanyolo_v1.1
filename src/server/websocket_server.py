"""
WebSocket server for real-time UI updates
Handles event distribution and connection management
"""
import asyncio
import logging
from datetime import datetime, timezone
from typing import Dict, List, Any, Optional
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from pydantic import BaseModel, ValidationError

from ..events import event_bell, EVENT_TYPES
from ..models import WalletStatus

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('websocket_server')

class ConnectionManager:
    """Manage WebSocket connections and message broadcasting"""
    def __init__(self):
        self.active_connections: List[WebSocket] = []
        self.connection_states: Dict[WebSocket, Dict[str, Any]] = {}
        self.logger = logging.getLogger('websocket_manager')

    async def connect(self, websocket: WebSocket):
        """Handle new connection"""
        await websocket.accept()
        self.active_connections.append(websocket)
        self.connection_states[websocket] = {
            'connected_at': datetime.now(timezone.utc).isoformat(),
            'last_ping': datetime.now(timezone.utc).isoformat(),
            'messages_sent': 0
        }
        self.logger.info(f"New connection. Total active: {len(self.active_connections)}")

    def disconnect(self, websocket: WebSocket):
        """Handle disconnection"""
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
            self.connection_states.pop(websocket, None)
            self.logger.info(f"Connection closed. Total active: {len(self.active_connections)}")

    async def broadcast(self, message: Dict[str, Any]):
        """Broadcast message to all connections"""
        disconnected = []
        for connection in self.active_connections:
            try:
                await connection.send_json(message)
                state = self.connection_states[connection]
                state['messages_sent'] += 1
                
            except Exception as e:
                self.logger.error(f"Error broadcasting to client: {e}")
                disconnected.append(connection)

        # Cleanup disconnected
        for connection in disconnected:
            self.disconnect(connection)

    def get_connection_stats(self) -> Dict[str, Any]:
        """Get connection statistics"""
        return {
            'active_connections': len(self.active_connections),
            'total_messages_sent': sum(
                state['messages_sent'] 
                for state in self.connection_states.values()
            ),
            'connection_states': {
                str(ws): state 
                for ws, state in self.connection_states.items()
            }
        }

class UIState:
    """Maintain current UI state"""
    def __init__(self):
        self.state = {
            "wallet_status": {
                "VERY_ACTIVE": 0,
                "ACTIVE": 0,
                "WATCHING": 0,
                "ASLEEP": 0
            },
            "wallets_checked": 0,
            "transactions_processed": 0,
            "token_metrics": {},
            "positions": {},
            "recent_transactions": [],
            "signal_history": [],
            "system_status": {
                "connected": True,
                "last_update": datetime.now(timezone.utc).isoformat()
            }
        }
        self.max_transactions = 50
        self.max_signals = 20

    def update(self, event_type: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """Update state based on event type"""
        try:
            if event_type == "system_update":
                if "wallet_status" in data:
                    self.state["wallet_status"].update(data["wallet_status"])
                if "wallets_checked" in data:
                    self.state["wallets_checked"] = data["wallets_checked"]
                if "transactions_processed" in data:
                    self.state["transactions_processed"] = data["transactions_processed"]

            elif event_type == "token_metrics":
                self.state["token_metrics"].update(data)

            elif event_type == "transaction":
                self.state["recent_transactions"].insert(0, data)
                self.state["recent_transactions"] = \
                    self.state["recent_transactions"][:self.max_transactions]

            elif event_type == "trading_signal":
                self.state["signal_history"].insert(0, {
                    **data,
                    "time": datetime.now(timezone.utc).isoformat()
                })
                self.state["signal_history"] = \
                    self.state["signal_history"][:self.max_signals]

            elif event_type == "position_update":
                if "positions" in data:
                    self.state["positions"] = data["positions"]

            # Update timestamp
            self.state["system_status"]["last_update"] = \
                datetime.now(timezone.utc).isoformat()

            return self.state

        except Exception as e:
            logger.error(f"Error updating state: {e}")
            return {
                "error": str(e),
                "event_type": event_type,
                "data": data
            }

class WebSocketServer:
    """WebSocket server implementation"""
    def __init__(self, app: FastAPI):
        self.app = app
        self.manager = ConnectionManager()
        self.state = UIState()
        self.setup_routes()

    def setup_routes(self):
        """Setup WebSocket routes"""
        @self.app.websocket("/ws")
        async def websocket_endpoint(websocket: WebSocket):
            await self.manager.connect(websocket)
            
            try:
                # Send initial state
                await websocket.send_json(self.state.state)
                
                # Handle connection
                while True:
                    try:
                        # Wait for ping or close
                        data = await websocket.receive_text()
                        if data == "ping":
                            await websocket.send_text("pong")
                            self.manager.connection_states[websocket]['last_ping'] = \
                                datetime.now(timezone.utc).isoformat()
                    except WebSocketDisconnect:
                        self.manager.disconnect(websocket)
                        break
                        
            except Exception as e:
                logger.error(f"WebSocket error: {e}")
                self.manager.disconnect(websocket)

    async def handle_event(self, event_type: str, data: Dict[str, Any]):
        """Handle incoming events"""
        # Update state
        updated_state = self.state.update(event_type, data)
        
        # Broadcast to all clients
        await self.manager.broadcast(updated_state)

def create_server() -> FastAPI:
    """Create and configure server"""
    app = FastAPI()
    
    # Enable CORS
    from fastapi.middleware.cors import CORSMiddleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # Initialize WebSocket server
    server = WebSocketServer(app)
    
    # Setup event handlers
    @app.on_event("startup")
    async def startup_event():
        # Subscribe to all events
        for event_type in EVENT_TYPES:
            await event_bell.subscribe(
                event_type,
                lambda data, et=event_type: server.handle_event(et, data)
            )
    
    return app

# Create server instance
app = create_server()
