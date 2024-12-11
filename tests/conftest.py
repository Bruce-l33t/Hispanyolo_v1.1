"""
Test configuration and fixtures
"""
import pytest
from unittest.mock import Mock
import sys
from pathlib import Path

# Add project root to path for imports
project_root = str(Path(__file__).parent.parent.absolute())
sys.path.insert(0, project_root)

# Import real keys for integration tests
from dontshare import birdeye_api_key, alchemy_url, alchemy_key

# Configure pytest-asyncio
pytest.register_assert_rewrite('pytest_asyncio')

def pytest_configure(config):
    """Configure pytest markers"""
    config.addinivalue_line("markers", "asyncio: mark test as async")
    config.addinivalue_line("markers", "integration: mark test as integration test")
    config.addinivalue_line("markers", "unit: mark test as unit test")

@pytest.fixture
def mock_api_keys():
    """Fixture for mock API keys"""
    return {
        "birdeye_api_key": "test_key",
        "alchemy_url": "http://test.url",
        "alchemy_key": "test_key"
    }

@pytest.fixture
def real_api_keys():
    """Fixture for real API keys"""
    return {
        "birdeye_api_key": birdeye_api_key,
        "alchemy_url": alchemy_url,
        "alchemy_key": alchemy_key
    }

@pytest.fixture
def mock_birdeye_client():
    """Mock Birdeye API client"""
    client = Mock()
    client.get_wallet_transactions = Mock(return_value={
        'data': {
            'solana': []
        }
    })
    return client

@pytest.fixture
def mock_alchemy_client():
    """Mock Alchemy API client"""
    client = Mock()
    client.execute_swap = Mock(return_value="test_signature")
    return client

@pytest.fixture
def mock_price_service():
    """Mock price service"""
    service = Mock()
    service.get_price = Mock(return_value=10.0)
    service.get_prices = Mock(return_value={'test_token': 10.0})
    return service

@pytest.fixture
def mock_transaction_response():
    """Mock transaction response data"""
    return {
        'success': True,
        'data': {
            'solana': [
                {
                    'txHash': 'test_hash',
                    'blockTime': '2024-01-01T00:00:00Z',
                    'status': 'Success',
                    'fee': 5000,
                    'mainAction': 'SWAP',
                    'balanceChange': [
                        {
                            'amount': '1000000000',
                            'symbol': 'TEST',
                            'decimals': 9
                        }
                    ]
                }
            ]
        }
    }

@pytest.fixture
def mock_metadata_response():
    """Mock metadata response data"""
    return {
        'success': True,
        'data': {
            'name': 'Test Token',
            'symbol': 'TEST',
            'description': 'Test token description'
        }
    }

@pytest.fixture
def mock_price_response():
    """Mock price response data"""
    return {
        'success': True,
        'data': {
            'value': 1.5,
            'updateUnixTime': 1234567890
        }
    }
