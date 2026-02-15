# Crypto Staking Analysis

Small research workspace for analyzing staking-provider concentration and reward characteristics with the StakingRewards API.

## Quick Start

1. Create a `.env` file in the project root:

```bash
X_API_KEY=your_stakingrewards_api_key
```

2. Start Jupyter in Docker:

```bash
./run_jupyter.sh
```

3. Open the Jupyter URL shown in the terminal and run the notebooks.

## Main Notebooks

- `StakingRewardsAnalysis.ipynb`: Primary analysis notebook (provider concentration, Lorenz/Gini/HHI/Nakamoto, charts).

## Project Layout

- `Helper/`: Python helper package (API client).
- `figures/`: Exported charts and plots.
- `api_response_cache/`: Local API response cache.
- `Dockerfile`: Jupyter base image definition.
- `run_jupyter.sh`: Build + run helper for local notebook work.

## Notes

- `run_jupyter.sh` mounts the repo into the container at `/home/jovyan/work`.
- If you change dependencies, update `Dockerfile` and rebuild via `./run_jupyter.sh`.
