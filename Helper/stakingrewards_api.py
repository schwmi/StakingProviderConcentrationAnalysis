import os
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

    # Query methods will be added here as you provide them
