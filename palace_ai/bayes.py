"""
Part 2 beliefs: Bayesian filtering over the position of each element.

For every element tau in {F, P, D (traps), M (soldier), S (exit)} the captain
keeps a probability map over the 6 x 6 cells, starting from a uniform prior
1 / (N - 1) (every cell except the entrance). The likelihood of a stimulus is
deterministic, as in the assignment:

    P(e_tau at c | tau at k) = 1 if k is c or adjacent to c, else 0

so Bayes' rule reduces to zeroing the cells that are incompatible with the
observation and renormalising. On top of the original course version this
module also uses the *survival* evidence: if the captain is alive in a cell,
no trap (and no living soldier) can be there.

Each element is tracked independently, so the probability of dying in a cell
is approximated as 1 - prod_tau (1 - P(tau at c)), which treats the elements
as independent (they are, except that M, S and CK avoid the traps).
"""

import numpy as np

from .grid import neighbours

START = (0, 0)
TRAPS = ("F", "P", "D")
ELEMENTS = (*TRAPS, "M", "S")


class BayesBeliefs:
    """Per-element posterior maps for the Part 2 palace."""

    def __init__(self, n=6):
        self.n = n
        prior = np.full((n, n), 1.0 / (n * n - 1))
        prior[START] = 0.0
        self.beliefs = {e: prior.copy() for e in ELEMENTS}
        self.soldier_alive = True
        self.visited = set()
        self.exit_cell = None
        self.kurtz_cell = None

    def _zone(self, cell):
        zone = np.zeros((self.n, self.n), dtype=bool)
        for r, k in neighbours(cell, self.n) + [cell]:
            zone[r, k] = True
        return zone

    def _update(self, element, compatible):
        """Bayes' rule with a 0/1 likelihood: keep compatible cells and renormalise."""
        b = self.beliefs[element] * compatible
        total = b.sum()
        if total == 0:
            raise RuntimeError(f"Contradictory evidence for {element}")
        self.beliefs[element] = b / total

    def tell(self, cell, percept):
        """Update every map with the stimuli perceived (and survived) at `cell`."""
        self.visited.add(cell)
        zone = self._zone(cell)
        here = np.zeros_like(zone)
        here[cell] = True

        for t in TRAPS:
            seen = percept.stimuli[f"e{t}"]
            self._update(t, (zone if seen else ~zone) & ~here)   # survived: no trap here
        if self.soldier_alive:
            seen = percept.stimuli["eM"]
            self._update("M", (zone if seen else ~zone) & ~here)
        if percept.at_exit:
            self.exit_cell = cell
            self._update("S", here)
        else:
            seen = percept.stimuli["eS"]
            self._update("S", (zone if seen else ~zone) & ~here)
        if percept.found_kurtz:
            self.kurtz_cell = cell

    def tell_grenade(self, target, scream):
        if not self.soldier_alive:
            return
        hit = np.zeros((self.n, self.n), dtype=bool)
        hit[target] = True
        self._update("M", hit if scream else ~hit)
        if scream:
            self.soldier_alive = False

    # ------------------------------------------------------------------ ask
    def p_trap(self):
        """P(at least one trap in the cell), assuming independent traps."""
        survive = np.ones((self.n, self.n))
        for t in TRAPS:
            survive *= 1 - self.beliefs[t]
        return 1 - survive

    def p_soldier(self):
        return self.beliefs["M"]

    def p_death(self):
        p_m = self.beliefs["M"] if self.soldier_alive else 0.0
        return 1 - (1 - self.p_trap()) * (1 - p_m)

    def safe_cells(self):
        d = self.p_death()
        return {(r, k) for r in range(self.n) for k in range(self.n) if d[r, k] < 1e-12}

    def known_soldier(self):
        hits = np.argwhere(self.beliefs["M"] > 1 - 1e-12)
        return tuple(hits[0]) if len(hits) else None

    def p_exit(self):
        return self.beliefs["S"]
