#!/bin/bash

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo "Running system health check..."
echo "-----------------------------"

# Check if processes are running
echo -e "\n${YELLOW}Checking PM2 Processes:${NC}"
pm2 status

# Check memory usage
echo -e "\n${YELLOW}Memory Usage:${NC}"
free -h

# Check disk space
echo -e "\n${YELLOW}Disk Space:${NC}"
df -h /

# Check CPU usage
echo -e "\n${YELLOW}CPU Usage:${NC}"
top -bn1 | head -n 3

# Check Nginx status
echo -e "\n${YELLOW}Nginx Status:${NC}"
if systemctl is-active --quiet nginx; then
    echo -e "${GREEN}Nginx is running${NC}"
else
    echo -e "${RED}Nginx is not running${NC}"
fi

# Check port 8000 (UI server)
echo -e "\n${YELLOW}Checking UI Server Port (8000):${NC}"
if netstat -tuln | grep ":8000 "; then
    echo -e "${GREEN}UI Server is listening on port 8000${NC}"
else
    echo -e "${RED}UI Server is not listening on port 8000${NC}"
fi

# Check Python environment
echo -e "\n${YELLOW}Checking Python Environment:${NC}"
if [ -d "venv" ]; then
    echo -e "${GREEN}Python virtual environment exists${NC}"
else
    echo -e "${RED}Python virtual environment not found${NC}"
fi

# Check log files
echo -e "\n${YELLOW}Recent Log Activity:${NC}"
echo "Last 5 lines of backend logs:"
tail -n 5 logs/main_*.log 2>/dev/null || echo "No backend logs found"

# Check Node.js and npm versions
echo -e "\n${YELLOW}Node.js and npm versions:${NC}"
echo "Node.js: $(node --version)"
echo "npm: $(npm --version)"

# Check system load
echo -e "\n${YELLOW}System Load:${NC}"
uptime

echo -e "\n${YELLOW}Health check complete${NC}"
