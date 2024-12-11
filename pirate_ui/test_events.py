import asyncio
import websockets
import json
import time
from datetime import datetime

# Test data
test_token_metrics = {
    "token_metrics": {
        "token1": {
            "symbol": "AI_TOKEN",
            "category": "AI",
            "score": 85.5,
            "confidence": 0.9
        },
        "token2": {
            "symbol": "MEME_COIN",
            "category": "MEME",
            "score": 95.0,
            "confidence": 0.8
        }
    }
}

test_positions = {
    "positions": {
        "AI_TOKEN": {
            "symbol": "AI_TOKEN",
            "current_size": 1.234,
            "entry_price": 0.00123,
            "current_price": 0.00145,
            "unrealized_pnl": 17.89
        },
        "MEME_COIN": {
            "symbol": "MEME_COIN",
            "current_size": 2.345,
            "entry_price": 0.00234,
            "current_price": 0.00256,
            "unrealized_pnl": -5.67
        }
    }
}

test_transactions = {
    "recent_transactions": [
        {
            "symbol": "AI_TOKEN",
            "amount": 1.234,
            "type": "buy",
            "timestamp": datetime.now().isoformat()
        },
        {
            "symbol": "MEME_COIN",
            "amount": 0.567,
            "type": "sell",
            "timestamp": datetime.now().isoformat()
        }
    ]
}

test_wallet_status = {
    "wallet_status": {
        "VERY_ACTIVE": 2,
        "ACTIVE": 5,
        "WATCHING": 270,
        "ASLEEP": 4
    },
    "wallets_checked": 281,
    "transactions_processed": 1423
}

async def send_test_data():
    """Send test data to WebSocket server"""
    uri = "ws://localhost:8000"
    
    try:
        async with websockets.connect(uri) as websocket:
            print("Connected to WebSocket server")
            
            # Send initial token metrics
            print("Sending token metrics...")
            await websocket.send(json.dumps(test_token_metrics))
            await asyncio.sleep(2)
            
            # Send position updates
            print("Sending positions...")
            await websocket.send(json.dumps(test_positions))
            await asyncio.sleep(2)
            
            # Send transactions
            print("Sending transactions...")
            await websocket.send(json.dumps(test_transactions))
            await asyncio.sleep(2)
            
            # Send wallet status
            print("Sending wallet status...")
            await websocket.send(json.dumps(test_wallet_status))
            await asyncio.sleep(2)
            
            # Update a position's PNL
            print("Updating position PNL...")
            test_positions["positions"]["AI_TOKEN"]["unrealized_pnl"] = 25.43
            await websocket.send(json.dumps({"positions": test_positions["positions"]}))
            await asyncio.sleep(2)
            
            # Add new transaction
            print("Adding new transaction...")
            new_transaction = {
                "recent_transactions": [
                    {
                        "symbol": "NEW_TOKEN",
                        "amount": 3.456,
                        "type": "buy",
                        "timestamp": datetime.now().isoformat()
                    },
                    *test_transactions["recent_transactions"]
                ]
            }
            await websocket.send(json.dumps(new_transaction))
            
            print("Test data sent successfully")
            
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    print("Starting WebSocket test client...")
    asyncio.run(send_test_data())
