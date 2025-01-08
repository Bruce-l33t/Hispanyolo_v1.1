# Birdeye Token Metadata API Guide

## Token Metadata Endpoints

### Single Token Metadata
```
GET https://public-api.birdeye.so/defi/v3/token/meta-data/single
```
- Query param: `address=<token_address>`
- Returns metadata for a single token

### Multiple Tokens Metadata
```
GET https://public-api.birdeye.so/defi/v3/token/meta-data/multiple
```
- Query param: `list_address=<token_address>` (comma-separated for multiple)
- Returns metadata keyed by token address

## Required Headers
```python
headers = {
    "X-API-KEY": "your_api_key",
    "accept": "application/json",
    "x-chain": "solana"
}
```

## Example Usage
```python
# Single token
response = requests.get(
    "https://public-api.birdeye.so/defi/v3/token/meta-data/single",
    headers=headers,
    params={"address": token_address}
)

# Multiple tokens
response = requests.get(
    "https://public-api.birdeye.so/defi/v3/token/meta-data/multiple",
    headers=headers,
    params={"list_address": "addr1,addr2,addr3"}
)
```

## Important Notes
- Both endpoints use GET requests with query parameters
- Do NOT use POST requests or JSON body
- Multiple endpoint accepts comma-separated addresses as a string, not a JSON array 