"""
Tests for UI data handling
"""
import pytest
import json
import asyncio
import websockets
import subprocess
import time
import signal
import os
from pathlib import Path

# Test data
TEST_TOKEN_DATA = {
    'token_metrics': {
        'yumi': {
            'symbol': 'yumi',
            'category': 'MEME',
            'score': 300.0,
            'confidence': 0.0,
            'buy_count': 1,
            'sell_count': 0,
            'total_volume': 5.0448,
            'unique_buyers': 1,
            'last_update': '2024-12-10T09:54:47+00:00',
            'recent_changes': []
        }
    }
}

async def wait_for_server(max_attempts=5, delay=1):
    """Wait for server to be ready"""
    for _ in range(max_attempts):
        try:
            async with websockets.connect('ws://localhost:8000') as ws:
                return True
        except:
            await asyncio.sleep(delay)
    return False

@pytest.fixture(scope="module")
async def ui_server():
    """Start UI server for tests"""
    # Get path to UI server
    ui_dir = Path(__file__).parent.parent / 'pirate_ui'
    server_path = ui_dir / 'server.ts'
    
    # Start server process
    server = subprocess.Popen(
        ['npx', 'ts-node', str(server_path)],
        cwd=str(ui_dir),
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        preexec_fn=os.setsid  # Use process group
    )
    
    # Wait for server to be ready
    server_ready = await wait_for_server()
    if not server_ready:
        os.killpg(os.getpgid(server.pid), signal.SIGTERM)
        server.wait()
        raise RuntimeError("Server failed to start")
    
    yield server
    
    # Cleanup server
    try:
        os.killpg(os.getpgid(server.pid), signal.SIGTERM)
        server.wait(timeout=5)
    except:
        os.killpg(os.getpgid(server.pid), signal.SIGKILL)
        server.wait()

@pytest.mark.asyncio
async def test_token_metrics_update(ui_server):
    """Test token metrics data handling"""
    # Connect to server with retries
    for attempt in range(3):
        try:
            async with websockets.connect('ws://localhost:8000') as ws:
                # Send test data
                await ws.send(json.dumps(TEST_TOKEN_DATA))
                
                # Get response
                response = await ws.recv()
                data = json.loads(response)
                
                # Verify token data
                assert 'token_metrics' in data
                token = data['token_metrics']['yumi']
                assert token['symbol'] == 'yumi'
                assert token['category'] == 'MEME'
                assert token['score'] == 300.0
                return
        except Exception as e:
            if attempt == 2:  # Last attempt
                raise
            await asyncio.sleep(1)

@pytest.mark.asyncio
async def test_token_display(ui_server):
    """Test token display in UI"""
    # Connect to server with retries
    for attempt in range(3):
        try:
            async with websockets.connect('ws://localhost:8000') as ws:
                # Send test data
                await ws.send(json.dumps(TEST_TOKEN_DATA))
                
                # Get response
                response = await ws.recv()
                data = json.loads(response)
                
                # Verify token display data
                token = data['token_metrics']['yumi']
                assert token['symbol'] == 'yumi'  # Should use symbol for display
                assert token['score'] == 300.0    # Score should be preserved
                return
        except Exception as e:
            if attempt == 2:  # Last attempt
                raise
            await asyncio.sleep(1)
