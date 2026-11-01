"""
Part 2 · Bayesian captain in the palace with typed traps.

    python palacio.py                # play with Bayesian risk estimates
    python palacio.py --plots        # also show the belief heatmaps
    python palacio.py --auto --risk 0.5 --seed 3
"""

from palace_ai.bayes import BayesBeliefs
from palace_ai.cli import main
from palace_ai.palace import BayesPalace


def plot_beliefs(kb, position):
    """Heatmaps of P(trap), P(soldier) and P(exit), as in the course version."""
    import matplotlib.pyplot as plt

    fig, axes = plt.subplots(1, 3, figsize=(11, 3.6))
    maps = [(kb.p_trap(), "P(trap)"), (kb.p_soldier(), "P(soldier M)"), (kb.p_exit(), "P(exit S)")]
    for ax, (values, title) in zip(axes, maps):
        im = ax.imshow(values, vmin=0, vmax=max(values.max(), 1e-9), cmap="magma")
        ax.scatter([position[1]], [position[0]], marker="x", color="cyan", s=80)
        ax.set_title(title)
        ax.set_xticks(range(kb.n))
        ax.set_yticks(range(kb.n))
        fig.colorbar(im, ax=ax, fraction=0.046)
    plt.tight_layout()
    plt.show()


if __name__ == "__main__":
    main(BayesPalace, BayesBeliefs, "Part 2: Bayesian agent in the palace", plots=plot_beliefs)
