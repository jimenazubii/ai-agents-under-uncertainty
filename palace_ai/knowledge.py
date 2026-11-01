"""
Part 1 knowledge base: propositional inference by model checking.

A "model" (possible world) is a placement of the 3 pits and the soldier. In a
6 x 6 palace there are C(35, 3) * 32 = 209,440 of them. The knowledge base
keeps every model that is consistent with everything the captain has
perceived so far and discards the rest after each percept:

    breeze at c  <=>  some pit is adjacent to c
    snore at c   <=>  the (living) soldier is adjacent to c
    survived c   =>   no pit at c and no living soldier at c
    scream       <=>  the grenade hit the soldier's cell

A sentence is entailed (KB |= alpha) when it holds in every remaining model.
This gives exact logical deductions: a cell is *safe* when no remaining model
puts a pit or a living soldier there, and a pit or the soldier is *located*
when every remaining model agrees on it.

Because the elements are placed uniformly at random, every consistent model
is equally likely. The fraction of models with a pit in a cell is therefore
the exact posterior probability P(pit | percepts): the same machinery gives
both the logical and the Bayesian answer.

The exit and Kurtz do not affect safety. They are tracked separately: the
glow restricts where the exit can be, and Kurtz is found by walking into his
cell. Ignoring their "different cell" constraint only makes the reasoning
slightly less informative, never wrong.
"""

from itertools import combinations

import numpy as np

from .grid import neighbours

START = (0, 0)


class LogicKB:
    """Knowledge base for the Part 1 palace (3 pits + 1 soldier)."""

    def __init__(self, n=6, n_pits=3):
        self.n = n
        cells = n * n
        start = START[0] * n + START[1]
        candidates = [c for c in range(cells) if c != start]

        bit = np.uint64(1) << np.arange(cells, dtype=np.uint64)
        adj = np.zeros(cells, dtype=np.uint64)
        for c in range(cells):
            for r, k in neighbours(divmod(c, n), n):
                adj[c] |= bit[r * n + k]
        self._bit, self._adj = bit, adj

        # Enumerate every model: (set of pits, soldier cell), all distinct.
        pit_sets = np.array(list(combinations(candidates, n_pits)), dtype=np.int64)
        pit_masks = np.bitwise_or.reduce(bit[pit_sets], axis=1)
        soldier = np.array(candidates, dtype=np.int64)
        pit_mask = np.repeat(pit_masks, len(soldier))
        soldier = np.tile(soldier, len(pit_masks))
        keep = (pit_mask & bit[soldier]) == 0         # soldier not on a pit
        self.pit_mask = pit_mask[keep]
        self.soldier = soldier[keep]

        self.soldier_alive = True
        self.visited = set()
        self.exit_possible = np.ones((n, n), dtype=bool)
        self.exit_possible[START] = False
        self.exit_cell = None
        self.kurtz_cell = None
        self._cache = None

    # ------------------------------------------------------------------ tell
    def _filter(self, keep):
        if not keep.all():
            self.pit_mask = self.pit_mask[keep]
            self.soldier = self.soldier[keep]
        if len(self.pit_mask) == 0:
            raise RuntimeError("Contradictory percepts: no model is consistent")
        self._cache = None

    def tell(self, cell, percept):
        """Add what the captain perceives (and survives) at `cell`."""
        c = cell[0] * self.n + cell[1]
        self.visited.add(cell)

        keep = (self.pit_mask & self._bit[c]) == 0                     # no pit here
        breeze = (self.pit_mask & self._adj[c]) != 0
        keep &= breeze == percept.stimuli["breeze"]
        if self.soldier_alive:
            keep &= self.soldier != c                                  # soldier not here
            snore = (self._bit[self.soldier] & self._adj[c]) != 0
            keep &= snore == percept.stimuli["snore"]
        self._filter(keep)

        # Exit: glow <=> exit in this cell or next to it.
        zone = np.zeros((self.n, self.n), dtype=bool)
        for r, k in neighbours(cell, self.n) + [cell]:
            zone[r, k] = True
        self.exit_possible &= zone if percept.stimuli["glow"] else ~zone
        if percept.at_exit:
            self.exit_cell = cell
            self.exit_possible[:] = False
            self.exit_possible[cell] = True
        else:
            self.exit_possible[cell] = False
        if percept.found_kurtz:
            self.kurtz_cell = cell

    def tell_grenade(self, target, scream):
        """The grenade was thrown at `target`: a scream means the soldier was there."""
        if not self.soldier_alive:
            return
        t = target[0] * self.n + target[1]
        self._filter(self.soldier == t if scream else self.soldier != t)
        if scream:
            self.soldier_alive = False

    # ----------------------------------------------------------------- ask
    def _marginals(self):
        if self._cache is None:
            n = self.n
            cells = n * n
            total = len(self.pit_mask)
            p_pit = np.array([
                np.count_nonzero(self.pit_mask & self._bit[c]) for c in range(cells)
            ]) / total
            p_soldier = np.bincount(self.soldier, minlength=cells) / total
            if not self.soldier_alive:
                p_soldier_alive = np.zeros(cells)
            else:
                p_soldier_alive = p_soldier
            # Pits and the soldier never share a cell, so the events are disjoint.
            p_death = p_pit + p_soldier_alive
            self._cache = {
                "pit": p_pit.reshape(n, n),
                "soldier": p_soldier.reshape(n, n),
                "death": p_death.reshape(n, n),
            }
        return self._cache

    @property
    def n_models(self):
        return len(self.pit_mask)

    def p_pit(self):
        return self._marginals()["pit"]

    def p_trap(self):
        """Probability of a static hazard (here: a pit) in each cell."""
        return self.p_pit()

    def p_soldier(self):
        """P(soldier in cell), whether or not he is still alive."""
        return self._marginals()["soldier"]

    def p_death(self):
        """Exact probability that entering each cell kills the captain."""
        return self._marginals()["death"]

    def safe_cells(self):
        """Cells entailed to be safe: no consistent model makes them deadly."""
        d = self.p_death()
        return {(r, k) for r in range(self.n) for k in range(self.n) if d[r, k] == 0}

    def known_pits(self):
        p = self.p_pit()
        return {(r, k) for r in range(self.n) for k in range(self.n) if p[r, k] == 1}

    def known_soldier(self):
        """The soldier's cell if it is entailed, else None."""
        p = self.p_soldier()
        hits = np.argwhere(p == 1)
        return tuple(hits[0]) if len(hits) else None

    def p_exit(self):
        """Belief over the exit position (uniform over the cells still possible)."""
        mask = self.exit_possible & (self.p_death() < 1)
        if self.exit_cell is not None:
            mask = np.zeros_like(mask)
            mask[self.exit_cell] = True
        return mask / mask.sum() if mask.any() else mask.astype(float)
