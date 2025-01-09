import sys
import os
import asyncio
import logging
import json
import requests
from pathlib import Path
from solders.keypair import Keypair

# Add the project root to the Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

import dontshare as d
from src.config import WSOL_ADDRESS

async def test_sol_balance():
    """Test SOL balance check via Alchemy RPC"""
    logging.basicConfig(level=logging.DEBUG)
    logger = logging.getLogger('test')
    
    logger.info("Testing SOL balance check...")
    
    # Get public key from private key
    keypair = Keypair.from_base58_string(d.sol_key)
    pubkey = str(keypair.pubkey())
    logger.debug(f"Using public key: {pubkey}")
    
    # Prepare RPC request
    rpc_request = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "getBalance",
        "params": [
            pubkey  # Our wallet public key
        ]
    }
    
    try:
        # Make RPC call
        response = requests.post(
            d.alchemy_url,
            json=rpc_request,
            headers={"Content-Type": "application/json"}
        )
        response.raise_for_status()
        
        # Parse response
        result = response.json()
        logger.debug(f"Raw response: {json.dumps(result, indent=2)}")
        
        if 'result' in result:
            balance_lamports = int(result['result']['value'])  # Extract value from result
            balance_sol = balance_lamports / 1e9  # Convert lamports to SOL
            
            logger.info(f"Current SOL balance: {balance_sol:.4f} SOL")
            logger.info(f"Raw balance in lamports: {balance_lamports}")
            
            # Basic validation
            assert balance_sol >= 0, "Balance should not be negative"
            assert isinstance(balance_lamports, int), "Lamports should be an integer"
            
            return balance_sol
            
        else:
            logger.error(f"Unexpected response format: {json.dumps(result, indent=2)}")
            return None
            
    except Exception as e:
        logger.error(f"Error checking balance: {str(e)}")
        logger.error(f"Response data: {response.text if 'response' in locals() else 'No response'}")
        return None

if __name__ == "__main__":
    # Run the test
    balance = asyncio.run(test_sol_balance())
    if balance is not None:
        print(f"\nTest passed! Current balance: {balance:.4f} SOL") 