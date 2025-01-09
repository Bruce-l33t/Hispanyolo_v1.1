"""
Token metrics and performance tracking
Core scoring and signal generation
"""
import logging
from typing import Dict, Optional
from datetime import datetime, timezone
import json

from ..models import TokenMetrics, Transaction
from ..events import event_bell
from ..config import SCORE_THRESHOLDS
from .categorizer import TokenCategorizer

class TokenMetricsManager:
    """Manages token metrics and scoring"""
    def __init__(self):
        self.logger = logging.getLogger('token_metrics')
        self.token_metrics: Dict[str, TokenMetrics] = {}
        self.categorizer = TokenCategorizer()
        self.previous_scores: Dict[str, float] = {}  # Track previous scores for threshold crossing
        
    async def get_or_create_metrics(self, token_address: str, symbol: str) -> TokenMetrics:
        """Get existing metrics or create new ones"""
        try:
            if token_address not in self.token_metrics:
                # Create new metrics with fallback symbol if needed
                self.token_metrics[token_address] = TokenMetrics(
                    symbol=symbol or token_address[:8],  # Use address prefix as fallback
                    token_address=token_address
                )
                
                try:
                    # Categorize token and get metadata
                    category, confidence = self.categorizer.categorize_token(
                        token_address, 
                        symbol
                    )
                    
                    # Try to get and validate metadata
                    metadata = self.categorizer.get_token_metadata(token_address)
                    if metadata is not None and isinstance(metadata, dict):
                        # Only update symbol if none was provided and metadata has a valid one
                        if not symbol and metadata.get('symbol'):
                            self.token_metrics[token_address].symbol = metadata['symbol']
                            self.logger.info(
                                f"Using metadata symbol as backup: {metadata['symbol']}"
                            )
                    
                    self.token_metrics[token_address].category = category
                    self.token_metrics[token_address].confidence = confidence
                    
                except Exception as e:
                    self.logger.warning(
                        f"Error processing metadata for {token_address[:8]}: {str(e)}, "
                        "defaulting to UNKNOWN category"
                    )
                    self.token_metrics[token_address].category = "UNKNOWN"
                    self.token_metrics[token_address].confidence = 0.0
                
                self.logger.info(
                    f"Created metrics for {self.token_metrics[token_address].symbol} "
                    f"({self.token_metrics[token_address].category}, "
                    f"{self.token_metrics[token_address].confidence:.2f})"
                )
                
                # Initialize previous score
                self.previous_scores[token_address] = 0.0
                
                # Emit token metrics update
                await self.emit_metrics_update()
            
            return self.token_metrics[token_address]
            
        except Exception as e:
            self.logger.error(f"Error in get_or_create_metrics for {token_address[:8]}: {str(e)}")
            # Create basic metrics as fallback if something went wrong
            if token_address not in self.token_metrics:
                self.token_metrics[token_address] = TokenMetrics(
                    symbol=symbol or token_address[:8],
                    token_address=token_address,
                    category="UNKNOWN",
                    confidence=0.0
                )
            return self.token_metrics[token_address]
    
    async def process_transaction(
        self,
        token_address: str,
        symbol: str,
        amount: float,
        tx_type: str,
        wallet_address: str,
        wallet_score: float
    ):
        """Process a token transaction"""
        try:
            # Validate inputs
            if not token_address:
                raise ValueError("Token address is required")
            if not symbol:
                symbol = token_address[:8]  # Use address prefix as fallback
                self.logger.warning(f"No symbol provided for {token_address[:8]}, using address prefix")
            if not amount or amount <= 0:
                raise ValueError(f"Invalid amount: {amount}")
            if not wallet_address:
                raise ValueError("Wallet address is required")
                
            metrics = await self.get_or_create_metrics(token_address, symbol)
            previous_score = metrics.score  # Get score before update
            
            if tx_type == 'buy':
                metrics.add_score(wallet_score, wallet_address, amount)
                self.logger.info(
                    f"Buy: {metrics.symbol} "  # Use metrics.symbol for consistency
                    f"(Score: {metrics.score:.2f}, "
                    f"Amount: {amount:.4f})"
                )
                
            elif tx_type == 'sell':
                metrics.reduce_score(wallet_score, amount, wallet_address)
                self.logger.info(
                    f"Sell: {metrics.symbol} "  # Use metrics.symbol for consistency
                    f"(Score: {metrics.score:.2f}, "
                    f"Amount: {amount:.4f})"
                )
            
            # Create transaction record
            transaction = Transaction(
                symbol=metrics.symbol,  # Use metrics.symbol for consistency
                amount=amount,
                tx_type=tx_type,
                timestamp=datetime.now(timezone.utc),
                token_address=token_address,
                wallet_address=wallet_address
            )
            
            # Emit updates
            await event_bell.publish('transaction', {
                'transaction': transaction.to_dict()
            })
            
            await self.emit_metrics_update()
            
            # Check for threshold crossing
            threshold = SCORE_THRESHOLDS[metrics.category]
            if previous_score < threshold and metrics.score >= threshold:
                # Emit trading signal only when crossing threshold
                await event_bell.publish('trading_signal', {
                    'token_address': token_address,
                    'symbol': metrics.symbol,  # Use metrics.symbol for consistency
                    'category': metrics.category,
                    'score': metrics.score,
                    'confidence': metrics.confidence
                })
                
        except Exception as e:
            self.logger.error(
                f"Error processing transaction for {symbol} ({token_address[:8]}): {str(e)}"
            )
            
    async def emit_metrics_update(self):
        """Emit token metrics update event"""
        metrics_data = {
            address: {
                'symbol': m.symbol,
                'category': m.category,
                'score': m.score,
                'confidence': m.confidence,
                'buy_count': m.buy_count,
                'sell_count': m.sell_count,
                'total_volume': m.total_volume,
                'unique_buyers': len(m.unique_buyers),
                'last_update': m.last_update.isoformat(),
                'recent_changes': m.recent_changes
            }
            for address, m in self.token_metrics.items()
            if m.score > 0  # Only include tokens with non-zero scores
        }
        
        # Debug log the metrics data
        for addr, data in metrics_data.items():
            self.logger.info(
                f"Emitting metrics for {addr[:8]}: "
                f"Symbol={data['symbol']}, "
                f"Category={data['category']}, "
                f"Score={data['score']:.2f}"
            )
        
        await event_bell.publish('token_metrics', {
            'token_metrics': metrics_data
        })
    
    def cleanup_old_tokens(self, max_age_hours: int = 24):
        """Remove old tokens that haven't been updated"""
        now = datetime.now(timezone.utc)
        addresses_to_remove = []
        
        for address, metrics in self.token_metrics.items():
            age = (now - metrics.last_update).total_seconds() / 3600
            if age > max_age_hours and metrics.score == 0:
                addresses_to_remove.append(address)
        
        for address in addresses_to_remove:
            del self.token_metrics[address]
            del self.previous_scores[address]  # Clean up previous scores too
            
        if addresses_to_remove:
            self.logger.info(f"Cleaned up {len(addresses_to_remove)} old tokens")
