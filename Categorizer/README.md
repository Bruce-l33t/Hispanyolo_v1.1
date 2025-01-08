# Advanced Token Categorizer

A sophisticated system for categorizing Solana tokens using multiple data sources:
- Token metadata analysis
- Twitter content analysis
- LLM-based verification

## Setup

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Configure environment variables:
Create a `.env` file with:
```
BIRDEYE_API_KEY=your_key
TWITTER_USERNAME=your_username
TWITTER_EMAIL=your_email
TWITTER_PASSWORD=your_password
OPENROUTER_API_KEY=your_key
```

## Components

- Metadata Analyzer: Token metadata analysis using Birdeye API
- Twitter Analyzer: Social signal detection from project Twitter accounts
- LLM Analyzer: Advanced pattern recognition using LLM
- Main Categorizer: Combines all signals for final classification

## Usage

```python
from src.categorizer import TokenCategorizer

categorizer = TokenCategorizer()
category, confidence = categorizer.categorize_token("token_address", "symbol")
```

## Testing

Run tests with:
```bash
pytest tests/
``` 