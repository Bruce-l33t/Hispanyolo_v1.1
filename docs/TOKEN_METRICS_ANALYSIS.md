# Token Metrics System Analysis

A detailed look at the token metrics and scoring system that works well.

## Overview
The token metrics system combines:
- Score tracking
- Transaction processing
- Signal generation
- Data cleanup

## Key Components

### 1. Metrics Manager
```python
class TokenMetricsManager:
    def __init__(self):
        self.token_metrics: Dict[str, TokenMetrics] = {}
        self.categorizer = TokenCategorizer()
```

### 2. Transaction Processing
```python
async def process_transaction(
    self,
    token_address: str,
    symbol: str,
    amount: float,
    tx_type: str,
    wallet_address: str,
    wallet_score: float
):
    metrics = await self.get_or_create_metrics(token_address, symbol)
    
    if tx_type == 'buy':
        metrics.add_score(wallet_score, wallet_address, amount)
    elif tx_type == 'sell':
        metrics.reduce_score(wallet_score, amount)
```

### 3. Signal Generation
```python
# Check for trading signals
threshold = self.categorizer.get_token_score_threshold(metrics.category)
if metrics.score >= threshold:
    await event_bell.publish('trading_signals', {
        'signals': [{
            'token_address': token_address,
            'symbol': symbol,
            'category': metrics.category,
            'score': metrics.score,
            'confidence': metrics.confidence
        }]
    })
```

### 4. Data Management
```python
def cleanup_old_tokens(self, max_age_hours: int = 24):
    now = datetime.now(timezone.utc)
    addresses_to_remove = []
    
    for address, metrics in self.token_metrics.items():
        age = (now - metrics.last_update).total_seconds() / 3600
        if age > max_age_hours and metrics.score == 0:
            addresses_to_remove.append(address)
```

## Why It Works Well

### 1. Smart Score Tracking
- Accumulates score based on wallet reputation
- Considers transaction volume
- Tracks unique buyers
- Maintains history of changes

### 2. Clear Signal Generation
- Uses category-specific thresholds
- Includes confidence scores
- Provides complete signal data
- Clear event format

### 3. Efficient Data Management
- Automatic cleanup of old data
- Tracks last update times
- Maintains recent history
- Memory efficient

### 4. Event Integration
- Direct event emission
- Clear data structure
- Real-time updates
- No middleware

## Lessons for New Implementation

### 1. Keep
- Score accumulation logic
- Category-based thresholds
- Transaction processing
- Data cleanup system

### 2. Improve
- Add more metrics tracking
- Enhanced signal validation
- Better error handling
- Performance optimization

## Example Usage

### 1. Processing a Buy
```python
await metrics_manager.process_transaction(
    token_address="abc123",
    symbol="TEST",
    amount=1.5,
    tx_type="buy",
    wallet_address="xyz789",
    wallet_score=1000.0
)
```

### 2. Checking Signals
```python
threshold = categorizer.get_token_score_threshold("AI")
if metrics.score >= threshold:
    # Emit trading signal
    await event_bell.publish('trading_signals', {...})
```

### 3. Cleanup
```python
# Run periodically
metrics_manager.cleanup_old_tokens(max_age_hours=24)
```

## Integration Points

### 1. With Monitor
- Receives transaction data
- Updates metrics
- Generates signals

### 2. With Trading System
- Emits trading signals
- Provides score data
- Tracks position impact

### 3. With UI
- Provides metrics updates
- Shows score changes
- Displays signals

## Next Steps

### 1. Documentation
- Add detailed API docs
- Document event formats
- Create usage examples

### 2. Testing
- Add unit tests
- Create integration tests
- Test edge cases

### 3. Optimization
- Add caching
- Optimize cleanup
- Improve performance
