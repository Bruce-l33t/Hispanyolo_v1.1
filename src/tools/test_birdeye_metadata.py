"""
Test Birdeye metadata API calls and categorization
"""
import requests
import sys
import os
import logging
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent.parent.parent
sys.path.append(str(project_root))
import dontshare
from src.monitor.categorizer import TokenCategorizer

# Test with known tokens
TEST_TOKEN = "61V8vBaqAGMpgDQi4JcAwo1dmBGHsyhzodcPqnEVpump"  # AI Rig Complex

def setup_logging():
    """Setup debug logging"""
    logging.basicConfig(
        level=logging.DEBUG,
        format='%(name)s - %(levelname)s - %(message)s'
    )

def test_metadata_and_categorization():
    """Test metadata API and categorization"""
    setup_logging()
    
    # Initialize categorizer
    categorizer = TokenCategorizer()
    
    # Test categorization
    print("\n🔍 Testing token categorization...")
    category, confidence = categorizer.categorize_token(TEST_TOKEN, "arc")
    print(f"Category: {category}")
    print(f"Confidence: {confidence}")

if __name__ == "__main__":
    test_metadata_and_categorization()
