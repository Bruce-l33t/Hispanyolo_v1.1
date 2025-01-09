# System Monitoring Guide

This guide covers all aspects of monitoring the Hispanyolo Trading System in production.

## Quick Reference

### Essential Commands

Check system status:
```bash
ssh root@SERVER_IP "cd ~/Hispanyolo_v1 && pm2 status"
```

View application logs:
```bash
ssh root@SERVER_IP "cd ~/Hispanyolo_v1 && pm2 logs pirate-backend"
```

Check positions summary:
```bash
ssh root@SERVER_IP "cd ~/Hispanyolo_v1 && source venv/bin/activate && python3 src/position_manager.py --summary"
```

Check points log:
```bash
ssh root@SERVER_IP "cat ~/Hispanyolo_v1/logs/points.log"
```

Run health check:
```bash
ssh root@SERVER_IP "cd ~/Hispanyolo_v1 && ./check_health.sh"
```

## Monitoring Areas

### 1. Application Health

#### Process Status
```bash
pm2 status
```
Check for:
- Status: "online"
- Uptime
- CPU/Memory usage
- Restart count

#### Application Logs
```bash
pm2 logs pirate-backend
```
Monitor for:
- Error messages
- Warning signs
- Performance issues
- API rate limits

### 2. Trading Activity

#### Position Monitoring
```bash
source venv/bin/activate
python3 src/position_manager.py --check
```
Verify:
- Active positions
- Position sizes
- Entry/exit points
- Profit/loss status

#### Transaction History
- Check database entries
- Review recent trades
- Monitor success rate
- Track position lifecycle

### 3. System Resources

#### Server Health
```bash
./check_health.sh
```
Monitors:
- Disk space
- Memory usage
- CPU load
- Network connectivity

#### Database Status
- Check file size
- Monitor growth rate
- Verify permissions
- Check integrity

### 4. API Integration

#### Rate Limits
- Monitor usage
- Track remaining quota
- Check response times
- Handle throttling

#### Data Quality
- Verify price data
- Check transaction info
- Monitor wallet data
- Validate token info

## Alert Conditions

### Critical Alerts
1. Application crash
2. Database errors
3. API failures
4. Position errors
5. Server resource exhaustion

### Warning Alerts
1. High memory usage
2. Increased error rate
3. API rate limit approaching
4. Unusual trading patterns
5. Performance degradation

## Regular Checks

### Daily Tasks
1. Check application status
2. Review active positions
3. Monitor error logs
4. Verify API health

### Weekly Tasks
1. Review performance metrics
2. Check resource usage
3. Backup database
4. Update documentation

### Monthly Tasks
1. System updates
2. Performance review
3. Strategy adjustment
4. Resource planning

## Troubleshooting

### Common Issues

1. Application Crashes
- Check error logs
- Verify configuration
- Review recent changes
- Check system resources

2. API Issues
- Verify credentials
- Check rate limits
- Monitor response times
- Review error messages

3. Trading Problems
- Check position status
- Verify wallet balance
- Review trade logic
- Check market conditions

## Maintenance Procedures

### Routine Maintenance
1. Log rotation
2. Database cleanup
3. Configuration backup
4. System updates

### Emergency Procedures
1. Application restart
2. Position emergency exit
3. API failover
4. System recovery

## Documentation

Keep records of:
1. System changes
2. Performance metrics
3. Incident reports
4. Configuration updates

## Contact Information

For critical issues:
1. System administrator
2. Development team
3. API support
4. Infrastructure team 