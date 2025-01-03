# Deployment Guide

This guide details the process of deploying the Hispanyolo Trading System to a production server.

## Server Requirements

- Ubuntu 22.04 or later
- Python 3.12
- Node.js 18+ (for PM2)
- 2GB RAM minimum
- 20GB storage minimum

## Initial Server Setup

1. Update system packages:
```bash
sudo apt update
sudo apt upgrade -y
```

2. Install system dependencies:
```bash
sudo apt install -y git python3.12 python3.12-venv python3.12-dev build-essential
```

3. Install Node.js and PM2:
```bash
curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash -
sudo apt install -y nodejs
sudo npm install -g pm2
```

## Application Deployment

1. Clone the repository:
```bash
cd ~
git clone https://github.com/your-username/Hispanyolo_v1.git
cd Hispanyolo_v1
```

2. Set up Python environment:
```bash
python3.12 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

3. Configure the application:
- Copy configuration template:
  ```bash
  cp dontshare.py.example dontshare.py
  ```
- Edit configuration:
  ```bash
  nano dontshare.py
  ```
  Add your API keys and settings

4. Start the application:
```bash
pm2 start ecosystem.config.js
```

## Monitoring and Maintenance

### Check Application Status
```bash
pm2 status
pm2 logs pirate-backend
```

### Check Positions
```bash
cd ~/Hispanyolo_v1
source venv/bin/activate
python3 src/position_manager.py --check
```

### Server Health Check
```bash
./check_health.sh
```

## Updating the Application

1. Pull latest changes:
```bash
cd ~/Hispanyolo_v1
git pull
```

2. Update dependencies:
```bash
source venv/bin/activate
pip install -r requirements.txt
```

3. Restart the application:
```bash
pm2 restart pirate-backend
```

## Troubleshooting

### Common Issues

1. Application not starting:
- Check PM2 logs: `pm2 logs`
- Verify Python environment: `which python`
- Check configuration file

2. Database errors:
- Check file permissions
- Verify database exists
- Check disk space

3. API connection issues:
- Verify API keys in configuration
- Check network connectivity
- Review rate limits

### Log Locations

- Application logs: `~/Hispanyolo_v1/logs/`
- PM2 logs: `~/.pm2/logs/`
- System logs: `/var/log/syslog`

## Backup and Recovery

1. Database backup:
```bash
cp ~/Hispanyolo_v1/positions.db ~/Hispanyolo_v1/positions.db.backup
```

2. Configuration backup:
```bash
cp ~/Hispanyolo_v1/dontshare.py ~/Hispanyolo_v1/dontshare.py.backup
```

## Security Considerations

1. Server access:
- Use SSH key authentication
- Disable password authentication
- Use UFW firewall

2. Application security:
- Keep API keys secure
- Regular security updates
- Monitor system access

## Support

For issues or questions:
1. Check the logs
2. Review documentation
3. Contact system administrator 