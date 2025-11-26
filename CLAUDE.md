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
GraphQL query methods will be added as queries are defined. Each method will parameterize the corresponding GraphQL query for easy use.
