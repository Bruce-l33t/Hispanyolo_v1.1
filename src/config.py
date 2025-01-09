"""
Core configuration settings
"""
from pathlib import Path

# Token addresses
WSOL_ADDRESS = "So11111111111111111111111111111111111111112"
USDC_ADDRESS = "EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v"

# Ignored tokens (e.g. LP tokens)
IGNORED_TOKENS = set([
    "EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v",  # USDC
    "So11111111111111111111111111111111111111112",   # WSOL
])

# Monitoring settings
BASE_CHECK_INTERVAL = 300  # 5 minutes
MIN_SOL_AMOUNT = 0.1      # Minimum SOL amount to track

# Trading Rules
SCORE_THRESHOLDS = {
    'AI': 80,
    'MEME': 150,
    'HYBRID': 80
}

POSITION_SIZES = {
    'AI': 1.0,      # SOL
    'MEME': 0.25,   # SOL
    'HYBRID': 1.0   # SOL
}

# Position limits
MAX_POSITIONS = 10
MAX_AI_POSITIONS = 8
MAX_MEME_POSITIONS = 2

# Profit taking levels
PROFIT_LEVELS = [
    {'increase': 0.6, 'sell_portion': 0.50},  # 60% up, sell 50%
    {'increase': 1.2, 'sell_portion': 0.25},  # 120% up, sell 25%
    {'increase': 1.8, 'sell_portion': 0.25},  # 180% up, sell 25%
    {'increase': 2.4, 'sell_portion': 0.25},  # 240% up, sell 25%
    {'increase': 4.2, 'sell_portion': 0.25},  # 420% up, sell 25%
    {'increase': 8.88, 'sell_portion': 0.25}, # 888% up, sell 25%
    {'increase': 10.0, 'sell_portion': 0.50}  # 1000% up, sell remaining 50%
]

# Transaction settings
PRIORITY_FEE_LAMPORTS = 250_000   # 0.00025 SOL priority fee
MAX_RETRIES = 3                   # Maximum retry attempts
RETRY_DELAY = 1                   # Delay between retries (seconds)
CONFIRMATION_TIMEOUT = 30         # Transaction confirmation timeout (seconds)

# Test settings
TEST_SETTINGS = {
    'token_address': '8i51XNNpGaKaj4G4nDdmQh95v4FKAxw8mhtaRoKd9tE8',
    'amount': 0.001,               # Test amount in SOL
    'slippage': 0.01,             # 1% slippage for tests
    'priority_fee': 250_000,       # 0.00025 SOL priority fee for tests
    'max_retries': 3,             # Test retry attempts
    'retry_delay': 1,             # Test retry delay
    'confirmation_timeout': 30     # Test confirmation timeout
}

# Birdeye API settings
BIRDEYE_SETTINGS = {
    'base_url': 'https://public-api.birdeye.so',
    'endpoints': {
        'token_metadata_single': '/defi/v3/token/meta-data/single',  # Single token endpoint
        'token_metadata_multiple': '/defi/v3/token/meta-data/multiple',  # Multiple tokens endpoint
        'token_price': '/v1/token/price',
        'token_info': '/v1/token/info',
        'tx_list': '/v1/wallet/tx_list'
    },
    'headers': {
        'Content-Type': 'application/json',
        'User-Agent': 'Mozilla/5.0'
    }
}

# Alchemy API settings
ALCHEMY_SETTINGS = {
    'base_url': 'https://api.alchemy.com/v2',
    'endpoints': {
        'swap_quote': '/swap/v1/quote',
        'swap_build': '/swap/v1/build',
        'tx_send': '/v2/transaction/send',
        'tx_status': '/v2/transaction'
    },
    'headers': {
        'Content-Type': 'application/json',
        'User-Agent': 'Mozilla/5.0'
    }
}
