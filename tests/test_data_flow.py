"""
Integration tests for complete data flow
Tests actual data formats through the event system
"""
import pytest
import asyncio
import json
from datetime import datetime, timezone
from typing import Dict, Any
import sys
from pathlib import Path

# Add src to Python path
sys.path.append(str(Path(__file__).parent.parent))

from src.monitor.token_metrics import TokenMetricsManager
from src.models import TokenMetrics
from src.events import event_bell

class TestDataFlow:
    @pytest.fixture
    async def token_metrics_manager(self):
        """Create token metrics manager with test data"""
        manager = TokenMetricsManager()
        
        # Add test token with real data structure
        token_address = "TestTokenAddress123"
        metrics = TokenMetrics(
            symbol="TEST",
            token_address=token_address
        )
        metrics.category = "AI"
        metrics.score = 100.0
        metrics.confidence = 1.0
        metrics.last_update = datetime.now(timezone.utc)
        
        manager.token_metrics[token_address] = metrics
        return manager

    @pytest.mark.asyncio
    async def test_metrics_data_flow(self, token_metrics_manager):
        """Test complete flow of metrics data through event system"""
        # 1. Get metrics data as emitted by TokenMetricsManager
        await token_metrics_manager.emit_metrics_update()
        
        # 2. Verify data structure at each step
        def verify_metrics_format(data: Dict[str, Any]):
            """Verify metrics maintain correct format"""
            assert 'token_metrics' in data
            metrics = data['token_metrics']
            
            # Should use address as key
            for addr, token in metrics.items():
                assert isinstance(addr, str)  # Address is key
                assert 'symbol' in token      # Symbol is in data
                assert 'category' in token
                assert 'score' in token
                
        # Subscribe to metrics events
        received_data = None
        async def handle_metrics(data):
            nonlocal received_data
            received_data = data
            verify_metrics_format(data)
            
        await event_bell.subscribe('token_metrics', handle_metrics)
        
        # 3. Emit metrics update
        await token_metrics_manager.emit_metrics_update()
        
        # Wait for event processing
        await asyncio.sleep(0.1)
        
        # 4. Verify data was received correctly
        assert received_data is not None
        verify_metrics_format(received_data)
