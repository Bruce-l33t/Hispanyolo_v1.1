"""
Integration tests for Birdeye API using real endpoints
"""
import pytest
import requests
import logging
from pathlib import Path
import sys

# Add project root to path for imports
project_root = str(Path(__file__).parent.parent.absolute())
sys.path.insert(0, project_root)

from dontshare import birdeye_api_key

def get_trending_tokens(limit=3):
    """Helper to get trending token addresses for testing"""
    url = "https://public-api.birdeye.so/defi/token_trending"
    headers = {
        "X-API-KEY": birdeye_api_key,
        "accept": "application/json",
        "x-chain": "solana"
    }
    params = {
        "sort_by": "volume24hUSD",
        "time_range": "1H"
    }
    
    response = requests.get(url, headers=headers, params=params)
    logging.info(f"Trending tokens response: {response.json()}")
    
    test_tokens = []
    if response.status_code == 200:
        data = response.json()
        if data.get('success') and data.get('data', {}).get('tokens'):
            for token in data['data']['tokens'][:limit]:
                test_tokens.append(token['address'])
                logging.info(f"Found trending token: {token.get('symbol')} ({token['address']})")
                
    return test_tokens

def test_trending_endpoint():
    """Test trending tokens endpoint with real data"""
    url = "https://public-api.birdeye.so/defi/token_trending"
    headers = {
        "X-API-KEY": birdeye_api_key,
        "accept": "application/json",
        "x-chain": "solana"
    }
    params = {
        "sort_by": "volume24hUSD",
        "time_range": "1H"
    }
    
    response = requests.get(url, headers=headers, params=params)
    assert response.status_code == 200, "Expected successful API call"
    
    data = response.json()
    assert data.get('success'), "Expected success flag in response"
    assert 'data' in data, "Expected data in response"
    assert 'tokens' in data['data'], "Expected tokens array in data"
    assert len(data['data']['tokens']) > 0, "Expected at least one token"

def test_token_metadata():
    """Test token metadata endpoint with real trending tokens"""
    # Get trending tokens first
    test_tokens = get_trending_tokens()
    assert len(test_tokens) > 0, "Expected to find trending tokens"
    
    url = "https://public-api.birdeye.so/defi/v3/token/meta-data/multiple"
    headers = {
        "X-API-KEY": birdeye_api_key,
        "accept": "application/json",
        "x-chain": "solana"
    }
    params = {"list_address": ",".join(test_tokens)}
    
    response = requests.get(url, headers=headers, params=params)
    assert response.status_code == 200, "Expected successful API call"
    
    data = response.json()
    assert data.get('success'), "Expected success flag in response"
    assert 'data' in data, "Expected data in response"
    
    # Verify metadata for each token
    for token in test_tokens:
        assert token in data['data'], f"Expected metadata for {token}"
        metadata = data['data'][token]
        assert 'symbol' in metadata, "Expected symbol in metadata"
        assert 'decimals' in metadata, "Expected decimals in metadata"

def test_transaction_list():
    """Test transaction list endpoint with a known wallet"""
    url = "https://public-api.birdeye.so/v1/wallet/tx_list"
    headers = {
        "X-API-KEY": birdeye_api_key,
        "accept": "application/json"
    }
    
    # Test with a known active wallet
    test_wallet = "FWcjxiv1KA8G1499CWdRZnSrGYb8yKfynTyUTSj3AZX3"
    params = {
        "wallet": test_wallet,
        "limit": 100
    }
    
    response = requests.get(url, headers=headers, params=params)
    assert response.status_code == 200, "Expected successful API call"
    
    data = response.json()
    assert 'data' in data, "Expected data in response"
    assert 'solana' in data['data'], "Expected solana transactions in data"
    
    # Verify transaction data structure
    if data['data']['solana']:
        tx = data['data']['solana'][0]
        assert 'txHash' in tx, "Expected txHash in transaction"
        assert 'blockTime' in tx, "Expected blockTime in transaction"
        assert 'balanceChange' in tx, "Expected balanceChange in transaction"

def test_error_handling():
    """Test API error handling with invalid inputs"""
    # Test invalid wallet - API returns 200 with empty data
    url = "https://public-api.birdeye.so/v1/wallet/tx_list"
    headers = {
        "X-API-KEY": birdeye_api_key,
        "accept": "application/json"
    }
    params = {"wallet": "invalid_wallet"}
    
    response = requests.get(url, headers=headers, params=params)
    assert response.status_code == 200, "Expected 200 even for invalid wallet"
    data = response.json()
    assert 'data' in data, "Expected data object in response"
    assert 'solana' in data['data'], "Expected solana array in data"
    assert len(data['data']['solana']) == 0, "Expected empty transactions for invalid wallet"
    
    # Test invalid API key
    headers = {
        "X-API-KEY": "invalid_key",
        "accept": "application/json"
    }
    response = requests.get(url, headers=headers, params=params)
    assert response.status_code in [401, 403], "Expected auth error for invalid API key"
    
    # Test rate limiting by making rapid requests
    headers = {
        "X-API-KEY": birdeye_api_key,
        "accept": "application/json"
    }
    test_wallet = "FWcjxiv1KA8G1499CWdRZnSrGYb8yKfynTyUTSj3AZX3"
    params = {"wallet": test_wallet}
    
    for _ in range(5):
        response = requests.get(url, headers=headers, params=params)
        if response.status_code == 429:  # Rate limit hit
            break
    
    # Verify we can still make requests after backing off
    import time
    time.sleep(1)  # Wait a bit
    response = requests.get(url, headers=headers, params=params)
    assert response.status_code == 200, "Expected successful request after backoff"
    assert 'data' in response.json(), "Expected data in response after backoff"
