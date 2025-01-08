"""
Diagnostic script to examine Twitter profile data
"""
import logging
import requests
from bs4 import BeautifulSoup
import json

# Setup logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

def normalize_twitter_url(url):
    """Convert twitter.com URLs to x.com"""
    return url.replace("twitter.com", "x.com")

def examine_twitter_profile(url="https://twitter.com/arcdotfun"):
    """Examine what data we can get from a Twitter profile"""
    url = normalize_twitter_url(url)
    
    print("\n🔍 Examining Twitter Profile")
    print("-" * 50)
    print(f"URL: {url}")
    
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko)'
        }
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        print("\nRaw HTML snippet:")
        print("-" * 30)
        # Print first 500 chars of HTML to see structure
        print(response.text[:500])
        
        print("\nTrying to find:")
        print("- Bio")
        print("- Links (especially GitHub)")
        print("-" * 30)
        
        # Let's see what we can find
        meta_tags = soup.find_all('meta')
        print("\nMeta tags found:")
        for tag in meta_tags:
            if tag.get('name') or tag.get('property'):
                print(f"{tag.get('name') or tag.get('property')}: {tag.get('content')}")
        
    except Exception as e:
        print(f"❌ Error: {str(e)}")
    
    print("-" * 50)

if __name__ == "__main__":
    # Test with both URL formats
    print("Testing with twitter.com URL:")
    examine_twitter_profile("https://twitter.com/arcdotfun")
    
    print("\nTesting with x.com URL:")
    examine_twitter_profile("https://x.com/arcdotfun") 