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

    # Query methods will be added here as you provide them
