import math
from typing import Optional

import matplotlib.pyplot as plt
import numpy as np


def _extract_points(stake_shares_response):
    """
    Extract (stake, reward_rate) pairs from get_provider_stake_shares response.

    Returns a list of (stake, reward_rate) tuples with both values present and > 0.
    """
    providers = stake_shares_response.get("providers") or []
    points = []
    for p in providers:
        stake = p.get("staked_tokens")
        rr = p.get("reward_rate")
        if stake is None or rr is None:
            continue
        try:
            stake_val = float(stake)
            rr_val = float(rr)
        except (TypeError, ValueError):
            continue
        if stake_val <= 0 or rr_val <= 0:
            continue
        points.append((stake_val, rr_val))
    return points


def plot_reward_rate_vs_stake(stake_shares_response, ax: Optional[plt.Axes] = None, title: Optional[str] = None, logx: bool = True, logy: bool = True):
    """
    Scatter + simple regression line for reward_rate vs staked_tokens.

    Args:
        stake_shares_response (dict): Response from get_provider_stake_shares
        ax (matplotlib.axes.Axes, optional): Axis to draw on; creates a new one if None.
        title (str, optional): Plot title.
        logx (bool, optional): Log scale for x (stake). Default True.
        logy (bool, optional): Log scale for y (reward rate). Default True.

    Returns:
        matplotlib.axes.Axes: The axis with the plot.

    Raises:
        ValueError: If fewer than two data points are available.
    """
    points = _extract_points(stake_shares_response)
    if len(points) < 2:
        raise ValueError("Need at least two providers with staked_tokens and reward_rate to plot regression.")

    stakes, reward_rates = zip(*points)
    stakes = np.array(stakes)
    reward_rates = np.array(reward_rates)

    ax = ax or plt.subplots(figsize=(7, 5))[1]
    ax.scatter(stakes, reward_rates, alpha=0.6, label="providers")

    # Regression on log-transformed data for robustness across magnitudes
    log_stakes = np.log(stakes)
    log_rr = np.log(reward_rates)
    slope, intercept = np.polyfit(log_stakes, log_rr, 1)
    fitted = np.exp(intercept) * stakes ** slope
    ax.plot(stakes, fitted, color="orange", label=f"fit: y = {math.exp(intercept):.3g} * x^{slope:.2f}")

    if logx:
        ax.set_xscale("log")
    if logy:
        ax.set_yscale("log")

    ax.set_xlabel("Staked tokens")
    ax.set_ylabel("Reward rate")
    if title:
        ax.set_title(title)
    ax.legend()
    ax.grid(True, which="both", ls="--", alpha=0.3)
    return ax
