"""
Tests for WebSocket server data flow
Verifies event transmission and data integrity with real data
"""
import pytest
import asyncio
from fastapi.testclient import TestClient
from fastapi.websockets import WebSocket
import json
from datetime import datetime, timezone
from typing import Dict, Any

from src.events import event_bell, EVENT_TYPES
from src.models import WalletStatus, Transaction
from src.monitor.monitor import WhaleMonitor
from src.monitor.token_metrics import TokenMetricsManager

@pytest.mark.asyncio
async def test_websocket_connection(websocket_server):
    """Test basic WebSocket connection with real monitor data"""
    # Initialize monitor components
    monitor = WhaleMonitor()
    
    async with websocket_server.websocket_connect("/ws") as websocket:
        # Should receive initial state
        data = await websocket.receive_json()
        assert "wallet_status" in data
        assert "token_metrics" in data
        assert "positions" in data

@pytest.mark.asyncio
async def test_real_transaction_flow(websocket_server):
    """Test transaction event flow with real monitor data"""
    # Initialize monitor
    monitor = WhaleMonitor()
    
    async with websocket_server.websocket_connect("/ws") as websocket:
        # Clear initial state
        await websocket.receive_json()
        
        # Start monitor
        await monitor.run()
        
        # Should receive real transaction updates
        data = await websocket.receive_json()
        assert "recent_transactions" in data
        
        # Verify transaction data structure
        if data["recent_transactions"]:
            tx = data["recent_transactions"][0]
            assert "symbol" in tx
            assert "amount" in tx
            assert "type" in tx
            assert "time" in tx

@pytest.mark.asyncio
async def test_real_token_metrics_flow(websocket_server):
    """Test token metrics event flow with real data"""
    # Initialize components
    monitor = WhaleMonitor()
    metrics_manager = TokenMetricsManager()
    
    async with websocket_server.websocket_connect("/ws") as websocket:
        # Clear initial state
        await websocket.receive_json()
        
        # Start monitor
        await monitor.run()
        
        # Should receive token metrics updates
        data = await websocket.receive_json()
        assert "token_metrics" in data
        
        # Verify metrics data structure
        if data["token_metrics"]:
            token = next(iter(data["token_metrics"].values()))
            assert "symbol" in token
            assert "score" in token
            assert "category" in token

@pytest.mark.asyncio
async def test_real_wallet_status_flow(websocket_server):
    """Test wallet status event flow with real data"""
    # Initialize monitor
    monitor = WhaleMonitor()
    
    async with websocket_server.websocket_connect("/ws") as websocket:
        # Clear initial state
        await websocket.receive_json()
        
        # Start monitor
        await monitor.run()
        
        # Should receive wallet status updates
        data = await websocket.receive_json()
        assert "wallet_status" in data
        assert all(status in data["wallet_status"] for status in 
                  ["VERY_ACTIVE", "ACTIVE", "WATCHING", "ASLEEP"])

@pytest.mark.asyncio
async def test_multiple_clients_real_data(websocket_server):
    """Test multiple WebSocket clients receiving real updates"""
    # Initialize monitor
    monitor = WhaleMonitor()
    
    async with websocket_server.websocket_connect("/ws") as ws1, \
              websocket_server.websocket_connect("/ws") as ws2:
        # Clear initial states
        await ws1.receive_json()
        await ws2.receive_json()
        
        # Start monitor
        await monitor.run()
        
        # Both clients should receive same updates
        data1 = await ws1.receive_json()
        data2 = await ws2.receive_json()
        assert data1 == data2

@pytest.mark.asyncio
async def test_connection_recovery_real_data(websocket_server):
    """Test WebSocket connection recovery with real data flow"""
    # Initialize monitor
    monitor = WhaleMonitor()
    
    async with websocket_server.websocket_connect("/ws") as websocket:
        # Clear initial state
        await websocket.receive_json()
        
        # Start monitor
        await monitor.run()
        
        # Get some real data
        initial_data = await websocket.receive_json()
        
        # Simulate connection drop
        await websocket.close()
        
        # Reconnect
        async with websocket_server.websocket_connect("/ws") as new_ws:
            # Should receive fresh state
            new_data = await new_ws.receive_json()
            
            # Verify data structure maintained
            assert set(initial_data.keys()) == set(new_data.keys())

@pytest.mark.asyncio
async def test_large_data_flow(websocket_server):
    """Test handling of large real data updates"""
    # Initialize monitor
    monitor = WhaleMonitor()
    
    async with websocket_server.websocket_connect("/ws") as websocket:
        # Clear initial state
        await websocket.receive_json()
        
        # Start monitor and let it run for a bit to accumulate data
        await monitor.run()
        await asyncio.sleep(5)  # Allow time for data collection
        
        # Should handle large updates
        data = await websocket.receive_json()
        assert "token_metrics" in data
        assert "recent_transactions" in data
        
        # Verify data integrity maintained with large datasets
        if data["token_metrics"]:
            for token in data["token_metrics"].values():
                assert "symbol" in token
                assert "score" in token
                assert "category" in token
