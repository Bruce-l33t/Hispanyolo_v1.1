"""
Tests for main.py data processing
Specifically tests token metrics data transformation
"""
import pytest
import asyncio
from datetime import datetime, timezone
from typing import Dict, Any

from src.main import handle_token_metrics
from src.models import TokenMetrics
from src.monitor.token_metrics import TokenMetricsManager
from src.events import event_bell

class TestMainProcessing:
    @pytest.fixture
    async def sample_metrics_data(self):
        """Create sample metrics data in token_metrics format"""
        token_address = "TestTokenAddress123"
        return {
            'token_metrics': {
                token_address: {
                    'symbol': 'TEST',
                    'category': 'AI',
                    'score': 100.0,
                    'confidence': 1.0,
                    'buy_count': 1,
                    'sell_count': 0,
                    'total_volume': 5.0,
                    'unique_buyers': 1,
                    'last_update': datetime.now(timezone.utc).isoformat(),
                    'recent_changes': []
                }
            }
        }

    @pytest.mark.asyncio
    async def test_metrics_processing(self, sample_metrics_data):
        """Test main.py processes metrics correctly"""
        # Track received events
        received_data = None
        
        async def handle_metrics(data):
            nonlocal received_data
            received_data = data
            
        # Subscribe to metrics events
        await event_bell.subscribe('token_metrics', handle_metrics)
        
        # Process metrics through main's handler
        await handle_token_metrics(sample_metrics_data)
        
        # Wait for event processing
        await asyncio.sleep(0.1)
        
        # Verify data structure
        assert received_data is not None
        assert 'token_metrics' in received_data
        
        # Data should maintain address as key
        metrics = received_data['token_metrics']
        for addr, token in metrics.items():
            assert isinstance(addr, str)  # Address should be key
            assert 'symbol' in token      # Symbol should be in data
            assert 'category' in token
            assert 'score' in token
