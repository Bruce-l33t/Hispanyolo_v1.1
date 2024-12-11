"""
Tests for token categorization with real API calls
"""
import pytest
import logging

from src.monitor.categorizer import TokenCategorizer

# Configure logging for tests
logging.basicConfig(level=logging.DEBUG)  # Set to DEBUG to see API responses

@pytest.fixture
def categorizer():
    """Create test categorizer"""
    return TokenCategorizer()

def test_real_tokens(categorizer):
    """Test with real tokens - AVB (AI) and BONK (MEME)"""
    # Test AVB token (should be AI)
    avb_address = "6d5zHW5B8RkGKd51Lpb9RqFQSqDudr9GJgZ1SgQZpump"
    avb_metadata = categorizer.get_token_metadata(avb_address)
    assert avb_metadata is not None, "Should get metadata for AVB"
    assert 'name' in avb_metadata, "AVB metadata should contain name"
    assert 'symbol' in avb_metadata, "AVB metadata should contain symbol"
    
    # Test categorization of AVB
    category, confidence = categorizer.categorize_token(avb_address, "AVB")
    assert category == "AI", "AVB should be categorized as AI"
    assert confidence > 0, "AVB should have positive confidence"
    
    # Test BONK token (should be MEME)
    bonk_address = "DezXAZ8z7PnrnRJjz3wXBoRgixCa6xjnB7YaB1pPB263"
    bonk_metadata = categorizer.get_token_metadata(bonk_address)
    assert bonk_metadata is not None, "Should get metadata for BONK"
    assert 'name' in bonk_metadata, "BONK metadata should contain name"
    assert 'symbol' in bonk_metadata, "BONK metadata should contain symbol"
    
    # Test categorization of BONK
    category, confidence = categorizer.categorize_token(bonk_address, "BONK")
    assert category == "MEME", "BONK should be categorized as MEME"
    assert confidence == 0, "BONK should have zero confidence"

def test_error_handling(categorizer):
    """Test error handling with invalid token address"""
    category, confidence = categorizer.categorize_token(
        "invalid_address",
        "INVALID"
    )
    assert category == "MEME", "Invalid token should default to MEME"
    assert confidence == 0, "Invalid token should have zero confidence"

def test_batch_metadata_fetch(categorizer):
    """Test fetching metadata for multiple tokens"""
    tokens = [
        ("6d5zHW5B8RkGKd51Lpb9RqFQSqDudr9GJgZ1SgQZpump", "AVB"),
        ("DezXAZ8z7PnrnRJjz3wXBoRgixCa6xjnB7YaB1pPB263", "BONK")
    ]
    
    # Get metadata for all tokens
    for addr, symbol in tokens:
        metadata = categorizer.get_token_metadata(addr)
        assert metadata is not None, f"Should get metadata for {symbol}"
        assert 'name' in metadata, f"Metadata for {symbol} should contain name"
        assert 'symbol' in metadata, f"Metadata for {symbol} should contain symbol"
        
        # Test categorization
        category, confidence = categorizer.categorize_token(addr, symbol)
        if symbol == "AVB":
            assert category == "AI", "AVB should be AI"
            assert confidence > 0, "AVB should have positive confidence"
        else:
            assert category == "MEME", "BONK should be MEME"
            assert confidence == 0, "BONK should have zero confidence"
