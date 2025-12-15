import os
import json
import hashlib
import requests
from pathlib import Path


class StakingRewardsAPIClient:
    """
    Client for interacting with the StakingRewards GraphQL API.
    """

    BASE_URL = "https://api.stakingrewards.com/public/query"

    def __init__(self, api_key=None, cache_dir="api_response_cache"):
        """
        Initialize the StakingRewards API client.

        Args:
            api_key (str, optional): API key for authentication.
                                     If not provided, will read from X_API_KEY environment variable.
            cache_dir (str, optional): Directory to store cached API responses (default: "api_response_cache")
        """
        self.api_key = api_key or os.getenv('X_API_KEY')
        if not self.api_key:
            raise ValueError("API key must be provided or set in X_API_KEY environment variable")

        self.headers = {
            "X-API-KEY": self.api_key,
            "Content-Type": "application/json"
        }

        # Set up cache directory
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(exist_ok=True)

    def _get_cache_key(self, query, variables=None):
        """
        Generate a unique cache key for a query and its variables.

        Args:
            query (str): The GraphQL query string
            variables (dict, optional): Variables for the GraphQL query

        Returns:
            str: A unique cache key (hash)
        """
        # Create a deterministic representation of the query and variables
        cache_data = {
            "query": query.strip(),
            "variables": variables or {}
        }
        # Convert to JSON string with sorted keys for consistency
        cache_string = json.dumps(cache_data, sort_keys=True)
        # Generate hash
        return hashlib.sha256(cache_string.encode()).hexdigest()

    def _execute_query(self, query, variables=None, use_cache=True):
        """
        Execute a GraphQL query against the StakingRewards API with caching support.

        Args:
            query (str): The GraphQL query string
            variables (dict, optional): Variables for the GraphQL query
            use_cache (bool, optional): Whether to use cached responses (default: True)

        Returns:
            dict: The JSON response from the API

        Raises:
            requests.exceptions.RequestException: If the request fails
        """
        # Generate cache key
        cache_key = self._get_cache_key(query, variables)
        cache_file = self.cache_dir / f"{cache_key}.json"

        # Try to load from cache if enabled
        if use_cache and cache_file.exists():
            try:
                with open(cache_file, 'r') as f:
                    return json.load(f)
            except (json.JSONDecodeError, IOError):
                # If cache is corrupted, continue to make API call
                pass

        # Make API call
        payload = {"query": query}
        if variables:
            payload["variables"] = variables

        response = requests.post(
            self.BASE_URL,
            json=payload,
            headers=self.headers
        )
        try:
            response.raise_for_status()
        except requests.exceptions.HTTPError as http_err:
            # Bubble up richer context for easier debugging
            try:
                error_body = response.json()
            except Exception:
                error_body = response.text
            raise requests.exceptions.HTTPError(
                f"HTTP {response.status_code} for {self.BASE_URL}: {error_body}"
            ) from http_err
        result = response.json()

        # Save to cache
        if use_cache:
            try:
                with open(cache_file, 'w') as f:
                    json.dump(result, f, indent=2)
            except IOError:
                # If we can't write to cache, continue anyway
                pass

        return result

    def get_billing_status(self):
        """
        Get billing status including available credits and subscription information.

        Returns:
            dict: The JSON response with billing status information

        Raises:
            requests.exceptions.RequestException: If the request fails
        """
        response = requests.get(
            "https://api.stakingrewards.com/public/billing/status",
            headers=self.headers
        )
        response.raise_for_status()
        return response.json()

    def get_assets(self, symbols=None, limit=None, where=None, use_cache=True):
        """
        Query assets from the StakingRewards API.

        Args:
            symbols (list, optional): List of asset symbols to filter by (e.g., ["ETH", "BTC"])
            limit (int, optional): Maximum number of results to return
            where (dict, optional): Additional where conditions for filtering
            use_cache (bool, optional): Whether to use cached responses (default: True)

        Returns:
            dict: The JSON response containing assets data

        Raises:
            requests.exceptions.RequestException: If the request fails
        """
        # Build where clause
        where_clause = where or {}
        if symbols:
            where_clause["symbols"] = symbols

        # Build query arguments
        args = []
        if where_clause:
            # Convert to GraphQL syntax (no quotes around keys)
            where_parts = []
            for key, value in where_clause.items():
                where_parts.append(f"{key}: {json.dumps(value)}")
            where_str = "{" + ", ".join(where_parts) + "}"
            args.append(f"where: {where_str}")
        if limit is not None:
            args.append(f"limit: {limit}")

        args_str = f"({', '.join(args)})" if args else ""

        # Build GraphQL query
        query = f"""
        {{
          assets{args_str} {{
            id
            name
            slug
            description
            symbol
          }}
        }}
        """

        return self._execute_query(query, use_cache=use_cache)

    def execute_raw_query(self, query, use_cache=True):
        """
        Executes an raw query string 1:1

        Args:
            query (str): The raw GraphQL query string
            use_cache (bool, optional): Whether to use cached responses (default: True)

        Returns:
            dict: The JSON response from the API
        """

        return self._execute_query(query, use_cache=use_cache)


    def get_asset_metrics(self, slug, metric_keys=None, created_before=None, metrics_limit=None, order=None, use_cache=True):
        """
        Query an asset with its metrics from the StakingRewards API.

        Args:
            slug (str): Asset slug to query (e.g., "polkadot", "ethereum-2-0")
            metric_keys (list, optional): List of metric keys to filter (e.g., ["reward_rate"])
            created_before (str, optional): Filter metrics created before this date (ISO format: "2023-06-28")
            metrics_limit (int, optional): Maximum number of metrics to return
            order (dict, optional): Order clause for metrics (default: {"createdAt": "desc"})
            use_cache (bool, optional): Whether to use cached responses (default: True)

        Returns:
            dict: The JSON response containing asset and metrics data

        Raises:
            requests.exceptions.RequestException: If the request fails
        """
        # Build metrics where clause
        metrics_where = {}
        if metric_keys:
            metrics_where["metricKeys"] = metric_keys
        if created_before:
            metrics_where["createdAt_lt"] = created_before

        # Build metrics arguments
        metrics_args = []
        if metrics_where:
            # Convert to GraphQL syntax (no quotes around keys)
            where_parts = []
            for key, value in metrics_where.items():
                where_parts.append(f"{key}: {json.dumps(value)}")
            where_str = "{" + ", ".join(where_parts) + "}"
            metrics_args.append(f"where: {where_str}")

        if metrics_limit is not None:
            metrics_args.append(f"limit: {metrics_limit}")

        # Default order to createdAt desc if not specified
        order_clause = order or {"createdAt": "desc"}
        order_parts = []
        for key, value in order_clause.items():
            order_parts.append(f"{key}: {value}")
        order_str = "{" + ", ".join(order_parts) + "}"
        metrics_args.append(f"order: {order_str}")

        metrics_args_str = f"({', '.join(metrics_args)})" if metrics_args else ""

        # Build GraphQL query
        query = f"""
        {{
          assets(where: {{slugs: [{json.dumps(slug)}]}}, limit: 1) {{
            id
            slug
            logoUrl
            metrics{metrics_args_str} {{
              defaultValue
              createdAt
            }}
          }}
        }}
        """

        return self._execute_query(query, use_cache=use_cache)

    def get_validators(self, symbol, limit=1, use_cache=True):
        """
        Query validators for a specific symbol

        Args:
            symbol (str): Asset symbol to query
            limit (int, optional): Maximum number of metrics to return (default: 1)
            use_cache (bool, optional): Whether to use cached responses (default: True)

        Returns:
            dict: The JSON response containing validator data
        """
        query = f"""
        {{
          assets(where: {{ symbols: ["{symbol}"] }}, limit: 1) {{
            id
            name
            slug
            description
            symbol
            metrics(where: {{ metricKeys: ["active_validators"] }}, limit: {limit}) {{
              metricKey
              label
              defaultValue
            }}
          }}
        }}
        """

        return self._execute_query(query, use_cache=use_cache)

    def get_staked_tokens(self, asset_slug, limit=1, use_cache=True):
        """
        Query the staked tokens

        Args:
            asset_slug (str): Asset slug to query
            limit (int, optional): Maximum number of validators to return (default: 1)
            use_cache (bool, optional): Whether to use cached responses (default: True)

        Returns:
            dict: The JSON response containing staked tokens data
        """
        query = """
               {{
         rewardOptions(
           where: {{
             inputAsset: {{ slugs: ["{asset_slug}"] }}
             typeKeys: ["pos"]
           }}
           limit: 10
           offset: 0
         ) {{
           providers(limit: 1) {{
             slug
           }}
           validators(limit: {limit}) {{
             address
             status {{
               label
             }}
             metrics(where: {{ metricKeys: ["staked_tokens"] }}, limit: 1) {{
               metricKey
               defaultValue
             }}
           }}
         }}
        }}""".format(asset_slug=asset_slug, limit=limit)

        return self._execute_query(query, use_cache=use_cache)

    def get_provider_staked_tokens(self, asset_slug, limit=100, is_active=True, use_cache=True):
        """
        Query all providers for an asset and return their staked token amounts.

        Args:
            asset_slug (str): Asset slug to query (e.g., "solana")
            limit (int, optional): Maximum number of reward options/providers to return (default: 100)
            is_active (bool|None, optional): If True/False, results are filtered client-side by provider.isActive.
                                             Set to None to skip filtering (default: True).
            use_cache (bool, optional): Whether to use cached responses (default: True)

        Returns:
            dict: The JSON response containing provider slugs and their staked token metrics
        """
        query = f"""
        {{
          rewardOptions(
            where: {{
              inputAsset: {{ slugs: [{json.dumps(asset_slug)}] }}
              typeKeys: ["pos"]
            }}
            limit: {limit}
            order: {{ metricKey_desc: "staked_tokens" }}
          ) {{
            id
            providers(limit: 1) {{
              slug
              isActive
            }}
            metrics(where: {{ metricKeys: ["staked_tokens"] }}, limit: 1) {{
              metricKey
              defaultValue
            }}
          }}
        }}
        """

        result = self._execute_query(query, use_cache=use_cache)

        if isinstance(is_active, bool):
            filtered = []
            for ro in result.get("data", {}).get("rewardOptions", []):
                provider = (ro.get("providers") or [{}])[0]
                if provider.get("isActive") is is_active:
                    filtered.append(ro)
            if "data" in result and "rewardOptions" in result["data"]:
                result["data"]["rewardOptions"] = filtered

        return result

    def get_provider_stake_for_asset(self, provider_slug, asset_slug, limit=20, validators_limit=0, use_cache=True):
        """
        Query staked tokens for a specific provider on a given asset.

        Args:
            provider_slug (str): Provider slug to query (e.g., "kiln")
            asset_slug (str): Asset slug to query (e.g., "solana")
            limit (int, optional): Maximum number of reward options to return (default: 20)
            validators_limit (int, optional): Number of validators to include (0 to skip, default: 0)
            use_cache (bool, optional): Whether to use cached responses (default: True)

        Returns:
            dict: The JSON response containing staked token metrics for the provider
        """
        validators_block = ""
        if validators_limit and validators_limit > 0:
            validators_block = f"""
            validators(limit: {validators_limit}) {{
              id
              address
            }}"""

        query = f"""
        {{
          rewardOptions(
            where: {{
              providers: {{ slugs: [{json.dumps(provider_slug)}] }}
              inputAsset: {{ slugs: [{json.dumps(asset_slug)}] }}
              typeKeys: ["pos"]
            }}
            limit: {limit}
            order: {{ metricKey_desc: "staked_tokens" }}
          ) {{
            id
            inputAssets(limit: 1) {{ slug }}
            providers(limit: 1) {{ slug }}
            metrics(where: {{ metricKeys: ["staked_tokens"] }}, limit: 2) {{
              defaultValue
            }}
            {validators_block}
          }}
        }}
        """

        return self._execute_query(query, use_cache=use_cache)

    def get_total_staked_tokens(self, asset_slug, metrics_limit=1, use_cache=True):
        """
        Get the staked_tokens metric for an asset (aggregate, not per-provider).

        Args:
            asset_slug (str): Asset slug to query (e.g., "solana")
            metrics_limit (int, optional): Number of metric records to return (default: 1, latest)
            use_cache (bool, optional): Whether to use cached responses (default: True)

        Returns:
            dict: The JSON response containing the asset's staked_tokens metric(s)
        """
        query = f"""
        {{
          assets(where: {{ slugs: [{json.dumps(asset_slug)}] }}, limit: 1) {{
            slug
            metrics(
              where: {{ metricKeys: ["staked_tokens"] }}
              order: {{ createdAt: desc }}
              limit: {metrics_limit}
            ) {{
              metricKey
              defaultValue
              createdAt
            }}
          }}
        }}
        """

        return self._execute_query(query, use_cache=use_cache)

    def get_provider_stake_shares(self, asset_slug, limit=200, is_active=True, include_reward_rate=True, use_cache=True):
        """
        Get provider staked tokens plus share of the asset's total staked tokens.

        Args:
            asset_slug (str): Asset slug to query (e.g., "solana")
            limit (int, optional): Maximum number of reward options/providers to return (default: 200)
            is_active (bool|None, optional): If True/False, providers are filtered client-side on isActive.
                                             Set to None to skip filtering (default: True).
            include_reward_rate (bool, optional): Include provider reward_rate metric if available (default: True)
            use_cache (bool, optional): Whether to use cached responses (default: True)

        Returns:
            dict: {
                "total_staked_tokens": <float|None>,
                "untracked_staked_tokens": <float|None>,
                "untracked_share": <float|None>,
                "providers": [
                    {
                        "provider": <slug>,
                        "staked_tokens": <float|None>,
                        "share": <float|None>,
                        "reward_rate": <float|None>
                    }, ...
                ]
            }
        """
        metric_keys = ["staked_tokens"]
        if include_reward_rate:
            metric_keys.append("reward_rate")

        query = f"""
        {{
          rewardOptions(
            where: {{
              inputAsset: {{ slugs: [{json.dumps(asset_slug)}] }}
              typeKeys: ["pos"]
            }}
            limit: {limit}
            order: {{ metricKey_desc: "staked_tokens" }}
          ) {{
            providers(limit: 1) {{
              slug
              name
              isActive
            }}
            metrics(where: {{ metricKeys: {json.dumps(metric_keys)} }}, limit: 5) {{
              metricKey
              defaultValue
            }}
          }}
        }}
        """

        ro_result = self._execute_query(query, use_cache=use_cache)

        # Fetch total staked tokens (aggregate)
        total_resp = self.get_total_staked_tokens(asset_slug=asset_slug, metrics_limit=1, use_cache=use_cache)
        total = None
        try:
            total = total_resp["data"]["assets"][0]["metrics"][0]["defaultValue"]
        except Exception:
            total = None

        providers = []
        reward_options = ro_result.get("data", {}).get("rewardOptions", []) or []

        for ro in reward_options:
            provider_info = (ro.get("providers") or [{}])[0]
            if isinstance(is_active, bool) and provider_info.get("isActive") is not is_active:
                continue

            metrics = ro.get("metrics") or []
            staked = None
            reward_rate = None
            for m in metrics:
                if m.get("metricKey") == "staked_tokens":
                    staked = m.get("defaultValue")
                elif m.get("metricKey") == "reward_rate":
                    reward_rate = m.get("defaultValue")

            share = None
            if total not in (None, 0) and staked is not None:
                try:
                    share = staked / total
                except Exception:
                    share = None

            providers.append({
                "provider": provider_info.get("slug"),
                "name": provider_info.get("name"),
                "staked_tokens": staked,
                "reward_rate": reward_rate,
                "share": share,
            })

        sum_tracked = sum(
            p["staked_tokens"] for p in providers if p.get("staked_tokens") not in (None, 0)
        ) if providers else 0
        untracked = None
        untracked_share = None
        if total not in (None, 0):
            try:
                untracked = total - sum_tracked
                untracked_share = untracked / total
            except Exception:
                untracked = None
                untracked_share = None

        return {
            "total_staked_tokens": total,
            "untracked_staked_tokens": untracked,
            "untracked_share": untracked_share,
            "providers": providers,
        }

    def get_providers(self, asset_slug, is_verified=True, order_by_metric="assets_under_management", limit=10, metric_keys=None, use_cache=True):
        """
        Query providers for a specific asset from the StakingRewards API.

        Args:
            asset_slug (str): Asset slug to filter providers by (e.g., "cosmos", "ethereum-2-0")
            is_verified (bool, optional): Filter for verified providers only (default: True)
            order_by_metric (str, optional): Metric key to order by descending (default: "assets_under_management")
            limit (int, optional): Maximum number of providers to return (default: 10)
            metric_keys (list, optional): List of metric keys to fetch (default: ["reward_rate"])
            use_cache (bool, optional): Whether to use cached responses (default: True)

        Returns:
            dict: The JSON response containing providers data

        Raises:
            requests.exceptions.RequestException: If the request fails
        """
        # Default metric keys
        if metric_keys is None:
            metric_keys = ["reward_rate"]

        # Build providers where clause
        where_parts = []
        where_parts.append(f"rewardOptions: {{inputAsset: {{slugs: [{json.dumps(asset_slug)}]}}}}")
        where_parts.append(f"isVerified: {json.dumps(is_verified)}")
        providers_where = "{" + ", ".join(where_parts) + "}"

        # Build order clause
        order_clause = f"{{metricKey_desc: {json.dumps(order_by_metric)}}}"

        # Build GraphQL query
        query = f"""
        {{
          providers(
            where: {providers_where}
            order: {order_clause}
            limit: {limit}
          ) {{
            slug
            rewardOptions(
              where: {{inputAsset: {{slugs: [{json.dumps(asset_slug)}]}}}}
              limit: 1
            ) {{
              metrics(
                where: {{metricKeys: {json.dumps(metric_keys)}}}
                limit: 1
              ) {{
                defaultValue
              }}
            }}
          }}
        }}
        """

        return self._execute_query(query, use_cache=use_cache)

    def get_metrics(self, asset=None, provider=None, reward_option=None, validator=None, metric_keys=None, limit=1, use_cache=True):
        """
        Query metrics from the StakingRewards API.

        When all filters (asset, provider, reward_option, validator) are None,
        this returns global market metrics.

        Args:
            asset (str, optional): Asset filter (default: None for global metrics)
            provider (str, optional): Provider filter (default: None)
            reward_option (str, optional): Reward option filter (default: None)
            validator (str, optional): Validator filter (default: None)
            metric_keys (list, optional): List of metric keys to fetch (default: ["marketcap"])
            limit (int, optional): Maximum number of metrics to return (default: 1)
            use_cache (bool, optional): Whether to use cached responses (default: True)

        Returns:
            dict: The JSON response containing metrics data

        Raises:
            requests.exceptions.RequestException: If the request fails
        """
        # Default metric keys
        if metric_keys is None:
            metric_keys = ["marketcap"]

        # Build where clause
        where_parts = []

        # For None values, use null in GraphQL
        where_parts.append(f"asset: {json.dumps(asset) if asset is not None else 'null'}")
        where_parts.append(f"provider: {json.dumps(provider) if provider is not None else 'null'}")
        where_parts.append(f"rewardOption: {json.dumps(reward_option) if reward_option is not None else 'null'}")
        where_parts.append(f"validator: {json.dumps(validator) if validator is not None else 'null'}")
        where_parts.append(f"metricKeys: {json.dumps(metric_keys)}")

        where_str = "{" + ", ".join(where_parts) + "}"

        # Build GraphQL query
        query = f"""
        {{
          metrics(
            where: {where_str}
            limit: {limit}
          ) {{
            defaultValue
            changeAbsolutes
            changePercentages
            createdAt
          }}
        }}
        """

        return self._execute_query(query, use_cache=use_cache)

    # Query methods will be added here as you provide them
