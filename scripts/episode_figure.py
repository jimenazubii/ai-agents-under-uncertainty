"""
Figure: how the logical agent's knowledge evolves during one game.

    python scripts/episode_figure.py [--seed 4]

Each panel shows the exact probability of death in every cell (from model
checking) at one moment of the game, with the captain's path so far.
"""

import argparse
import sys
from pathlib import Path

import matplotlib.pyplot as plt
from matplotlib.colors import LinearSegmentedColormap

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from palace_ai.agent import Agent  # noqa: E402
from palace_ai.knowledge import LogicKB  # noqa: E402
from palace_ai.palace import LogicPalace  # noqa: E402

CMAP = LinearSegmentedColormap.from_list("risk", ["#f7f7f7", "#fdae61", "#d7191c"])


def snapshot(game, kb, label):
    return {
        "label": label, "pos": game.pos, "p_death": kb.p_death().copy(),
        "visited": set(kb.visited), "safe": kb.safe_cells(), "models": kb.n_models,
        "kurtz": game.has_kurtz, "soldier_alive": kb.soldier_alive,
        "kurtz_cell": kb.kurtz_cell, "exit_cell": kb.exit_cell,
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--seed", type=int, default=4)
    args = parser.parse_args()

    game, kb = LogicPalace.random(seed=args.seed), LogicKB()
    frames, path = [], [game.pos]

    def record(g, k, action):
        path.append(g.pos)
        frames.append(snapshot(g, k, action))

    kb.tell(game.pos, game.percept())
    start = snapshot(game, kb, "start")
    result = Agent(kb, on_step=record).run(game)

    # Pick informative moments: start, first located hazard, Kurtz found, end
    chosen = [("Start: snore at the entrance", start, 0)]
    for i, f in enumerate(frames):
        if f["label"][0] == "throw":
            chosen.append(("Risk-free grenade hits the soldier", f, i + 1))
            break
    for i, f in enumerate(frames):
        if f["kurtz"]:
            chosen.append(("Kurtz found", f, i + 1))
            break
    chosen.append((f"Mission complete ({result.actions} actions)", frames[-1], len(frames)))

    fig, axes = plt.subplots(1, len(chosen), figsize=(4.1 * len(chosen), 4.4))
    n = game.n
    for ax, (title, f, idx) in zip(axes, chosen):
        ax.imshow(f["p_death"], cmap=CMAP, vmin=0, vmax=1)
        for r in range(n):
            for k in range(n):
                cell = (r, k)
                p = f["p_death"][r, k]
                if cell == f["kurtz_cell"]:
                    text, color = "KURTZ", "#7b3294"
                elif cell == f["exit_cell"]:
                    text, color = "EXIT", "#1a9850"
                elif cell in f["visited"]:
                    text, color = "·", "#555555"
                elif p == 1:
                    text, color = "PIT", "white"
                elif cell in f["safe"]:
                    text, color = "safe", "#1a9850"
                else:
                    text, color = f"{100 * p:.0f}%", "#333333"
                bold = text in ("safe", "PIT", "KURTZ", "EXIT")
                ax.text(k, r, text, ha="center", va="center", fontsize=8, color=color,
                        fontweight="bold" if bold else "normal")
        ax.scatter([f["pos"][1]], [f["pos"][0]], s=260, facecolor="none", zorder=3,
                   edgecolor="#2b83ba", linewidth=2.5)
        ax.set_title(f"{title}\n{f['models']:,} consistent worlds", fontsize=10)
        ax.set_xticks([])
        ax.set_yticks([])
    fig.suptitle("Probability of death in each cell, as deduced by the agent  (grey: visited · blue circle: captain)",
                 fontsize=11)
    fig.tight_layout(rect=(0, 0, 1, 0.92))
    out = ROOT / "docs" / "figures" / "agent_reasoning.png"
    fig.savefig(out, dpi=130)
    print(f"Saved {out.relative_to(ROOT)} — outcome: {result.outcome}")


if __name__ == "__main__":
    main()
