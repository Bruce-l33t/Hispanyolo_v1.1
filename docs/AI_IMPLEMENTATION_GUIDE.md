# AI Implementation Guide for Pirate3

## Document Reading Order

### 1. Requirements & Approach
1. `CORE_REQUIREMENTS.md`
   - Understand essential features
   - Note must-haves vs nice-to-haves
   - Understand success criteria

2. `IMPLEMENTATION_APPROACH.md`
   - Review core architecture
   - Understand component relationships
   - Note testing strategy

### 2. Reference Material
1. `alex/LESSONS_FOR_PIRATE3.md`
   - Learn from previous versions
   - Note what worked/didn't work
   - Understand key improvements

2. `alex/EVOLUTION_INSIGHTS.md`
   - Understand system evolution
   - Note architectural improvements
   - Learn from past challenges

### 3. Component Details
1. `TOKEN_METRICS_ANALYSIS.md`
   - For score tracking implementation
   - For signal generation
   - For categorization

2. `BIRDEYE_INTEGRATION.md`
   - For API integration
   - For error handling
   - For rate limiting

3. `TRADING_SYSTEM.md`
   - For position management
   - For risk rules
   - For execution logic

## Implementation Order

### 1. Project Setup
```python
# Start with basic structure
project/
    src/
        monitor/
        trading/
        ui/
    tests/
    config/
```

### 2. Core Components
1. Monitor First:
   - Wallet tracking
   - Transaction processing
   - Score updates

2. Trading Second:
   - Signal handling
   - Position management
   - Trade execution

3. UI Last:
   - Basic status display
   - Position view
   - Signal monitoring

## Key Principles

### 1. Keep It Simple
```python
# Example: Direct event handling
async def handle_transaction(tx: dict):
    if is_real_swap(tx):
        await update_scores(tx)
        await check_signals(tx)
```

### 2. Focus on Core Features
```python
# Example: Essential monitoring
class Monitor:
    async def run(self):
        while True:
            # 1. Get transactions
            txs = await get_transactions()
            
            # 2. Process real swaps
            for tx in filter(is_real_swap, txs):
                await process_transaction(tx)
```

### 3. Clear Testing
```python
# Example: Core functionality tests
async def test_monitor():
    # Given
    monitor = Monitor()
    tx = create_test_transaction()
    
    # When
    await monitor.process(tx)
    
    # Then
    assert scores_updated()
```

## Implementation Steps

### 1. For Each Component
1. Review Requirements:
   - Check CORE_REQUIREMENTS.md
   - Note essential features
   - Identify must-haves

2. Check Approach:
   - Review IMPLEMENTATION_APPROACH.md
   - Note component design
   - Understand interactions

3. Reference Details:
   - Check component-specific docs
   - Note working patterns
   - Understand pitfalls

### 2. Development Flow
1. Start Simple:
   ```python
   # Begin with core functionality
   class Component:
       async def core_function(self):
           # Essential logic only
           pass
   ```

2. Add Features:
   ```python
   # Add required features one by one
   class Component:
       async def core_function(self):
           # Essential logic
           pass
           
       async def required_feature(self):
           # Additional required functionality
           pass
   ```

3. Test Thoroughly:
   ```python
   # Test each feature
   async def test_component():
       # Test core functionality
       await test_core()
       
       # Test required features
       await test_required_features()
   ```

## Review Process

### 1. Before Implementation
- Read CORE_REQUIREMENTS.md
- Check IMPLEMENTATION_APPROACH.md
- Review relevant component docs

### 2. During Implementation
- Focus on essential features
- Keep it simple
- Test thoroughly

### 3. After Implementation
- Verify against requirements
- Check test coverage
- Validate functionality

## Common Pitfalls

### 1. Over-engineering
```python
# Don't do this
class ComplexSystem:
    async def process(self):
        # Complex state management
        # Multiple transformations
        # Unnecessary abstraction
```

### 2. Feature Creep
```python
# Don't add unnecessary features
class Component:
    async def nice_to_have(self):
        # Focus on must-haves first
        pass
```

### 3. Complex Events
```python
# Keep it direct
async def handle_event(event):
    # Direct processing
    await process(event)
```

## Success Metrics

### 1. Code Quality
- Simple and clear
- Well-tested
- Easy to maintain

### 2. Functionality
- Core features working
- Essential requirements met
- Reliable operation

### 3. Performance
- Quick response
- Reliable execution
- Error recovery

## Remember

1. Start Simple:
   - Essential features first
   - Clear implementation
   - Direct flow

2. Stay Focused:
   - Core requirements
   - Must-have features
   - Clear testing

3. Build Quality:
   - Reliable code
   - Good error handling
   - Proper testing
