# Implementation Fixes for Pirate3

## Core Issues Found

### 1. Trading System Integration
- Trading system works but needs proper testing approach
- Integration tests show correct flow
- Position manager and trading system responsibilities need clarity

### 2. Test Coverage Gaps
- Position Manager tests use wrong parameters
- PNL calculations need fixing
- Take profit logic split between components

### 3. Implementation Mismatches
- Position Manager expects tokens but tests pass SOL amount
- Take profit execution responsibilities unclear
- PNL calculation assumptions incorrect

### 4. Take Profit Strategy
- Implemented partial sell strategy for better risk management
- Sells 25% of position at each take profit level
- Tracks hit profit levels to prevent duplicate sells
- Maintains position until all tokens sold or stop loss hit

## Take Profit Implementation

### 1. Configuration
```python
# In config.py
PROFIT_LEVELS = [
    {'increase': 0.6, 'sell_portion': 0.25},  # 60% up, sell 25%
    {'increase': 1.2, 'sell_portion': 0.25},  # 120% up, sell 25%
    {'increase': 1.8, 'sell_portion': 0.25},  # 180% up, sell 25%
    {'increase': 2.4, 'sell_portion': 0.25}   # 240% up, sell 25%
]
```

### 2. Position Tracking
```python
@dataclass
class Position:
    """Trading position data"""
    profit_levels_hit: Set[int] = field(default_factory=set)  # Track hit levels
```

### 3. Take Profit Logic
```python
# In TradingSystem
async def execute_take_profit(self, token_address: str, tokens_to_sell: float):
    """Execute take profit with proper position tracking"""
    position = self.position_manager.positions.get(token_address)
    
    # Sell portion of tokens
    signature = await self.trader.execute_swap(
        token_address=token_address,
        amount_in=tokens_to_sell
    )
    
    if signature:
        # Update position
        self.position_manager.update_realized_pnl(
            token_address=token_address,
            tokens_sold=tokens_to_sell,
            sell_price=target_price
        )
        
        # Track profit level hit
        position.profit_levels_hit.add(level_index)
```

### 4. Testing Strategy
```python
async def test_take_profit_execution():
    """Test partial sell at take profit levels"""
    # Create test position with 100 tokens
    signal = {
        'token_address': TEST_TOKEN,
        'symbol': TEST_SYMBOL,
        'category': 'AI',
        'score': 200
    }
    await trading.handle_signal(signal)
    
    # Hit first take profit (60% up)
    target_price = TEST_PRICE * 1.6
    mock_price_service.get_prices.return_value = {
        TEST_TOKEN: target_price
    }
    
    await trading.update_positions()
    
    # Verify partial sell
    position = trading.position_manager.get_active_positions()[0]
    assert position.tokens == 75  # 75 tokens remaining
    assert position.r_pnl == pytest.approx(15.0)  # 25 tokens * 0.6 profit each
    assert position.profit_levels_hit == {0}  # First level hit
```

## Good Testing Examples

### 1. Birdeye API Tests (test_birdeye_real.py)
```python
def test_token_metadata():
    """Test with real trending tokens"""
    # Get real tokens to test with
    test_tokens = get_trending_tokens()
    
    # Test actual API
    response = requests.get(url, headers=headers, params=params)
    assert response.status_code == 200
    
    # Verify response structure
    data = response.json()
    assert 'symbol' in metadata
    assert 'decimals' in metadata

def test_error_handling():
    """Test real error scenarios"""
    # Test invalid inputs
    response = requests.get(url, headers=headers, params={"wallet": "invalid"})
    assert response.status_code == 200
    assert len(data['data']['solana']) == 0
    
    # Test rate limiting
    for _ in range(5):
        response = requests.get(url, headers=headers, params=params)
        if response.status_code == 429:  # Rate limit hit
            break
    
    # Test recovery
    time.sleep(1)
    response = requests.get(url, headers=headers, params=params)
    assert response.status_code == 200
```

### 2. Trading Execution Tests (test_trading_execution.py)
```python
async def test_valid_quote():
    """Test actual Jupiter API"""
    quote = trader.get_jupiter_quote(
        token_address=TEST_TOKEN,
        amount_in=TEST_AMOUNT
    )
    assert quote is not None
    
async def test_complete_swap():
    """Test real swap execution"""
    tx_hash = await trader.execute_swap(
        token_address=TEST_TOKEN,
        amount_in=TEST_AMOUNT
    )
    assert tx_hash is not None
```

### 3. Integration Tests (test_integration.py)
```python
async def test_transaction_to_trade_flow():
    """Test complete system flow"""
    # Setup system
    monitor = WhaleMonitor()
    trading = TradingSystem()
    
    # Process real transaction
    await monitor.process_wallet(TEST_WALLET)
    
    # Verify position created
    positions = trading.position_manager.get_active_positions()
    assert len(positions) == 1
```

## Required Changes

### 1. Position Manager Tests
Update test_position_manager.py to:
```python
class TestPositionManager:
    async def test_open_position():
        # Test with tokens not SOL
        position = manager.open_position(
            token_address="token",
            symbol="TEST",
            category="AI",
            entry_price=1.0,
            tokens=100  # Number of tokens
        )
        assert position.tokens == 100
        
    async def test_pnl_calculation():
        # Test proper PNL math
        position = manager.open_position(...)
        manager.update_position("token", 1.1)
        assert position.r_pnl == 0.0
        assert position.ur_pnl == pytest.approx(10.0)
```

### 2. Take Profit Tests
Move take profit execution tests to trading system:
```python
class TestTradingSystem:
    async def test_take_profit_execution():
        # Setup position
        signal = {...}
        await trading.handle_signal(signal)
        
        # Hit take profit level
        target_price = TEST_PRICE * 1.6
        mock_price_service.get_prices.return_value = {
            TEST_TOKEN: target_price
        }
        
        await trading.update_positions()
        
        # Verify partial sell
        position = trading.position_manager.get_active_positions()[0]
        assert position.tokens == 75  # 25% sold
        assert position.r_pnl == pytest.approx(15.0)
```

## Implementation Order

### Week 1: Test Cleanup
1. Remove mock-based tests
2. Fix position manager tests
3. Move diagnostic tools

### Week 2: Implementation Fixes
1. Fix PNL calculations
2. Fix take profit logic
3. Fix position parameters

### Week 3: Documentation
1. Document testing approach
2. Add debugging guide
3. Update API docs

## Success Criteria

### 1. Test Coverage
- Real API tests working
- Integration tests passing
- Error cases covered

### 2. Code Quality
- Clear component boundaries
- Proper error handling
- Consistent patterns

### 3. Documentation
- Clear testing guide
- API documentation
- Debugging guide

## Monitoring

### 1. Test Results
- All tests passing
- Coverage metrics met
- No flaky tests

### 2. Error Handling
- Proper logging
- Clear error messages
- Recovery paths tested

### 3. Performance
- Quick test execution
- Efficient testing
- Clear test output

## Notes
- Follow Birdeye API test pattern
- Test with real APIs where possible
- Handle errors properly
- Document testing patterns
- Partial sells provide better risk management
- Track profit levels to prevent duplicate sells
- Maintain positions until fully sold or stopped out
