# Deployment Guide

## Server Requirements

- Ubuntu 22.04 LTS
- 2+ vCPUs
- 4GB+ RAM
- 50GB+ SSD
- Python 3.10+
- Node.js 18+

## Initial Setup

1. Clone the repository:
```bash
git clone https://github.com/Bruce-l33t/Hispanyolo_v1.git
cd Hispanyolo_v1
```

2. Create dontshare.py with your API keys:
```python
birdeye_api_key = "your_key_here"
alchemy_url = "your_url_here"
sol_key = "your_key_here"
```

3. Make setup script executable and run it:
```bash
chmod +x setup_server.sh
./setup_server.sh
```

## Managing the Application

The application runs using PM2 process manager.

### Common PM2 Commands

- View process status:
```bash
pm2 status
```

- View logs:
```bash
pm2 logs          # All logs
pm2 logs pirate-ui     # UI logs only
pm2 logs pirate-backend  # Backend logs only
```

- Restart processes:
```bash
pm2 restart all   # Restart all
pm2 restart pirate-ui  # Restart UI only
```

### System Health

Monitor system health:
```bash
./check_health.sh
```

### Updating the Application

1. Pull latest changes:
```bash
git pull origin main
```

2. Restart services:
```bash
pm2 restart all
```

## Troubleshooting

1. If the UI is not accessible:
- Check Nginx status: `sudo systemctl status nginx`
- Check UI logs: `pm2 logs pirate-ui`
- Verify port 8000 is not blocked: `sudo netstat -tulpn | grep 8000`

2. If the backend is not running:
- Check Python logs: `pm2 logs pirate-backend`
- Verify Python environment: `source venv/bin/activate`
- Check requirements: `pip install -r requirements.txt`

3. If WebSocket connections fail:
- Check Nginx error logs: `sudo tail -f /var/log/nginx/error.log`
- Verify WebSocket proxy settings in Nginx config

## Maintenance

1. Log Rotation
- PM2 logs are automatically rotated
- Nginx logs are rotated by logrotate
- Application logs in `logs/` should be monitored and cleaned periodically

2. Backups
- Regular backups of `dontshare.py` and any custom configurations
- Consider backing up the logs directory if needed

3. Updates
- Regularly update system packages: `sudo apt update && sudo apt upgrade`
- Keep Node.js and Python packages updated
- Monitor GitHub repository for updates
