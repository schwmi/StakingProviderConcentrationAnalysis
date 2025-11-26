import os
import json
import requests


class StakingRewardsAPIClient:
    """
    Client for interacting with the StakingRewards GraphQL API.
    """

    BASE_URL = "https://api.stakingrewards.com/public/query"

    def __init__(self, api_key=None):
        """
        Initialize the StakingRewards API client.

        Args:
            api_key (str, optional): API key for authentication.
                                     If not provided, will read from X_API_KEY environment variable.
        """
        self.api_key = api_key or os.getenv('X_API_KEY')
        if not self.api_key:
            raise ValueError("API key must be provided or set in X_API_KEY environment variable")

        self.headers = {
            "X-API-KEY": self.api_key,
            "Content-Type": "application/json"
        }

    def _execute_query(self, query, variables=None):
        """
        Execute a GraphQL query against the StakingRewards API.

        Args:
            query (str): The GraphQL query string
            variables (dict, optional): Variables for the GraphQL query

        Returns:
            dict: The JSON response from the API

        Raises:
            requests.exceptions.RequestException: If the request fails
        """
        payload = {"query": query}
        if variables:
            payload["variables"] = variables

        response = requests.post(
            self.BASE_URL,
            json=payload,
            headers=self.headers
        )
        response.raise_for_status()
        return response.json()

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

    def get_assets(self, symbols=None, limit=None, where=None):
        """
        Query assets from the StakingRewards API.

        Args:
            symbols (list, optional): List of asset symbols to filter by (e.g., ["ETH", "BTC"])
            limit (int, optional): Maximum number of results to return
            where (dict, optional): Additional where conditions for filtering

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

        return self._execute_query(query)

    def get_asset_metrics(self, slug, metric_keys=None, created_before=None, metrics_limit=None, order=None):
        """
        Query an asset with its metrics from the StakingRewards API.

        Args:
            slug (str): Asset slug to query (e.g., "polkadot", "ethereum-2-0")
            metric_keys (list, optional): List of metric keys to filter (e.g., ["reward_rate"])
            created_before (str, optional): Filter metrics created before this date (ISO format: "2023-06-28")
            metrics_limit (int, optional): Maximum number of metrics to return
            order (dict, optional): Order clause for metrics (default: {"createdAt": "desc"})

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

        return self._execute_query(query)

    def get_providers(self, asset_slug, is_verified=True, order_by_metric="assets_under_management", limit=10, metric_keys=None):
        """
        Query providers for a specific asset from the StakingRewards API.

        Args:
            asset_slug (str): Asset slug to filter providers by (e.g., "cosmos", "ethereum-2-0")
            is_verified (bool, optional): Filter for verified providers only (default: True)
            order_by_metric (str, optional): Metric key to order by descending (default: "assets_under_management")
            limit (int, optional): Maximum number of providers to return (default: 10)
            metric_keys (list, optional): List of metric keys to fetch (default: ["reward_rate"])

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

        return self._execute_query(query)

    def get_metrics(self, asset=None, provider=None, reward_option=None, validator=None, metric_keys=None, limit=1):
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

        return self._execute_query(query)

    # Query methods will be added here as you provide them
