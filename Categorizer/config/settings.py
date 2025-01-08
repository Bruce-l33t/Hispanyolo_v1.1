"""
Configuration settings for the categorizer
"""
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# API Settings
BIRDEYE_SETTINGS = {
    "base_url": "https://public-api.birdeye.so",
    "endpoints": {
        "token_metadata": "/defi/v3/token/meta-data/single"
    },
    "headers": {
        "X-API-KEY": os.getenv("BIRDEYE_API_KEY"),
        "accept": "application/json",
        "x-chain": "solana"
    }
}

# Twitter Settings
TWITTER_SETTINGS = {
    "username": os.getenv("TWITTER_USERNAME"),
    "email": os.getenv("TWITTER_EMAIL"),
    "password": os.getenv("TWITTER_PASSWORD"),
    "min_tweets": 50,
    "ignore_words": [
        't.co', 'discord', 'join', 'telegram', 
        'discount', 'pay', 'airdrop', 'giveaway'
    ]
}

# LLM Settings
LLM_SETTINGS = {
    "api_key": os.getenv("OPENROUTER_API_KEY"),
    "model": "openai/gpt-3.5-turbo",
    "temperature": 0.3,
    "max_tokens": 500
}

# Categorization Settings
CATEGORIZATION = {
    "confidence_threshold": 0.7,
    "weights": {
        "metadata": 0.2,
        "twitter": 0.4,
        "llm": 0.4
    }
}

# Cache Settings
CACHE_SETTINGS = {
    "metadata_ttl": 3600,  # 1 hour
    "twitter_ttl": 1800,   # 30 minutes
    "max_size": 1000      # Maximum number of items to cache
} 