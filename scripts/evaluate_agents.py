"""
Evaluate the autonomous captain on random palaces.

    python scripts/evaluate_agents.py [--palaces 1000]

For each part (logical / Bayesian) and each risk threshold, the agent plays the
same set of random palaces (seeds 0..N-1). Results are compared with an
omniscient captain who knows the whole map (upper bound). Writes
docs/results.csv and docs/figures/agent_evaluation.png.
"""

import argparse
import csv
import sys
import time
from collections import Counter
from pathlib import Path

import matplotlib.pyplot as plt

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from palace_ai.agent import Agent  # noqa: E402
from palace_ai.bayes import BayesBeliefs  # noqa: E402
from palace_ai.knowledge import LogicKB  # noqa: E402
from palace_ai.palace import BayesPalace, LogicPalace, solvable  # noqa: E402

PARTS = {
    "Part 1 · logical agent": (LogicPalace, LogicKB),
    "Part 2 · Bayesian agent": (BayesPalace, BayesBeliefs),
}
THRESHOLDS = [0.0, 0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7]


def evaluate(env_cls, kb_cls, threshold, n):
    counts, actions = Counter(), []
    for seed in range(n):
        result = Agent(kb_cls(), risk_threshold=threshold).run(env_cls.random(seed=seed))
        counts[result.outcome] += 1
        if result.success:
            actions.append(result.actions)
    return counts, sum(actions) / max(len(actions), 1)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--palaces", type=int, default=1000)
    args = parser.parse_args()
    n = args.palaces

    rows = []
    for part, (env_cls, kb_cls) in PARTS.items():
        oracle = sum(solvable(env_cls.random(seed=s)) for s in range(n)) / n
        print(f"\n{part} — solvable by an omniscient captain: {oracle:.1%}")
        for th in THRESHOLDS:
            t = time.time()
            counts, mean_actions = evaluate(env_cls, kb_cls, th, n)
            row = {
                "part": part, "risk_threshold": th, "palaces": n, "oracle_success": oracle,
                "success": counts["escaped"] / n, "death": counts["dead"] / n,
                "stuck": (counts["stuck"] + counts["timeout"]) / n,
                "mean_actions_when_success": round(mean_actions, 1),
            }
            rows.append(row)
            print(f"  risk ≤ {th:.1f}: success {row['success']:.1%} · death {row['death']:.1%} · "
                  f"gives up {row['stuck']:.1%} · {mean_actions:.1f} actions  ({time.time() - t:.0f}s)")

    with open(ROOT / "docs" / "results.csv", "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=rows[0].keys())
        writer.writeheader()
        writer.writerows(rows)

    fig, axes = plt.subplots(1, 2, figsize=(11, 4), sharey=True)
    for ax, part in zip(axes, PARTS):
        data = [r for r in rows if r["part"] == part]
        x = [r["risk_threshold"] for r in data]
        ax.stackplot(x, [100 * r["success"] for r in data], [100 * r["stuck"] for r in data],
                     [100 * r["death"] for r in data], labels=["Mission complete", "Gives up", "Dies"],
                     colors=["#2ca02c", "#bbbbbb", "#d62728"], alpha=0.85)
        ax.axhline(100 * data[0]["oracle_success"], color="black", ls="--", lw=1,
                   label="Omniscient captain")
        ax.set_title(part)
        ax.set_xlabel("Maximum probability of death accepted when stuck")
        ax.set_xlim(0, max(THRESHOLDS))
        ax.set_ylim(0, 100)
        ax.grid(alpha=0.3)
    axes[0].set_ylabel(f"% of {n} random palaces")
    axes[1].legend(loc="lower left", fontsize=8)
    fig.tight_layout()
    fig.savefig(ROOT / "docs" / "figures" / "agent_evaluation.png", dpi=130)
    print("\nSaved docs/results.csv and docs/figures/agent_evaluation.png")


if __name__ == "__main__":
    main()
