# Birdeye API Integration Lessons

## Key Learnings from Testing

### 1. Don't Guess API Behavior
```python
# WRONG: Making assumptions about error codes
assert response.status_code == 404  # Assuming invalid wallets return 404

# RIGHT: Test actual behavior
response = requests.get(url, headers=headers, params=params)
assert response.status_code == 200  # API returns 200 with empty data
assert 'data' in response.json()
assert len(response.json()['data']['solana']) == 0  # Empty transactions array
```

### 2. Check Working Implementation First
```python
# Working implementation in Pirate2 shows:
# 1. We get price data from transaction balanceChange
for change in tx['balanceChange']:
    amount = float(change.get('amount', 0)) / 10 ** change.get('decimals', 9)
    address = change.get('address', '')
    
    if address == WSOL_ADDRESS:
        sol_amount = amount  # Can be positive (sell) or negative (buy)
```

### 3. Focus on What Matters
```python
# What really matters:
1. Transaction list endpoint - For getting balanceChange data
2. Metadata endpoint - For token info and categorization
3. Error handling - For reliable operation

# What doesn't matter:
1. Price endpoint - We get this from balanceChange
2. Multiple vs Single metadata - Both work fine
3. Complex error assumptions - API is more forgiving than expected
```

### 4. Test Real Behavior
```python
# WRONG: Testing what we think should happen
def test_error_handling():
    response = requests.get(url, headers=headers, params={"wallet": "invalid"})
    assert response.status_code in [404, 400]  # Wrong assumption

# RIGHT: Testing what actually happens
def test_error_handling():
    response = requests.get(url, headers=headers, params={"wallet": "invalid"})
    assert response.status_code == 200  # API returns 200
    data = response.json()
    assert 'data' in data
    assert 'solana' in data['data']
    assert len(data['data']['solana']) == 0  # Empty array for invalid wallet
```

## Critical Endpoints

### 1. Transaction List
```python
url = "https://public-api.birdeye.so/v1/wallet/tx_list"
headers = {
    "X-API-KEY": api_key,
    "accept": "application/json"
}
params = {
    "wallet": wallet_address,
    "limit": 100
}
```

### 2. Token Metadata
```python
url = "https://public-api.birdeye.so/defi/v3/token/meta-data/single"
# or
url = "https://public-api.birdeye.so/defi/v3/token/meta-data/multiple"
headers = {
    "X-API-KEY": api_key,
    "accept": "application/json"
}
```

## Real API Behavior

### 1. Invalid Wallets
- Returns 200 status code
- Returns empty transactions array
- Clean error handling not needed

### 2. Rate Limiting
- Responds with 429 when limit hit
- Recovers after short backoff
- Simple retry logic works well

### 3. Auth Errors
- Returns 401/403 for invalid key
- Clear error response
- Easy to handle

## Implementation Guidelines

### 1. Transaction Processing
```python
def process_transaction(tx: dict):
    if 'balanceChange' not in tx:
        return
        
    for change in tx['balanceChange']:
        amount = float(change.get('amount', 0)) / 10 ** change.get('decimals', 9)
        address = change.get('address', '')
        
        # Process based on address and amount
        process_token_change(address, amount)
```

### 2. Error Handling
```python
async def handle_api_error(e: Exception):
    if isinstance(e, RateLimitError):
        await asyncio.sleep(1)  # Simple backoff
        return True  # Retry
        
    if isinstance(e, AuthError):
        logger.error("API key error")
        return False  # Don't retry
        
    # Other errors
    logger.error(f"API error: {e}")
    return False
```

### 3. Metadata Caching
```python
class MetadataCache:
    def __init__(self):
        self.cache = {}
        
    def get_metadata(self, token_address: str):
        if token_address in self.cache:
            return self.cache[token_address]
            
        metadata = fetch_metadata(token_address)
        if metadata:
            self.cache[token_address] = metadata
        return metadata
```

## Testing Guidelines

### 1. Test Real Behavior
```python
def test_transaction_list():
    """Test with real wallet"""
    response = requests.get(url, headers=headers, params=params)
    assert response.status_code == 200
    data = response.json()
    
    # Check data structure
    assert 'data' in data
    assert 'solana' in data['data']
    
    # Check transaction format
    if data['data']['solana']:
        tx = data['data']['solana'][0]
        assert 'balanceChange' in tx
```

### 2. Error Cases
```python
def test_error_handling():
    """Test actual API error behavior"""
    # Invalid wallet returns 200 with empty data
    response = requests.get(url, headers=headers, params={"wallet": "invalid"})
    assert response.status_code == 200
    assert len(response.json()['data']['solana']) == 0
    
    # Invalid key returns auth error
    response = requests.get(url, headers={"X-API-KEY": "invalid"})
    assert response.status_code in [401, 403]
```

### 3. Rate Limiting
```python
def test_rate_limiting():
    """Test rate limit behavior"""
    for _ in range(5):  # Make several requests
        response = requests.get(url, headers=headers, params=params)
        if response.status_code == 429:
            # Wait and retry
            time.sleep(1)
            response = requests.get(url, headers=headers, params=params)
            assert response.status_code == 200
```

## Remember

1. Check working code first
2. Test actual behavior
3. Keep it simple
4. Focus on what matters

The key lesson: The working implementation is often the best documentation. Before writing new tests or making assumptions about API behavior, always check how the working code does it.
