"""
Test metadata analyzer with real tokens
"""
import logging
import sys
import traceback
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent
sys.path.append(str(project_root))

from src.metadata import MetadataAnalyzer

# Setup logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# Test tokens (from real data)
TEST_TOKENS = {
    # Known AI tokens
    "61V8vBaqAGMpgDQi4JcAwo1dmBGHsyhzodcPqnEVpump": "ARC",      # AI Rig Complex
    "HeLp6NuQkmYB4pYWo2zYs22mESHXPQYzXbB8n4V98jwC": "AI16Z",    # AI16Z
    "79vpEaaXrHnHHEtU9kYYQtwLTZy1SXpxXHi7LZ9Ppump": "PRISMAI",  # PrismAI
    "9DHe3pycTuymFk4H4bbPoAJ4hQrr2kaLDF6J6aAKpump": "HIVEAI",   # HiveAI
    "8vBMibwpn8wpfYKbQ9xqzodymg3LjmYec2tSNGRy23K8": "HYPER",    # Hyper
    
    # Meme tokens for comparison
    "DezXAZ8z7PnrnRJjz3wXBoRgixCa6xjnB7YaB1pPB263": "BONK",     # BONK
    "CzLSujWBLFsSjncfkh59rUFqvafWcY5tzedWJSuypump": "GOAT",     # GOAT (AI meme token)
}

def test_metadata_analyzer():
    """Test metadata analyzer with known tokens"""
    analyzer = MetadataAnalyzer()
    
    print("\n🔍 Testing Metadata Analyzer")
    print("-" * 50)
    
    for address, symbol in TEST_TOKENS.items():
        print(f"\nAnalyzing {symbol} ({address[:8]}...)")
        
        try:
            # Get metadata
            metadata = analyzer.get_metadata(address)
            if metadata:
                print(f"✅ Got metadata:")
                print(f"  Name: {metadata.get('name', 'N/A')}")
                print(f"  Symbol: {metadata.get('symbol', 'N/A')}")
                print(f"  Raw metadata: {metadata}")
                
                # Safely get description and Twitter
                extensions = metadata.get('extensions') or {}
                description = extensions.get('description', '')
                twitter = extensions.get('twitter', '')
                
                if description:
                    print(f"  Description: {description[:100]}...")
                else:
                    print("  Description: N/A")
                    
                if twitter:
                    print(f"  Twitter: @{twitter}")
            else:
                print("❌ Failed to get metadata")
                continue
                
            # Analyze token
            is_ai, confidence, details = analyzer.analyze_token(address, symbol)
            print(f"\nAnalysis Results:")
            print(f"  Is AI: {'Yes' if is_ai else 'No'}")
            print(f"  Confidence: {confidence:.2f}")
            print(f"  Raw details: {details}")
            
            if details.get('matches'):
                print("\nMatched Signals:")
                for category, signals in details['matches'].items():
                    if signals:
                        print(f"  {category.title()}: {', '.join(signals)}")
            
        except Exception as e:
            print(f"❌ Error analyzing token: {str(e)}")
            print("Traceback:")
            traceback.print_exc()
            
        print("-" * 50)

if __name__ == "__main__":
    test_metadata_analyzer() 