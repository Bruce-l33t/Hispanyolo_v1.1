"""
Test Birdeye metadata API responses for specific tokens
"""
import logging
import json
import requests
import sys
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

import dontshare as d
from src.monitor.categorizer import TokenCategorizer

# Setup logging
logging.basicConfig(
    level=logging.DEBUG,  # Changed to DEBUG for more info
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('metadata_test')

# Test tokens
TEST_TOKENS = {
    "7h5AzpYTAnh4Gyux8Gqko5Fvx4AYQBZdkzHZ2CsBudvJ": "Citadail",
    "DKu9kykSfbN5LBfFXtNNDPaX35o4Fv6vJ9FKk7pZpump": "AVA",
    "oraim8c9d1nkfuQk9EzGYEUGxqL3MHQYndRw1huVo5h": "MAX"
}

def test_single_metadata():
    """Test single token metadata endpoint"""
    url = "https://public-api.birdeye.so/defi/v3/token/meta-data/single"
    headers = {
        "X-API-KEY": d.birdeye_api_key,
        "accept": "application/json",
        "x-chain": "solana"  # Required header
    }
    
    for address, symbol in TEST_TOKENS.items():
        logger.info(f"\nTesting metadata for {symbol} ({address}):")
        logger.info(f"URL: {url}")
        
        try:
            response = requests.get(url, headers=headers, params={"address": address})
            logger.info(f"Status Code: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                logger.info("\nRaw Response:")
                logger.info(json.dumps(data, indent=2))
                
                # Check success field
                success = data.get('success', False)
                logger.info(f"\nSuccess: {success}")
                
                # Check data field
                if 'data' in data:
                    metadata = data['data']
                    logger.info("\nKey metadata fields:")
                    logger.info(f"Name: {metadata.get('name', 'N/A')}")
                    logger.info(f"Symbol: {metadata.get('symbol', 'N/A')}")
                    logger.info(f"Decimals: {metadata.get('decimals', 'N/A')}")
                    
                    # Check extensions
                    extensions = metadata.get('extensions', {})
                    if extensions:
                        logger.info("\nExtensions:")
                        logger.info(f"Description: {extensions.get('description', 'N/A')}")
                        logger.info(f"Twitter: {extensions.get('twitter', 'N/A')}")
                        logger.info(f"Website: {extensions.get('website', 'N/A')}")
                else:
                    logger.error("No data field in response")
            else:
                logger.error(f"Error response: {response.text}")
                
        except Exception as e:
            logger.error(f"Error testing metadata endpoint: {str(e)}")
            logger.error("Full traceback:", exc_info=True)

def test_multiple_metadata():
    """Test multiple tokens metadata endpoint"""
    url = "https://public-api.birdeye.so/defi/v3/token/meta-data/multiple"
    headers = {
        "X-API-KEY": d.birdeye_api_key,
        "accept": "application/json",
        "x-chain": "solana"  # Required header
    }
    
    # Create comma-separated list of addresses
    addresses = ",".join(TEST_TOKENS.keys())
    
    logger.info("\nTesting multiple tokens metadata endpoint:")
    logger.info(f"URL: {url}")
    
    try:
        response = requests.get(url, headers=headers, params={"list_address": addresses})
        logger.info(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            logger.info("\nRaw Response:")
            logger.info(json.dumps(data, indent=2))
            
            # Check each token
            if 'data' in data:
                for address, symbol in TEST_TOKENS.items():
                    if address in data['data']:
                        metadata = data['data'][address]
                        logger.info(f"\nMetadata for {symbol}:")
                        logger.info(f"Name: {metadata.get('name', 'N/A')}")
                        logger.info(f"Symbol: {metadata.get('symbol', 'N/A')}")
                        logger.info(f"Decimals: {metadata.get('decimals', 'N/A')}")
                    else:
                        logger.error(f"No metadata found for {symbol}")
            else:
                logger.error("No data field in response")
        else:
            logger.error(f"Error response: {response.text}")
            
    except Exception as e:
        logger.error(f"Error testing multiple endpoint: {str(e)}")
        logger.error("Full traceback:", exc_info=True)

def test_categorization():
    """Test token categorization"""
    logger.info("\nTesting token categorization:")
    categorizer = TokenCategorizer()
    
    for address, symbol in TEST_TOKENS.items():
        logger.info(f"\nCategorizing {symbol} ({address}):")
        
        # Get metadata first to see what we're working with
        metadata = categorizer.get_token_metadata(address)
        if metadata:
            logger.info("Got metadata successfully")
            logger.debug(f"Raw metadata: {json.dumps(metadata, indent=2)}")
        else:
            logger.error("Failed to get metadata")
            continue
            
        # Try categorization
        category, confidence = categorizer.categorize_token(address, symbol)
        logger.info(f"Category: {category}")
        logger.info(f"Confidence: {confidence}")

if __name__ == "__main__":
    logger.info("Starting metadata tests...")
    
    try:
        # Test single token endpoint
        test_single_metadata()
        
        # Test multiple tokens endpoint
        test_multiple_metadata()
        
        # Test categorization
        test_categorization()
        
        logger.info("\n✅ Tests completed!")
        
    except Exception as e:
        logger.error(f"\n❌ Tests failed: {str(e)}")
        sys.exit(1) 