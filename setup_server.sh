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
    python3.12 \
    python3.12-venv \
    python3-pip \
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
python3.12 -m venv venv
source venv/bin/activate

# Install Python packages
echo "Installing Python requirements..."
pip install -r requirements.txt
pip install solders  # Install solders separately as it can be tricky

# Setup PM2 processes
echo "Setting up PM2 processes..."
cat > ecosystem.config.js << EOL
module.exports = {
  apps: [
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

# Start applications with PM2
echo "Starting applications..."
pm2 start ecosystem.config.js
pm2 save

echo "Setup complete! The system is now running."
echo "Monitor processes with: pm2 status"
echo "View logs with: pm2 logs"
