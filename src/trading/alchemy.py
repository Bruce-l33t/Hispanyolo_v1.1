"""
Alchemy RPC integration for transaction execution
Uses Jupiter API for swaps/quotes
"""
import base64
import logging
import asyncio
import requests
from typing import Dict, Optional
from solders.keypair import Keypair
from solders.transaction import VersionedTransaction

from ..config import (
    WSOL_ADDRESS, PRIORITY_FEE_LAMPORTS, MAX_RETRIES,
    RETRY_DELAY, CONFIRMATION_TIMEOUT
)
import dontshare as d

# Jupiter API endpoints
JUPITER_QUOTE_API = "https://quote-api.jup.ag/v6/quote"
JUPITER_SWAP_API = "https://quote-api.jup.ag/v6/swap"

class AlchemyTrader:
    """Handles token swaps through Jupiter and transaction execution through Alchemy"""
    def __init__(self):
        self.logger = logging.getLogger('alchemy_trader')
        self.keypair = Keypair.from_base58_string(d.sol_key)
        
    def get_jupiter_quote(
        self,
        token_address: str,
        amount_in: float,
        is_sell: bool = False,
        slippage: float = 0.01
    ) -> Optional[Dict]:
        """Get Jupiter quote for swap"""
        try:
            amount_lamports = int(amount_in * 1_000_000_000)  # Convert to lamports
            
            # For sells, swap from token to SOL
            input_mint = token_address if is_sell else WSOL_ADDRESS
            output_mint = WSOL_ADDRESS if is_sell else token_address
            
            params = {
                "inputMint": input_mint,
                "outputMint": output_mint,
                "amount": amount_lamports,
                "slippageBps": int(slippage * 10000),  # Convert to basis points
                "onlyDirectRoutes": "true",
                "asLegacyTransaction": "false",
                "prioritizationFeeLamports": PRIORITY_FEE_LAMPORTS
            }
            
            self.logger.debug(f"Getting Jupiter quote with params: {params}")
            
            response = requests.get(JUPITER_QUOTE_API, params=params)
            response.raise_for_status()
            
            quote = response.json()
            if not quote.get('routePlan'):
                self.logger.error("No valid route found in quote")
                return None
                
            self.logger.info(
                f"Quote received - Input: {quote['inAmount']} {'tokens' if is_sell else 'lamports'}, "
                f"Output: {quote['outAmount']} {'lamports' if is_sell else 'tokens'}, "
                f"Price impact: {quote.get('priceImpactPct', '0')}%"
            )
            return quote
            
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 400:
                self.logger.warning(f"Invalid quote request: {e.response.text}")
            else:
                self.logger.error(f"HTTP error getting quote: {str(e)}")
            return None
        except Exception as e:
            self.logger.error(f"Error getting quote: {str(e)}")
            return None
            
    async def execute_swap(
        self,
        token_address: str,
        amount_in: float,
        is_sell: bool = False,
        slippage: float = 0.01,
        max_retries: int = MAX_RETRIES
    ) -> Optional[str]:
        """Execute complete swap flow
        
        Args:
            token_address: Address of token to swap to/from
            amount_in: Amount to swap (in SOL for buys, in tokens for sells)
            is_sell: True if selling tokens for SOL, False if buying tokens with SOL
            slippage: Slippage tolerance (default: 1%)
            max_retries: Maximum retry attempts (default from config)
        """
        for attempt in range(max_retries):
            try:
                # 1. Get Jupiter quote
                quote = self.get_jupiter_quote(
                    token_address=token_address,
                    amount_in=amount_in,
                    is_sell=is_sell,
                    slippage=slippage
                )
                if not quote:
                    continue
                
                # 2. Get swap transaction
                swap_request = {
                    "quoteResponse": quote,
                    "userPublicKey": str(self.keypair.pubkey()),
                    "wrapUnwrapSOL": True,
                    "dynamicComputeUnitLimit": True,
                    "prioritizationFeeLamports": PRIORITY_FEE_LAMPORTS
                }
                
                self.logger.debug("Requesting swap transaction...")
                response = requests.post(
                    JUPITER_SWAP_API,
                    json=swap_request,
                    headers={"Content-Type": "application/json"}
                )
                response.raise_for_status()
                swap_response = response.json()
                
                # 3. Sign transaction
                tx = VersionedTransaction.from_bytes(
                    base64.b64decode(swap_response['swapTransaction'])
                )
                signed_tx = VersionedTransaction(tx.message, [self.keypair])
                
                # 4. Send via Alchemy RPC
                raw_tx = bytes(signed_tx)
                rpc_request = {
                    "jsonrpc": "2.0",
                    "id": 1,
                    "method": "sendTransaction",
                    "params": [
                        base64.b64encode(raw_tx).decode('utf-8'),
                        {
                            "encoding": "base64",
                            "skipPreflight": False,
                            "preflightCommitment": "confirmed",
                            "maxRetries": max_retries
                        }
                    ]
                }
                
                response = requests.post(
                    d.alchemy_url,
                    json=rpc_request,
                    headers={"Content-Type": "application/json"}
                )
                
                if response.status_code == 200:
                    tx_hash = response.json().get('result')
                    if tx_hash:
                        self.logger.info(f"Transaction sent: {tx_hash}")
                        
                        # 5. Wait for confirmation
                        if await self.confirm_transaction(tx_hash):
                            return tx_hash
                
            except Exception as e:
                self.logger.error(f"Swap attempt {attempt + 1} failed: {str(e)}")
                if attempt == max_retries - 1:
                    return None
                    
                await asyncio.sleep(RETRY_DELAY)
                continue
                
        return None
        
    async def confirm_transaction(
        self,
        signature: str,
        max_retries: int = CONFIRMATION_TIMEOUT,
        retry_delay: int = RETRY_DELAY
    ) -> bool:
        """Wait for transaction confirmation"""
        self.logger.debug(f"Waiting for confirmation: {signature}")
        
        try:
            for attempt in range(max_retries):
                try:
                    response = requests.post(
                        d.alchemy_url,
                        json={
                            "jsonrpc": "2.0",
                            "id": 1,
                            "method": "getSignatureStatuses",
                            "params": [[signature]]
                        },
                        headers={"Content-Type": "application/json"}
                    )
                    
                    if response.status_code == 200:
                        result = response.json().get('result', {})
                        if result and result.get('value'):
                            status = result['value'][0]
                            if status:
                                if status.get('err'):
                                    self.logger.error(f"Transaction failed: {status['err']}")
                                    return False
                                # Accept both confirmed and finalized status
                                conf_status = status.get('confirmationStatus')
                                if conf_status in ['confirmed', 'finalized']:
                                    self.logger.info(f"Transaction {conf_status}!")
                                    return True
                    
                    await asyncio.sleep(retry_delay)
                    
                except Exception as e:
                    self.logger.error(f"Error checking confirmation: {e}")
                    await asyncio.sleep(retry_delay)
            
            self.logger.error("Confirmation timeout")
            return False
            
        except Exception as e:
            self.logger.error(f"Error in confirmation process: {e}")
            return False
