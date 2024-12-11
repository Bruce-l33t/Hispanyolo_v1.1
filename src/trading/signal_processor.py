"""
Signal processing and trade decisions
"""
import logging
from typing import Dict, Optional
from datetime import datetime, timezone

from ..config import SCORE_THRESHOLDS, POSITION_SIZES

class SignalProcessor:
    """Process trading signals and make trade decisions"""
    def __init__(self):
        self.logger = logging.getLogger('signal_processor')
        
    async def process_signal(self, signal: dict) -> Optional[dict]:
        """
        Process trading signal and return trade parameters if valid
        Returns None if signal doesn't qualify
        """
        try:
            # Extract signal data
            token_address = signal['token_address']
            symbol = signal['symbol']
            category = signal['category']
            score = signal['score']
            
            # Check score threshold
            threshold = SCORE_THRESHOLDS[category]
            if score < threshold:
                self.logger.info(
                    f"Score {score} below threshold {threshold} "
                    f"for {category}"
                )
                return None
                
            # Calculate position size
            size = POSITION_SIZES[category]
            if not size:
                return None
                
            # Return trade parameters
            trade_params = {
                'token_address': token_address,
                'symbol': symbol,
                'category': category,
                'size': size,
                'score': score,  # Include score for logging
                'timestamp': datetime.now(timezone.utc).isoformat()
            }
            
            self.logger.info(
                f"Signal qualified: {symbol} ({category}) "
                f"score {score} >= threshold {threshold}"
            )
            
            return trade_params
            
        except Exception as e:
            self.logger.error(f"Error processing signal: {e}")
            return None
