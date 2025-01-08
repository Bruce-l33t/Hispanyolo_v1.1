# Logging Reference Guide

## Quick Access Commands

### Main System Logs (PM2)
```bash
# View last 100 lines of main system logs
pm2 logs pirate-backend --lines 100 | cat

# Follow main logs in real-time
pm2 logs pirate-backend
```

### Points Activity Log
```bash
# View entire points log
cat ~/Hispanyolo_v1/logs/points.log

# Follow points activity in real-time
tail -f ~/Hispanyolo_v1/logs/points.log

# View last 50 points updates
tail -n 50 ~/Hispanyolo_v1/logs/points.log
```

## Log Types and Locations

1. **System Logs** (PM2)
   - Location: `~/.pm2/logs/pirate-backend-out.log`
   - Contains: All system activity, transactions, status updates
   - Access: Use PM2 commands above

2. **Points Activity Log**
   - Location: `~/Hispanyolo_v1/logs/points.log`
   - Contains: Only token score updates and buy activity
   - Format: Clean output showing token scores and point additions
   - Example:
     ```
     AVA: 44.00 points
     hfjdls7s bought 22.00 SOL: +14.00 points
     ```

3. **Error Logs** (PM2)
   - Location: `~/.pm2/logs/pirate-backend-error.log`
   - Contains: System errors and warnings
   - Access: `pm2 logs pirate-backend --err | cat`

## Common Use Cases

1. **Monitor System Health**
   ```bash
   # Check recent system activity
   pm2 logs pirate-backend --lines 50 | cat
   ```

2. **Track Points/Buys**
   ```bash
   # Follow points activity
   tail -f ~/Hispanyolo_v1/logs/points.log
   ```

3. **Debug Issues**
   ```bash
   # Check error logs
   pm2 logs pirate-backend --err --lines 100 | cat
   ```

4. **Clear Logs**
   ```bash
   # Clear PM2 logs
   pm2 flush

   # Clear points log
   > ~/Hispanyolo_v1/logs/points.log
   ```

## Tips

1. Use `| cat` with PM2 commands to prevent paging
2. Use `--lines N` to limit output
3. Use `tail -f` for real-time monitoring
4. All times in logs are in UTC 