import os
import json
import hashlib
import requests
from pathlib import Path
from typing import Any, Dict, Optional


class RatedAPIClient:
    """
    Client for interacting with the Rated Network REST API.

    Auth:
      - Set env var RATED_API_KEY
      - Uses header: Authorization: Bearer <token>

    Note on "total staked":
      Rated exposes network-wide stake totals in the "network overview" endpoints
      for some chains (e.g., Solana/Polygon/Ethereum). For other supported networks,
      the public docs don't clearly expose an equivalent network-level stake-total
      endpoint, so this client raises NotImplementedError for those slugs.
    """

    DEFAULT_BASE_URL = "https://api.rated.network"
    DEFAULT_API_KEY_ENV = "RATED_API_KEY"

    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: str = DEFAULT_BASE_URL,
        api_key_env: str = DEFAULT_API_KEY_ENV,
        timeout_s: int = 30,
        default_rated_network: Optional[str] = None,  # e.g. "mainnet", "hoodi", "holesky" (ETH-only)
    ) -> None:
        self.api_key = api_key or os.getenv(api_key_env)
        if not self.api_key:
            raise ValueError(
                f"Missing Rated API key. Provide api_key=... or set env var {api_key_env}."
            )

        self.base_url = base_url.rstrip("/")
        self.timeout_s = timeout_s
        self.default_rated_network = default_rated_network

        self._session = requests.Session()
        self._session.headers.update({"Authorization": f"Bearer {self.api_key}"})

    def _get(self, path: str, params: Optional[Dict[str, Any]] = None, headers: Optional[Dict[str, str]] = None) -> Any:
        url = f"{self.base_url}{path}"
        h = {}
        if self.default_rated_network:
            # Used by some Ethereum endpoints (X-Rated-Network: mainnet/hoodi/holesky)
            h["X-Rated-Network"] = self.default_rated_network
        if headers:
            h.update(headers)

        resp = self._session.get(url, params=params or {}, headers=h, timeout=self.timeout_s)
        resp.raise_for_status()
        return resp.json()

    @staticmethod
    def _pick_timewindow_row(rows: Any, time_window: str) -> Dict[str, Any]:
        """
        Rated overview endpoints typically return a JSON array of objects with a 'timeWindow' field.
        """
        if not isinstance(rows, list) or not rows:
            raise ValueError(f"Unexpected response shape (expected non-empty list), got: {type(rows)}")

        # Prefer exact match, else first row
        for r in rows:
            if isinstance(r, dict) and r.get("timeWindow") == time_window:
                return r
        return rows[0] if isinstance(rows[0], dict) else {}

    def get_total_staked_amount(self, token_slug: str, time_window: str = "1d") -> Dict[str, Any]:
        """
        Return the network-wide total staked amount for a given token slug.

        Supported slugs (implemented):
          - solana -> /v1/solana/network/overview -> totalDelegatedStake
          - matic-network (Polygon) -> /v1/polygon/network/overview -> totalStake
          - ethereum-2-0 -> /v0/eth/network/overview -> activeStake

        Returns:
          {
            "slug": <token_slug>,
            "timeWindow": <time_window or returned timeWindow>,
            "totalStaked": <raw value from API>,
            "sourceField": <field name>,
            "endpoint": <endpoint path used>
          }
        """
        slug = token_slug.strip().lower()

        if slug == "solana":
            endpoint = "/v1/solana/network/overview"
            rows = self._get(endpoint)
            row = self._pick_timewindow_row(rows, time_window)
            return {
                "slug": slug,
                "timeWindow": row.get("timeWindow"),
                "totalStaked": row.get("totalDelegatedStake"),
                "sourceField": "totalDelegatedStake",
                "endpoint": endpoint,
            }

        if slug == "matic-network":  # Polygon
            endpoint = "/v1/polygon/network/overview"
            rows = self._get(endpoint)
            row = self._pick_timewindow_row(rows, time_window)
            return {
                "slug": slug,
                "timeWindow": row.get("timeWindow"),
                "totalStaked": row.get("totalStake"),
                "sourceField": "totalStake",
                "endpoint": endpoint,
            }

        if slug == "ethereum-2-0":
            # Note: Ethereum network overview is documented under v0 for "activeStake".
            endpoint = "/v0/eth/network/overview"
            rows = self._get(endpoint, params={"window": time_window})
            row = self._pick_timewindow_row(rows, time_window)
            return {
                "slug": slug,
                "timeWindow": row.get("timeWindow"),
                "totalStaked": row.get("activeStake"),
                "sourceField": "activeStake",
                "endpoint": endpoint,
            }

        # Supported by your project list, but no obvious network-wide "total stake" overview endpoint in docs:
        not_implemented = {
            "cardano",
            "celestia",
            "avalanche",
            "polkadot",
            "cosmos",
            "eigenlayer",
            "babylon",
        }
        if slug in not_implemented:
            raise NotImplementedError(
                f"No network-level 'total staked' overview endpoint is clearly documented for slug '{slug}' "
                f"(at least not in the same way as Solana/Polygon/Ethereum). "
                f"If you want, I can adapt this to compute a proxy metric (e.g., sum validator stake states where available), "
                f"but that may be expensive and incomplete depending on the chain."
            )

        raise ValueError(f"Unknown token slug: {token_slug}")

    def get_total_staked_amounts_for_slugs(self, slugs, time_window: str = "1d") -> Dict[str, Any]:
        """
        Convenience method: fetch totals for multiple slugs.
        Returns a dict: {slug: result_or_error}
        """
        out: Dict[str, Any] = {}
        for s in slugs:
            try:
                out[s] = self.get_total_staked_amount(s, time_window=time_window)
            except Exception as e:
                out[s] = {"slug": s, "error": f"{type(e).__name__}: {e}"}
        return out


if __name__ == "__main__":
    slugs = [
        "solana",
        "cardano",
        "celestia",
        "ethereum-2-0",
        "matic-network",  # Polygon
        "avalanche",
        "polkadot",
        "cosmos",
        "eigenlayer",
        "babylon",
    ]

    client = RatedAPIClient()
    results = client.get_total_staked_amounts_for_slugs(slugs, time_window="1d")
    print(json.dumps(results, indent=2))