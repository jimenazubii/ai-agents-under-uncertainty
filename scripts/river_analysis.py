"""
Part 3 analysis: value function, optimal policy, convergence and Monte Carlo
evaluation of the river-crossing MDP.

    python scripts/river_analysis.py

Writes docs/figures/river_value_policy.png and docs/figures/river_convergence.png
and prints a comparison between the optimal policy and a naive baseline.
"""

import random
import sys
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from river_mdp import (ACTIONS, all_states, create_river_grid, find_exit,  # noqa: E402
                       reward, river_strength_for_cols, transition_probs, value_iteration)

FIGURES = ROOT / "docs" / "figures"
ROWS, COLS = 7, 6
ARROWS = {"up": (0, -0.3), "down": (0, 0.3), "left": (-0.3, 0), "right": (0.3, 0)}


def convergence(grid, strengths, gamma=0.99, theta=1e-6):
    """Run Value Iteration recording the largest change (delta) per sweep."""
    states, exit_pos = all_states(grid), find_exit(grid)
    V = {s: 0.0 for s in states}
    deltas = []
    while True:
        delta = 0.0
        for s in states:
            if s == exit_pos:
                continue
            best = max(
                sum(p * (reward(grid, s, a, sp, exit_pos) + gamma * V[sp])
                    for sp, p in transition_probs(grid, strengths, s, a).items())
                for a in ACTIONS
            )
            delta = max(delta, abs(V[s] - best))
            V[s] = best
        deltas.append(delta)
        if delta < theta:
            return deltas


def naive_policy(grid):
    """Baseline: always swim right; in the last column move towards the exit."""
    exit_row, last = find_exit(grid)[0], len(grid[0]) - 1
    policy = {}
    for s in all_states(grid):
        if s[1] < last:
            policy[s] = "right"
        else:
            policy[s] = "up" if s[0] > exit_row else "down" if s[0] < exit_row else "stay"
    return policy


def simulate(grid, strengths, policy, rng, max_steps=200):
    """One episode from (0, 0). Returns (reached_exit, steps)."""
    exit_pos, s = find_exit(grid), (0, 0)
    for t in range(max_steps):
        if s == exit_pos:
            return True, t
        probs = transition_probs(grid, strengths, s, policy[s])
        s = rng.choices(list(probs), weights=list(probs.values()))[0]
    return s == exit_pos, max_steps


def plot_value_policy(grid, strengths, V, policy, path):
    rows, cols = len(grid), len(grid[0])
    values = np.full((rows, cols), np.nan)
    for (i, j), v in V.items():
        values[i, j] = v
    fig, ax = plt.subplots(figsize=(6.4, 6.2))
    im = ax.imshow(values, cmap="viridis")
    fig.colorbar(im, ax=ax, fraction=0.046, label="V(s)")
    for i in range(rows):
        for j in range(cols):
            if grid[i][j] == "I":
                ax.add_patch(plt.Rectangle((j - .5, i - .5), 1, 1, color="#8B5A2B"))
                ax.text(j, i, "island", ha="center", va="center", color="white", fontsize=8)
            elif grid[i][j] == "E":
                # Terminal state: V = 0 by definition, so it is drawn apart from the colour scale
                ax.add_patch(plt.Rectangle((j - .5, i - .5), 1, 1, color="#2ca02c"))
                ax.text(j, i, "EXIT", ha="center", va="center", color="white", fontweight="bold")
            elif policy[(i, j)] in ARROWS:
                dx, dy = ARROWS[policy[(i, j)]]
                ax.arrow(j - dx / 2, i - dy / 2, dx, dy, head_width=0.18, color="white",
                         length_includes_head=True)
    ax.text(0, 0.38, "start", ha="center", va="center", color="white", fontsize=7)
    ax.set_xticks(range(cols))
    ax.set_xticklabels([f"{s:.1f}" for s in strengths])
    ax.set_xlabel("River strength per column (probability of being pushed down)")
    ax.set_yticks(range(rows))
    ax.set_title("Optimal value function and policy")
    fig.tight_layout()
    fig.savefig(path, dpi=130)
    plt.close(fig)


def main():
    FIGURES.mkdir(parents=True, exist_ok=True)

    # Example river used in the README
    random.seed(3)
    grid = create_river_grid(ROWS, COLS, nislas=2)
    strengths = river_strength_for_cols(ROWS, COLS)
    V, policy = value_iteration(grid, strengths)
    plot_value_policy(grid, strengths, V, policy, FIGURES / "river_value_policy.png")

    deltas = convergence(grid, strengths)
    fig, ax = plt.subplots(figsize=(6, 3.4))
    ax.semilogy(range(1, len(deltas) + 1), deltas, color="#1f77b4")
    ax.set_xlabel("Value Iteration sweep")
    ax.set_ylabel("max |ΔV| (log scale)")
    ax.set_title(f"Convergence: {len(deltas)} sweeps to reach 1e-6")
    ax.grid(alpha=0.3)
    fig.tight_layout()
    fig.savefig(FIGURES / "river_convergence.png", dpi=130)
    plt.close(fig)
    print(f"Example river (seed 3): converged in {len(deltas)} sweeps")

    # Monte Carlo over many random rivers: optimal vs naive policy
    rng = random.Random(0)
    stats = {"optimal": [], "naive": []}
    for seed in range(200):
        random.seed(1000 + seed)
        grid = create_river_grid(ROWS, COLS, nislas=2)
        strengths = river_strength_for_cols(ROWS, COLS)
        _, opt = value_iteration(grid, strengths)
        for name, pol in (("optimal", opt), ("naive", naive_policy(grid))):
            for _ in range(50):
                stats[name].append(simulate(grid, strengths, pol, rng))
    for name, runs in stats.items():
        reached = np.array([r for r, _ in runs])
        steps = np.array([t for r, t in runs if r])
        print(f"{name:8s}: reaches the exit in {reached.mean():.1%} of episodes, "
              f"mean {steps.mean():.1f} steps (median {np.median(steps):.0f}) when it does")


if __name__ == "__main__":
    main()
