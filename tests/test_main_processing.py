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
from src.ui_client import UIClient

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
        # Create test UI client
        ui = UIClient()
        
        # Process metrics through main's handler
        await handle_token_metrics(sample_metrics_data, ui)
        
        # Verify data structure sent to UI
        sent_data = ui.last_sent_data  # Need to add this to UIClient for testing
        assert 'token_metrics' in sent_data
        
        # Data should maintain address as key
        metrics = sent_data['token_metrics']
        for addr, token in metrics.items():
            assert isinstance(addr, str)  # Address should be key
            assert 'symbol' in token      # Symbol should be in data
            assert 'category' in token
            assert 'score' in token
            
        # Clean up
        await ui.close()
