# Hispanyolo Trading System

A sophisticated trading system for monitoring and acting on whale wallet activity in the Solana ecosystem.

## System Overview

The system consists of several core components:

1. **Wallet Monitoring**
   - Tracks high-value wallet activity
   - Uses scoring system to identify significant wallets
   - Real-time transaction monitoring

2. **Trading System**
   - Automated position management
   - Dynamic take-profit levels
   - Risk management controls

3. **Token Metrics**
   - Token categorization
   - Volume tracking
   - Price impact analysis

## Key Features

- Real-time whale wallet monitoring
- Automated trading based on whale activity
- Dynamic position management
- Multi-level take-profit system
- Token categorization and scoring
- Comprehensive logging and monitoring

## Getting Started

### Prerequisites
- Python 3.12
- Node.js (for PM2)
- Git

### Installation

1. Clone the repository:
```bash
git clone https://github.com/your-username/Hispanyolo_v1.git
cd Hispanyolo_v1
```

2. Set up Python environment:
```bash
python3.12 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

3. Install PM2:
```bash
npm install -g pm2
```

4. Configure settings:
- Copy `dontshare.py.example` to `dontshare.py`
- Add your API keys and configuration

### Deployment

See [DEPLOYMENT.md](setup/DEPLOYMENT.md) for detailed deployment instructions.

## System Monitoring

### Check System Status
```bash
pm2 status
pm2 logs
```

### Check Positions
```bash
source venv/bin/activate
python3 src/position_manager.py --check
```

## Documentation

- [Setup Guide](setup/INSTALLATION.md)
- [System Architecture](architecture/SYSTEM_OVERVIEW.md)
- [Operations Guide](operations/MONITORING.md)
- [Development Guide](development/API_INTEGRATION.md)

## Future Development

See [FUTURE_IMPROVEMENTS.md](roadmap/FUTURE_IMPROVEMENTS.md) for upcoming features and improvements.

## License

Proprietary software. All rights reserved.
