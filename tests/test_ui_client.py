"""
UI client tests
Tests data formatting and transmission
"""
import pytest
import json
from datetime import datetime, timezone
from src.ui_client import UIClient

class TestUIClient:
    """Test UI client data handling"""
    
    @pytest.fixture
    def ui_client(self):
        """Create test UI client"""
        return UIClient("ws://localhost:8000")

    async def test_position_data_format(self, ui_client):
        """Test position data formatting"""
        # Create test position data
        position_data = {
            'token_address': 'test_token',
            'symbol': 'TEST',
            'category': 'MEME',
            'entry_price': 0.0025,  # In SOL
            'current_price': 0.0030,  # In SOL
            'tokens': 100000,
            'r_pnl': 0.0,  # In SOL
            'ur_pnl': 0.0005,  # In SOL (0.0030 - 0.0025) * 100000
            'total_pnl': 0.0005,  # In SOL
            'entry_time': datetime.now(timezone.utc).isoformat()
        }

        # Track what was sent
        await ui_client.update_positions([position_data])
        sent_data = ui_client.last_sent_data

        # Verify data format
        assert 'active_positions' in sent_data
        sent_position = sent_data['active_positions'][0]

        # Verify SOL values have 4 decimal places
        assert format(sent_position['entry_price'], '.4f') == '0.0025'
        assert format(sent_position['current_price'], '.4f') == '0.0030'
        assert format(sent_position['r_pnl'], '.4f') == '0.0000'
        assert format(sent_position['ur_pnl'], '.4f') == '0.0005'
        assert format(sent_position['total_pnl'], '.4f') == '0.0005'

    async def test_multiple_positions(self, ui_client):
        """Test handling multiple positions"""
        positions = [
            {
                'token_address': 'token1',
                'symbol': 'TEST1',
                'category': 'MEME',
                'entry_price': 0.0025,
                'current_price': 0.0030,
                'tokens': 100000,
                'r_pnl': 0.0,
                'ur_pnl': 0.0005,
                'total_pnl': 0.0005,
                'entry_time': datetime.now(timezone.utc).isoformat()
            },
            {
                'token_address': 'token2',
                'symbol': 'TEST2',
                'category': 'AI',
                'entry_price': 0.0015,
                'current_price': 0.0020,
                'tokens': 200000,
                'r_pnl': 0.0,
                'ur_pnl': 0.001,
                'total_pnl': 0.001,
                'entry_time': datetime.now(timezone.utc).isoformat()
            }
        ]

        await ui_client.update_positions(positions)
        sent_data = ui_client.last_sent_data

        # Verify all positions sent
        assert len(sent_data['active_positions']) == 2
        
        # Verify each position's format
        for sent_pos, orig_pos in zip(sent_data['active_positions'], positions):
            assert format(sent_pos['entry_price'], '.4f') == format(orig_pos['entry_price'], '.4f')
            assert format(sent_pos['current_price'], '.4f') == format(orig_pos['current_price'], '.4f')
            assert format(sent_pos['r_pnl'], '.4f') == format(orig_pos['r_pnl'], '.4f')
            assert format(sent_pos['ur_pnl'], '.4f') == format(orig_pos['ur_pnl'], '.4f')
            assert format(sent_pos['total_pnl'], '.4f') == format(orig_pos['total_pnl'], '.4f')

    async def test_position_update(self, ui_client):
        """Test position updates maintain precision"""
        # Initial position
        initial_position = {
            'token_address': 'test_token',
            'symbol': 'TEST',
            'category': 'MEME',
            'entry_price': 0.0025,
            'current_price': 0.0030,
            'tokens': 100000,
            'r_pnl': 0.0,
            'ur_pnl': 0.0005,
            'total_pnl': 0.0005,
            'entry_time': datetime.now(timezone.utc).isoformat()
        }

        await ui_client.update_positions([initial_position])
        initial_sent = ui_client.last_sent_data

        # Update position
        updated_position = dict(initial_position)
        updated_position.update({
            'current_price': 0.0035,
            'ur_pnl': 0.001,
            'total_pnl': 0.001
        })

        await ui_client.update_positions([updated_position])
        updated_sent = ui_client.last_sent_data

        # Verify precision maintained
        initial_pos = initial_sent['active_positions'][0]
        updated_pos = updated_sent['active_positions'][0]

        assert format(initial_pos['entry_price'], '.4f') == format(updated_pos['entry_price'], '.4f')
        assert format(updated_pos['current_price'], '.4f') == '0.0035'
        assert format(updated_pos['ur_pnl'], '.4f') == '0.0010'
        assert format(updated_pos['total_pnl'], '.4f') == '0.0010'
