"""
Utility functions for checking SOL balance
"""
import logging
import json
import requests
from solders.keypair import Keypair

import dontshare as d

async def get_sol_balance() -> float:
    """
    Get current SOL balance for our wallet
    Returns:
        float: Balance in SOL, or None if error
    """
    logger = logging.getLogger('sol_balance')
    
    # Get public key from private key
    keypair = Keypair.from_base58_string(d.sol_key)
    pubkey = str(keypair.pubkey())
    
    # Prepare RPC request
    rpc_request = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "getBalance",
        "params": [
            pubkey
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
        
        if 'result' in result:
            balance_lamports = int(result['result']['value'])
            balance_sol = balance_lamports / 1e9  # Convert lamports to SOL
            
            logger.debug(f"Current SOL balance: {balance_sol:.4f} SOL")
            return balance_sol
            
        else:
            logger.error(f"Unexpected response format: {json.dumps(result, indent=2)}")
            return None
            
    except Exception as e:
        logger.error(f"Error checking balance: {str(e)}")
        return None 