import pytest
import requests
from datetime import datetime, timezone
import os
import sys

# Get API key from dontshare.py
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from dontshare import birdeye_api_key

TEST_WALLET = "AUPQhiVX4Q9eFrF962p6P6Es777ydUksbTiS69VmQ5tT"
WSOL_ADDRESS = "So11111111111111111111111111111111111111112"

async def test_fetch_transactions():
    """Test fetching transactions from TEST_WALLET"""
    url = "https://public-api.birdeye.so/v1/wallet/tx_list"
    headers = {
        "X-API-KEY": birdeye_api_key,
        "accept": "application/json"
    }
    params = {
        "wallet": TEST_WALLET,
        "limit": 100,
        "type": "swap"
    }
    
    print(f"\n🔍 Requesting transactions for {TEST_WALLET[:8]}...")
    response = requests.get(url, headers=headers, params=params)
    
    print(f"Response Status: {response.status_code}")
    print(f"Response Time: {response.elapsed.total_seconds():.2f}s")
    
    assert response.status_code == 200, f"Expected 200, got {response.status_code}"
    
    data = response.json()
    transactions = data.get('data', {}).get('solana', [])
    tx_count = len(transactions)
    print(f"Transactions found: {tx_count}")
    
    assert tx_count > 0, "No transactions found"
    
    token_addresses = {}  # address -> {symbol, decimals}
    
    print("\nAnalyzing transactions...")
    for tx in transactions:
        tx_time = datetime.fromisoformat(tx['blockTime'].replace('Z', '+00:00'))
        time_ago = (datetime.now(timezone.utc) - tx_time).total_seconds() / 60
        
        # Skip if only SOL changes
        non_sol_changes = [c for c in tx['balanceChange'] if c['address'] != WSOL_ADDRESS]
        if not non_sol_changes:
            continue
            
        print(f"\nTransaction from {time_ago:.1f} minutes ago:")
        print(f"Hash: {tx['txHash']}")
        print("Balance changes:")
        
        for change in tx['balanceChange']:
            amount = float(change['amount'])
            decimals = int(change['decimals'])
            real_amount = abs(amount) / (10 ** decimals)
            symbol = change.get('symbol', 'Unknown')
            address = change.get('address', '')
            
            print(f"  • {symbol} ({address[:8]}...): {real_amount:.6f} ({'out' if amount < 0 else 'in'})")
            
            if address and address != WSOL_ADDRESS:
                token_addresses[address] = {
                    'symbol': symbol,
                    'decimals': decimals
                }
    
    print("\nUnique token addresses found:")
    for addr, info in token_addresses.items():
        print(f"  • {info['symbol']}: {addr}")
    
    return token_addresses

if __name__ == "__main__":
    import asyncio
    asyncio.run(test_fetch_transactions())
