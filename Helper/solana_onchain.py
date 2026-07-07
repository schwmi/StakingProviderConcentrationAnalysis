import os
import json
import hashlib
import requests
from pathlib import Path
from datetime import datetime, timezone


class SolanaOnChainClient:
    """
    Minimal adapter for Solana's public JSON-RPC endpoint.

    Solana is not sufficiently covered on StakingRewards (only ~36% of staked
    SOL), so its stake distribution is instead read directly from the chain via
    the ``getVoteAccounts`` RPC method, which returns the active stake of every
    vote account / validator and requires no authentication.

    Responses are cached on disk in the same style as ``StakingRewardsAPIClient``
    (a SHA-256 key over the request, wrapped with ``_cache_meta`` + ``response``)
    so that the analysis can be reproduced fully offline from the committed
    cache, without any network access.

    The returned concentration inputs are validator-level, not operator-level:
    a single operator can run multiple vote accounts, so these data are best
    interpreted as a lower bound on operator concentration.
    """

    DEFAULT_RPC_URL = "https://api.mainnet-beta.solana.com"
    LAMPORTS_PER_SOL = 1_000_000_000

    def __init__(self, rpc_url=None, cache_dir="onchain_cache"):
        """
        Args:
            rpc_url (str, optional): Solana JSON-RPC endpoint. Falls back to the
                SOLANA_RPC_URL environment variable, then to the public mainnet
                endpoint.
            cache_dir (str, optional): Directory for cached RPC responses
                (default: "onchain_cache").
        """
        self.rpc_url = rpc_url or os.getenv("SOLANA_RPC_URL") or self.DEFAULT_RPC_URL
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)

    def _get_cache_key(self, method, params=None):
        """Generate a unique cache key for an RPC method and its params."""
        cache_data = {
            "rpc_url": self.rpc_url,
            "method": method,
            "params": params or [],
        }
        cache_string = json.dumps(cache_data, sort_keys=True)
        return hashlib.sha256(cache_string.encode()).hexdigest()

    def _get_legacy_cache_key(self, method, params=None):
        """
        Generate the cache key used before rpc_url was included.

        This preserves offline reproducibility for older committed cache files.
        New network responses are written under the rpc_url-aware key.
        """
        cache_data = {"method": method, "params": params or []}
        cache_string = json.dumps(cache_data, sort_keys=True)
        return hashlib.sha256(cache_string.encode()).hexdigest()

    def _read_cache_file(self, cache_file):
        with open(cache_file, "r", encoding="utf-8") as f:
            cached = json.load(f)
        if isinstance(cached, dict) and "response" in cached:
            return cached["response"]
        return cached

    def _raise_for_rpc_error(self, result, method):
        if isinstance(result, dict) and result.get("error"):
            raise RuntimeError(f"Solana RPC {method} failed: {result['error']}")
        if not isinstance(result, dict) or "result" not in result:
            raise RuntimeError(f"Solana RPC {method} returned no result")

    def _rpc(self, method, params=None, use_cache=True):
        """
        Execute a JSON-RPC call with on-disk caching.

        Args:
            method (str): RPC method name (e.g. "getVoteAccounts").
            params (list, optional): RPC params.
            use_cache (bool, optional): Whether to use cached responses
                (default: True).

        Returns:
            dict: The parsed JSON-RPC response.
        """
        cache_key = self._get_cache_key(method, params)
        cache_file = self.cache_dir / f"{cache_key}.json"

        if use_cache and cache_file.exists():
            result = self._read_cache_file(cache_file)
            self._raise_for_rpc_error(result, method)
            return result

        legacy_cache_file = (
            self.cache_dir / f"{self._get_legacy_cache_key(method, params)}.json"
        )
        if use_cache and legacy_cache_file.exists():
            result = self._read_cache_file(legacy_cache_file)
            self._raise_for_rpc_error(result, method)
            return result

        payload = {"jsonrpc": "2.0", "id": 1, "method": method, "params": params or []}
        response = requests.post(self.rpc_url, json=payload, timeout=60)
        response.raise_for_status()
        result = response.json()
        self._raise_for_rpc_error(result, method)

        try:
            with open(cache_file, "w", encoding="utf-8") as f:
                cache_payload = {
                    "_cache_meta": {
                        "retrieved_at_utc": datetime.now(timezone.utc).isoformat(),
                        "method": method,
                        "params": params or [],
                        "cache_key": cache_key,
                        "rpc_url": self.rpc_url,
                    },
                    "response": result,
                }
                json.dump(cache_payload, f, indent=2)
        except IOError:
            pass

        return result

    def get_vote_accounts(self, commitment="finalized", use_cache=True):
        """Return the raw ``getVoteAccounts`` result (current + delinquent)."""
        return self._rpc(
            "getVoteAccounts",
            params=[{"commitment": commitment}],
            use_cache=use_cache,
        )

    def get_validator_stakes(
        self,
        commitment="finalized",
        include_delinquent=False,
        identity="vote_account",
        use_cache=True,
    ):
        """
        Return the per-validator effective stake in a shape compatible with the
        concentration-metric functions used for the StakingRewards assets.

        Args:
            commitment (str, optional): RPC commitment level.
            include_delinquent (bool, optional): Include delinquent validators
                (default: False). Delinquent validators can still have activated
                stake, but they are not in the current voting set.
            identity (str, optional): Which validator identifier to expose in
                the backward-compatible ``provider`` field. Use ``vote_account``
                (default) or ``node_identity``.
            use_cache (bool, optional): Whether to use cached responses.

        Returns:
            tuple[list[dict], float]: A list of
            ``{"provider": <identifier>, "value": <active stake in SOL>, ...}``
            entries (one per active validator), and the total active stake in SOL.
        """
        if identity not in {"vote_account", "node_identity"}:
            raise ValueError("identity must be 'vote_account' or 'node_identity'")

        result = self.get_vote_accounts(commitment=commitment, use_cache=use_cache)["result"]

        accounts = [
            {**account, "_vote_account_status": "current"}
            for account in result.get("current", [])
        ]
        if include_delinquent:
            accounts += [
                {**account, "_vote_account_status": "delinquent"}
                for account in result.get("delinquent", [])
            ]

        identity_field = "votePubkey" if identity == "vote_account" else "nodePubkey"

        validators = [
            {
                "provider": v[identity_field],
                "identity_level": identity,
                "vote_pubkey": v["votePubkey"],
                "node_pubkey": v.get("nodePubkey"),
                "vote_account_status": v["_vote_account_status"],
                "value": v["activatedStake"] / self.LAMPORTS_PER_SOL,
            }
            for v in accounts
            if v.get("activatedStake", 0) > 0 and v.get(identity_field)
        ]
        total = sum(v["value"] for v in validators)
        return validators, total
