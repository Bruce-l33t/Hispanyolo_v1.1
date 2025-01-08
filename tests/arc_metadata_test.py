"""
Test script for Birdeye metadata API using ARC token
"""
import requests
import logging
import json
from pathlib import Path
import sys

# Add project root to path for imports
project_root = str(Path(__file__).parent.absolute())
sys.path.insert(0, project_root)

from dontshare import birdeye_api_key

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# ARC token address
ARC_ADDRESS = "61V8vBaqAGMpgDQi4JcAwo1dmBGHsyhzodcPqnEVpump"  # AI Rig Complex

def test_single_metadata():
    """Test single token metadata endpoint with ARC"""
    url = "https://public-api.birdeye.so/defi/v3/token/meta-data/single"
    headers = {
        "X-API-KEY": birdeye_api_key,
        "accept": "application/json",
        "x-chain": "solana"  # Required header
    }
    params = {"address": ARC_ADDRESS}
    
    logger.info("\nTesting single token metadata endpoint for ARC:")
    logger.info(f"URL: {url}")
    logger.info(f"Token Address: {ARC_ADDRESS}")
    
    try:
        response = requests.get(url, headers=headers, params=params)
        logger.info(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            logger.info("\nARC Token Metadata:")
            logger.info(json.dumps(data, indent=2))
            
            # Verify required fields
            if 'data' in data:
                metadata = data['data']
                logger.info("\nKey metadata fields:")
                logger.info(f"Name: {metadata.get('name', 'N/A')}")
                logger.info(f"Symbol: {metadata.get('symbol', 'N/A')}")
                logger.info(f"Decimals: {metadata.get('decimals', 'N/A')}")
                logger.info(f"Price USD: {metadata.get('priceUsd', 'N/A')}")
                logger.info(f"Volume 24h: {metadata.get('volume24h', 'N/A')}")
            else:
                logger.error("No data field in response")
        else:
            logger.error(f"Error response: {response.text}")
            
    except Exception as e:
        logger.error(f"Error testing metadata endpoint: {str(e)}")

def test_multiple_metadata():
    """Test multiple tokens metadata endpoint with ARC"""
    url = "https://public-api.birdeye.so/defi/v3/token/meta-data/multiple"
    headers = {
        "X-API-KEY": birdeye_api_key,
        "accept": "application/json",
        "x-chain": "solana"  # Required header
    }
    params = {"list_address": ARC_ADDRESS}  # Can add more addresses with commas
    
    logger.info("\nTesting multiple tokens metadata endpoint for ARC:")
    logger.info(f"URL: {url}")
    
    try:
        response = requests.get(url, headers=headers, params=params)
        logger.info(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            logger.info("\nMultiple Tokens Response:")
            logger.info(json.dumps(data, indent=2))
            
            # Verify ARC data
            if 'data' in data and ARC_ADDRESS in data['data']:
                metadata = data['data'][ARC_ADDRESS]
                logger.info("\nARC Token Metadata from multiple endpoint:")
                logger.info(f"Name: {metadata.get('name', 'N/A')}")
                logger.info(f"Symbol: {metadata.get('symbol', 'N/A')}")
                logger.info(f"Decimals: {metadata.get('decimals', 'N/A')}")
                logger.info(f"Price USD: {metadata.get('priceUsd', 'N/A')}")
                logger.info(f"Volume 24h: {metadata.get('volume24h', 'N/A')}")
            else:
                logger.error("ARC token data not found in response")
        else:
            logger.error(f"Error response: {response.text}")
            
    except Exception as e:
        logger.error(f"Error testing multiple endpoint: {str(e)}")

if __name__ == "__main__":
    logger.info("Starting ARC token metadata tests...")
    
    try:
        # Test single token endpoint
        test_single_metadata()
        
        # Test multiple tokens endpoint
        test_multiple_metadata()
        
        logger.info("\n✅ Tests completed!")
        
    except Exception as e:
        logger.error(f"\n❌ Tests failed: {str(e)}")
        sys.exit(1) 