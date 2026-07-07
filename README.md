# Crypto Staking Analysis

Research workspace for analyzing staking provider concentration and reward characteristics with the StakingRewards API.

## Quick Start

1. Create your local environment file:

```bash
cp .env.example .env
```

2. Set your API key in `.env`:

```bash
X_API_KEY=your_stakingrewards_api_key
```

3. Start Jupyter in Docker:

```bash
./run_jupyter.sh
```

4. Open the Jupyter URL printed in the terminal and run `StakingRewardsAnalysis.ipynb`.

## Repository Layout

- `StakingRewardsAnalysis.ipynb`: Primary analysis notebook.
- `Helper/stakingrewards_api.py`: StakingRewards API client and query helpers.
- `Helper/solana_onchain.py`: Solana JSON-RPC adapter (`getVoteAccounts`) with the same caching style, used for the on-chain Solana coverage.
- `api_response_cache/`: Versioned StakingRewards response cache for reproducible and offline analysis.
- `onchain_cache/`: Versioned Solana RPC response cache.
- `figures/`: Exported figures from notebook runs.
- `tables/`: Generated tables from notebook runs.
- `Dockerfile`: Jupyter image definition.
- `run_jupyter.sh`: Local build/run wrapper for Jupyter.

## Asset Eligibility

An asset is only used for the concentration analysis if StakingRewards covers at
least 70% of its total staked tokens and it has more than 30 tracked providers.
The notebook records every candidate asset together with an `exclusion_reason`
column, so excluded chains remain visible in the intermediate results table.

Some prominent networks fall below the coverage threshold on StakingRewards. The
most notable example is **Solana**: StakingRewards tracks only ~36% of the total
staked SOL, even though Solana has enough providers. The same coverage limitation
applies to other chains with many independent validators (e.g. Polkadot,
Avalanche).

### Solana via on-chain data

Because Solana is too important to omit, it is instead pulled directly from
Solana's public JSON-RPC endpoint (`getVoteAccounts`, no authentication), which
returns the complete validator set (~100% coverage). The raw response is cached
under `onchain_cache/` using a SHA-256 request key so the analysis stays
reproducible and offline, and the same metric functions are applied as for the
StakingRewards assets. This data is at validator / vote-account level rather
than operator level, so it is a lower bound on operator-level concentration.
Delinquent validators can still have activated stake, but the default analysis
uses only the current voting set. The snapshot date also differs from the
StakingRewards snapshot. These caveats are noted in the report.

## Notes

- `run_jupyter.sh` requires `X_API_KEY` (from `.env` or your shell environment) and mounts this repo to `/home/jovyan/work`.
- If dependencies change, update `Dockerfile` and rerun `./run_jupyter.sh` to rebuild the image.
- `.env` is ignored by git; `.env.example` is the committed template.
