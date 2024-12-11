#!/bin/bash

# Exit on error
set -e

echo "Starting server setup..."

# Update system
echo "Updating system packages..."
sudo apt-get update
sudo apt-get upgrade -y

# Install system dependencies
echo "Installing system dependencies..."
sudo apt-get install -y \
    python3.10 \
    python3.10-venv \
    python3-pip \
    nodejs \
    npm \
    nginx \
    git \
    build-essential \
    pkg-config \
    libudev-dev \
    libssl-dev

# Install PM2 globally
echo "Installing PM2..."
sudo npm install -g pm2

# Create Python virtual environment
echo "Setting up Python environment..."
python3.10 -m venv venv
source venv/bin/activate

# Install Python packages
echo "Installing Python requirements..."
pip install -r requirements.txt
pip install solders  # Install solders separately as it can be tricky

# Install Node.js dependencies
echo "Installing Node.js dependencies..."
npm install

# Setup PM2 processes
echo "Setting up PM2 processes..."
cat > ecosystem.config.js << EOL
module.exports = {
  apps: [
    {
      name: 'pirate-ui',
      script: 'pirate_ui/server.ts',
      interpreter: 'node',
      interpreter_args: '-r ts-node/register',
      env: {
        NODE_ENV: 'production'
      }
    },
    {
      name: 'pirate-backend',
      script: 'run.py',
      interpreter: './venv/bin/python',
      env: {
        PYTHONPATH: '.'
      }
    }
  ]
}
EOL

# Setup Nginx
echo "Setting up Nginx..."
sudo tee /etc/nginx/sites-available/pirate << EOL
server {
    listen 80;
    server_name _;  # Replace with your domain if you have one

    location / {
        proxy_pass http://localhost:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade \$http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host \$host;
        proxy_cache_bypass \$http_upgrade;
    }
}
EOL

# Enable Nginx site
sudo ln -s /etc/nginx/sites-available/pirate /etc/nginx/sites-enabled/
sudo rm /etc/nginx/sites-enabled/default
sudo systemctl restart nginx

# Start applications with PM2
echo "Starting applications..."
pm2 start ecosystem.config.js
pm2 save

echo "Setup complete! The system is now running."
echo "UI should be accessible on port 80 (http)"
echo "Monitor processes with: pm2 status"
echo "View logs with: pm2 logs"
