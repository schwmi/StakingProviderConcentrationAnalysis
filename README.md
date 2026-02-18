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
- `Helper/stakingrewards_api.py`: API client and query helpers.
- `api_response_cache/`: Versioned API response cache for reproducible and offline analysis.
- `figures/`: Exported figures from notebook runs.
- `tables/`: Generated tables from notebook runs.
- `Dockerfile`: Jupyter image definition.
- `run_jupyter.sh`: Local build/run wrapper for Jupyter.

## Notes

- `run_jupyter.sh` requires `X_API_KEY` (from `.env` or your shell environment) and mounts this repo to `/home/jovyan/work`.
- If dependencies change, update `Dockerfile` and rerun `./run_jupyter.sh` to rebuild the image.
- `.env` is ignored by git; `.env.example` is the committed template.
