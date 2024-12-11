# Wallet Monitoring System

## Overview

The wallet monitoring system tracks wallets with different monitoring frequencies based on their activity level. Wallets are never removed from the system, they just get checked at different intervals based on their status.

## Status Levels

### VERY_ACTIVE
- Recent activity within 15 minutes
- Checked every 30 seconds
- High priority monitoring
- Example: Wallet actively trading

### ACTIVE
- Activity within last hour
- Checked every 3 minutes
- Regular monitoring
- Example: Wallet with recent trades

### WATCHING
- Activity within last 4 hours
- Checked every hour
- Reduced monitoring
- Example: Wallet with occasional activity

### ASLEEP
- No activity for over 4 hours
- Checked every 4 hours
- Minimal monitoring
- Example: Wallet with infrequent activity

## Monitoring Architecture

### Separate Monitoring Tasks
```python
# Active wallets monitor (30 sec interval)
async def monitor_active_wallets():
    while is_running:
        active_wallets = get_active_wallets()
        await process_wallets(active_wallets)
        await asyncio.sleep(30)

# Watching wallets monitor (1 hour interval)
async def monitor_watching_wallets():
    while is_running:
        watching_wallets = get_watching_wallets()
        await process_wallets(watching_wallets)
        await asyncio.sleep(3600)

# Asleep wallets monitor (4 hour interval)
async def monitor_asleep_wallets():
    while is_running:
        asleep_wallets = get_asleep_wallets()
        await process_wallets(asleep_wallets)
        await asyncio.sleep(14400)
```

### Status Transitions
- Wallets move between statuses based on activity time
- More active = More frequent checks
- Less active = Less frequent checks
- Any activity immediately upgrades status

### Batch Processing
- Wallets processed in batches to manage load
- Small delays between batches for rate limiting
- Different batch sizes for different statuses

## Implementation Details

### Status Updates
```python
# Update status based on activity time
if time_diff <= timedelta(minutes=15):
    status = WalletStatus.VERY_ACTIVE
elif time_diff <= timedelta(hours=1):
    status = WalletStatus.ACTIVE
elif time_diff <= timedelta(hours=4):
    status = WalletStatus.WATCHING
else:
    status = WalletStatus.ASLEEP
```

### Monitoring Flow
1. Each status type has its own monitoring loop
2. Loops run independently on different schedules
3. Any wallet can become active at any time
4. Status changes affect which loop monitors the wallet

### Error Handling
- Each monitoring task handles errors independently
- Failed checks are retried with backoff
- Errors don't affect other monitoring tasks
- System maintains state through errors

## Key Points

### 1. Never Delete Wallets
- Wallets stay in the system indefinitely
- Status changes control monitoring frequency
- Any wallet can become active again

### 2. Independent Monitoring
- Separate tasks for each status type
- Different check intervals
- Rate limiting per task
- Error isolation

### 3. Dynamic Status
- Status based on activity time
- Immediate upgrade on activity
- Gradual downgrade on inactivity
- Continuous monitoring

## Example Scenarios

### 1. Active Trading
```python
# Wallet makes a trade
status = VERY_ACTIVE  # Checked every 30 seconds
# No activity for 30 minutes
status = ACTIVE      # Checked every 3 minutes
```

### 2. Occasional Trading
```python
# Wallet inactive for 2 hours
status = WATCHING    # Checked every hour
# Makes a trade
status = VERY_ACTIVE # Back to 30-second checks
```

### 3. Infrequent Trading
```python
# Wallet inactive for 5 hours
status = ASLEEP     # Checked every 4 hours
# Makes a trade
status = VERY_ACTIVE # Immediately back to 30-second checks
```

## Maintenance

### Status Updates
- Regular status checks
- Update based on last activity
- Maintain monitoring frequency
- Track wallet metrics

### Rate Limiting
- Delays between batches
- Different delays per status
- Backoff on errors
- API friendly

### Error Recovery
- Independent task recovery
- State preservation
- Continuous operation
- Graceful degradation
