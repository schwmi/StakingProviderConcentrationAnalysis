# StakingRewards API Wrapper

## Overview
This project contains a Python wrapper for the StakingRewards GraphQL API, designed to be used from Jupyter notebooks (e.g., `StakingRewardsExperiments.ipynb`) and other Python scripts.

## Structure
- `Helper/` - Python package containing the API client
  - `stakingrewards_api.py` - Main API client implementation
  - `__init__.py` - Package initialization

## API Client

### Class: `StakingRewardsAPIClient`

#### Configuration
- **Base URL**: `https://api.stakingrewards.com/public/query`
- **Authentication**: API key via `X-API-KEY` header
- **HTTP Client**: `requests` library

#### Usage

```python
from Helper import StakingRewardsAPIClient

# Initialize client (API key from X_API_KEY environment variable)
client = StakingRewardsAPIClient()

# Or provide API key directly
client = StakingRewardsAPIClient(api_key="your_api_key_here")
```

#### Environment Variables
- `X_API_KEY` - Your StakingRewards API key

**Setup**: Add your API key to the `.env` file:
```
X_API_KEY=your_actual_api_key_here
```

## Methods

### `get_billing_status()`
Get billing status including available credits and subscription information.

```python
status = client.get_billing_status()
```

**Returns**: Dictionary with billing status information

### GraphQL Query Methods

#### `get_assets(symbols=None, limit=None, where=None)`
Query assets from the StakingRewards API.

**Parameters:**
- `symbols` (list, optional): List of asset symbols to filter by (e.g., `["ETH", "BTC"]`)
- `limit` (int, optional): Maximum number of results to return
- `where` (dict, optional): Additional where conditions for filtering

**Returns**: Dictionary with assets data

**Example:**
```python
# Get single ETH asset
assets = client.get_assets(symbols=["ETH"], limit=1)

# Get multiple assets
assets = client.get_assets(symbols=["ETH", "BTC"])

# Get all assets (no filter)
assets = client.get_assets()
```

**Fields returned:** id, name, slug, description, symbol

#### `get_asset_metrics(slug, metric_keys=None, created_before=None, metrics_limit=None, order=None)`
Query an asset with its metrics.

**Parameters:**
- `slug` (str): Asset slug to query (e.g., `"polkadot"`, `"ethereum-2-0"`)
- `metric_keys` (list, optional): List of metric keys to filter (e.g., `["reward_rate"]`)
- `created_before` (str, optional): Filter metrics created before this date (ISO format: `"2023-06-28"`)
- `metrics_limit` (int, optional): Maximum number of metrics to return
- `order` (dict, optional): Order clause for metrics (default: `{"createdAt": "desc"}`)

**Returns**: Dictionary with asset and metrics data

**Example:**
```python
# Get Polkadot asset with reward_rate metrics
result = client.get_asset_metrics(
    slug="polkadot",
    metric_keys=["reward_rate"],
    created_before="2023-06-28",
    metrics_limit=10
)

# Get Ethereum metrics with default ordering
result = client.get_asset_metrics(
    slug="ethereum-2-0",
    metric_keys=["reward_rate"],
    metrics_limit=5
)
```

**Fields returned:**
- Asset: id, slug, logoUrl
- Metrics: defaultValue, createdAt
