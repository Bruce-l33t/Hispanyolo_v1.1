# Practical Implementation Guide

## Data Structures & Formats

### 1. Birdeye API Responses
```python
# Transaction List Response
{
    "data": {
        "solana": [
            {
                "blockTime": "2024-01-01T00:00:00Z",
                "balanceChange": [
                    {
                        "address": "token_address",
                        "amount": "1000000000",  # Raw amount
                        "decimals": 9,
                        "symbol": "TOKEN"
                    }
                ]
            }
        ]
    }
}

# Token Metadata Response
{
    "data": {
        "name": "Token Name",
        "symbol": "TOKEN",
        "extensions": {
            "description": "Token description"
        }
    }
}
```

### 2. System State
```python
# Wallet Status
class WalletTier:
    def __init__(self):
        self.status = WalletStatus.WATCHING
        self.last_active = datetime.now(timezone.utc)
        self.transaction_count = 0
        self.score = 0.0

# Token Metrics
class TokenMetrics:
    def __init__(self):
        self.symbol = ""
        self.score = 0.0
        self.category = ""
        self.confidence = 0.0
        self.buy_count = 0
        self.sell_count = 0
        self.total_volume = 0.0
        self.unique_buyers = set()
        self.recent_changes = []
```

## Critical Configurations

### 1. System Parameters
```python
# Thresholds
MIN_SOL_AMOUNT = 0.1
MAX_POSITIONS = 10
MAX_AI_POSITIONS = 8
MAX_MEME_POSITIONS = 2

# Timeouts
API_TIMEOUT = 10  # seconds
RETRY_DELAY = 2   # seconds
MAX_RETRIES = 3

# Score Thresholds
SCORE_THRESHOLDS = {
    'AI': 80,
    'MEME': 150,
    'HYBRID': 80
}

# Position Sizes
POSITION_SIZES = {
    'AI': 0.05,      # SOL
    'MEME': 0.025,   # SOL
    'HYBRID': 0.05   # SOL
}
```

### 2. API Settings
```python
# Birdeye
BIRDEYE_SETTINGS = {
    "base_url": "https://public-api.birdeye.so",
    "endpoints": {
        "tx_list": "/v1/wallet/tx_list",
        "token_metadata": "/defi/v3/token/meta-data/single"
    },
    "headers": {
        "X-API-KEY": "your_key",
        "accept": "application/json"
    }
}

# Alchemy
ALCHEMY_SETTINGS = {
    "network": "mainnet-beta",
    "commitment": "confirmed",
    "timeout": 30
}
```

## Initialization Flow

### 1. System Startup
```python
async def main():
    # 1. Setup logging
    setup_logging()
    
    # 2. Initialize APIs
    birdeye = BirdeyeClient()
    alchemy = AlchemyTrader()
    
    # 3. Create components
    monitor = WalletMonitor(birdeye)
    trading = TradingSystem(alchemy)
    
    # 4. Setup event handlers
    await setup_events(monitor, trading)
    
    # 5. Start UI server
    ui_server = await start_ui_server()
    
    # 6. Start monitoring
    await monitor.start()
```

### 2. Component Setup
```python
async def setup_events(monitor, trading):
    # Trading signals
    await event_bell.subscribe(
        'trading_signal',
        trading.handle_signal
    )
    
    # System updates
    await event_bell.subscribe(
        'system_update',
        ui_server.handle_update
    )
```

## Error Recovery

### 1. API Errors
```python
async def handle_api_error(e: Exception, context: str):
    if isinstance(e, RateLimitError):
        # Wait and retry
        await asyncio.sleep(RETRY_DELAY)
        return True
        
    if isinstance(e, TimeoutError):
        # Retry with increased timeout
        return True
        
    if isinstance(e, ConnectionError):
        # Wait longer and retry
        await asyncio.sleep(RETRY_DELAY * 2)
        return True
        
    # Log unhandled error
    logger.error(f"Error in {context}: {e}")
    return False
```

### 2. State Recovery
```python
async def recover_state():
    # 1. Check component health
    monitor_health = await check_monitor()
    trading_health = await check_trading()
    
    # 2. Reload necessary data
    if not monitor_health:
        await reload_monitor_state()
    
    if not trading_health:
        await reload_trading_state()
    
    # 3. Verify system state
    await verify_system_state()
```

## WebSocket Implementation

### 1. Server Side
```python
class UIServer:
    def __init__(self):
        self.active_connections = []
        self.current_state = {
            "token_metrics": {},
            "wallet_status": {
                "VERY_ACTIVE": 0,
                "ACTIVE": 0,
                "WATCHING": 0,
                "ASLEEP": 0
            },
            "wallets_checked": 0,
            "transactions_processed": 0,
            "recent_transactions": [],
            "positions": {},
            "signal_history": [],
            "start_time": None
        }
    
    async def handle_connection(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)
        await self.send_state(websocket)
        
    async def broadcast_update(self, update: dict):
        self.current_state.update(update)
        await self.broadcast_state()
```

### 2. Client Side
```javascript
class WebSocketClient {
    constructor() {
        this.connect();
        this.reconnectAttempts = 0;
    }
    
    connect() {
        this.ws = new WebSocket('ws://localhost:8000/ws');
        this.ws.onmessage = this.handleMessage;
        this.ws.onclose = this.handleClose;
        this.ws.onerror = this.handleError;
    }
    
    handleClose = () => {
        setTimeout(() => this.connect(), 1000);
    }
}
```

## Testing Strategy

### 1. Component Tests
```python
async def test_monitor():
    monitor = WalletMonitor(mock_birdeye)
    
    # Test transaction processing
    tx = create_test_transaction()
    await monitor.process_transaction(tx)
    
    # Verify metrics
    metrics = monitor.token_metrics.get(tx.token)
    assert metrics.score > 0
```

### 2. Integration Tests
```python
async def test_system_flow():
    # 1. Setup test system
    system = TestSystem()
    
    # 2. Inject test transaction
    await system.inject_transaction(test_tx)
    
    # 3. Verify flow
    assert system.signals_received
    assert system.trades_executed
    assert system.ui_updated
```

## Monitoring & Debugging

### 1. System Metrics
```python
class SystemMetrics:
    def __init__(self):
        self.api_calls = Counter()
        self.api_errors = Counter()
        self.signal_count = Counter()
        self.trade_count = Counter()
        
    def track_api_call(self, api: str, success: bool):
        self.api_calls[api] += 1
        if not success:
            self.api_errors[api] += 1
```

### 2. Debug Logging
```python
def setup_logging():
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler('debug.log'),
            logging.StreamHandler()
        ]
    )
```

## Performance Optimization

### 1. Caching
```python
class MetadataCache:
    def __init__(self):
        self.cache = {}
        self.ttl = 3600  # 1 hour
        
    async def get(self, token: str):
        if token in self.cache:
            entry = self.cache[token]
            if time.time() - entry['time'] < self.ttl:
                return entry['data']
        return None
```

### 2. Batch Processing
```python
async def process_wallets(wallets: List[str]):
    chunks = [wallets[i:i+10] for i in range(0, len(wallets), 10)]
    for chunk in chunks:
        tasks = [process_wallet(w) for w in chunk]
        await asyncio.gather(*tasks)
```

## Deployment Considerations

### 1. Environment Setup
```python
# Required environment variables
REQUIRED_ENV = [
    'BIRDEYE_API_KEY',
    'ALCHEMY_API_KEY',
    'LOG_LEVEL',
    'MAX_POSITIONS',
    'MIN_SOL_AMOUNT'
]

# Verify environment
for var in REQUIRED_ENV:
    if var not in os.environ:
        raise EnvironmentError(f"Missing {var}")
```

### 2. Health Checks
```python
async def health_check():
    checks = {
        'birdeye': await check_birdeye(),
        'alchemy': await check_alchemy(),
        'monitor': await check_monitor(),
        'trading': await check_trading(),
        'websocket': await check_websocket()
    }
    return all(checks.values()), checks
