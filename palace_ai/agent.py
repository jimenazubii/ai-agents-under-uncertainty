"""
Autonomous captain: a knowledge-based agent that plans with search.

The agent only uses its percepts, through a knowledge base (`LogicKB` for
Part 1 or `BayesBeliefs` for Part 2). At every step it asks the knowledge base
which cells are safe and replans with breadth-first search over safe cells:

1. With Kurtz on board and the exit located: go to the exit and leave.
2. Otherwise explore: go to the closest safe, unvisited cell. Once Kurtz is
   found, cells more likely to be the exit (according to the glow) come first.
3. No safe cell left to explore, but the soldier's cell is *entailed*: walk to
   a safe cell next to him and throw the grenade (a guaranteed hit). If his cell
   is unknown but a neighbouring cell could only be deadly because of him, the
   grenade is thrown there instead: it either kills him or proves the cell
   safe, so it is a risk-free way to gain information.
4. Still stuck: take a calculated risk. Enter the unexplored cell with the
   lowest probability of death, if it is below `risk_threshold`. If the only
   danger in that cell is the soldier, throw the grenade into it first.
5. Otherwise give up. With `risk_threshold=0` the captain never takes a risk.
"""

from dataclasses import dataclass

import numpy as np

from .grid import bfs_distances, bfs_path, direction_to, neighbours


@dataclass
class EpisodeResult:
    outcome: str            # "escaped" | "dead" | "stuck" | "timeout"
    actions: int
    found_kurtz: bool
    grenade_used: bool
    soldier_killed: bool
    risky_moves: int

    @property
    def success(self):
        return self.outcome == "escaped"


class Agent:
    def __init__(self, kb, risk_threshold=0.0, max_actions=300, on_step=None):
        self.kb = kb
        self.risk_threshold = risk_threshold
        self.max_actions = max_actions
        self.on_step = on_step          # optional callback(game, kb, action) for displays
        self.risky_moves = 0

    # ------------------------------------------------------------ decision
    def decide(self, game):
        """Return the next action as ("move" | "throw", direction), ("leave", None) or ("stop", reason)."""
        kb, pos = self.kb, game.pos
        safe = kb.safe_cells() | kb.visited
        dist = bfs_distances(pos, safe)

        # 1. Mission almost done: Kurtz on board and the exit is known.
        if game.has_kurtz and kb.exit_cell is not None:
            if pos == kb.exit_cell:
                return ("leave", None)
            path = bfs_path(pos, kb.exit_cell, safe)
            if path:
                return ("move", direction_to(pos, path[0]))

        # 2. Explore the closest safe, unvisited cell.
        frontier = [c for c in safe - kb.visited if c in dist]
        if frontier:
            if game.has_kurtz:
                p_exit = kb.p_exit()
                key = lambda c: (dist[c] - kb.n * kb.n * p_exit[c], c)
            else:
                key = lambda c: (dist[c], c)
            return self._go_towards(pos, min(frontier, key=key), safe)

        # 3. The soldier's position is entailed: eliminate him.
        soldier = kb.known_soldier()
        if soldier is not None and kb.soldier_alive and game.grenades:
            action = self._attack(pos, soldier, safe, dist)
            if action:
                return action

        # 3b. Risk-free grenade: a border cell whose only possible danger is the
        #     soldier. Either the grenade kills him or it proves the cell safe.
        if kb.soldier_alive and game.grenades:
            p_trap, p_soldier = kb.p_trap(), kb.p_soldier()
            targets = [c for c in self._unexplored_border(safe, dist)
                       if p_trap[c] < 1e-12 and p_soldier[c] > 0]
            if targets:
                target = max(targets, key=lambda c: (p_soldier[c], -dist[self._closest_entry(c, safe, dist)]))
                action = self._attack(pos, target, safe, dist)
                if action:
                    return action

        # 4. Calculated risk.
        if self.risk_threshold > 0:
            p_death = kb.p_death()
            options = []
            for cell in self._unexplored_border(safe, dist):
                p = p_death[cell]
                if p <= self.risk_threshold and p < 1:
                    options.append((p, dist[self._closest_entry(cell, safe, dist)], cell))
            if options:
                p, _, cell = min(options)
                only_soldier = kb.p_trap()[cell] < 1e-12 and kb.soldier_alive
                if only_soldier and game.grenades and kb.p_soldier()[cell] > 0:
                    action = self._attack(pos, cell, safe, dist)
                    if action:
                        return action
                entry = self._closest_entry(cell, safe, dist)
                if pos != entry:
                    return self._go_towards(pos, entry, safe)
                self.risky_moves += 1
                return ("move", direction_to(pos, cell))

        return ("stop", "no safe move")

    def _go_towards(self, pos, target, safe):
        path = bfs_path(pos, target, safe | {target})
        return ("move", direction_to(pos, path[0]))

    def _closest_entry(self, cell, safe, dist):
        """Reachable safe neighbour of `cell` that is closest to the captain."""
        entries = [c for c in neighbours(cell, self.kb.n) if c in safe and c in dist]
        return min(entries, key=lambda c: (dist[c], c))

    def _unexplored_border(self, safe, dist):
        n = self.kb.n
        border = set()
        for cell in dist:
            for nb in neighbours(cell, n):
                if nb not in safe:
                    border.add(nb)
        return border

    def _attack(self, pos, target, safe, dist):
        """Move next to `target` and throw the grenade at it."""
        spots = [c for c in neighbours(target, self.kb.n) if c in safe and c in dist]
        if not spots:
            return None
        if pos in spots:
            return ("throw", direction_to(pos, target))
        return self._go_towards(pos, min(spots, key=lambda c: (dist[c], c)), safe)

    # --------------------------------------------------------------- loop
    def run(self, game):
        kb = self.kb
        kb.tell(game.pos, game.percept())
        outcome = "timeout"
        while game.actions < self.max_actions:
            if game.escaped:
                outcome = "escaped" if game.has_kurtz else "stuck"
                break
            if not game.alive:
                outcome = "dead"
                break
            kind, direction = self.decide(game)
            if kind == "stop":
                outcome = "stuck"
                break
            if kind == "move":
                percept = game.move(direction)
                if game.alive:
                    kb.tell(game.pos, percept)
            elif kind == "throw":
                target = (game.pos[0] + {"U": -1, "D": 1}.get(direction, 0),
                          game.pos[1] + {"L": -1, "R": 1}.get(direction, 0))
                percept = game.throw(direction)
                kb.tell_grenade(target, percept.scream)
            elif kind == "leave":
                game.leave()
            if self.on_step:
                self.on_step(game, kb, (kind, direction))
        return EpisodeResult(
            outcome=outcome,
            actions=game.actions,
            found_kurtz=game.has_kurtz,
            grenade_used=game.grenades == 0,
            soldier_killed=not game.soldier_alive,
            risky_moves=self.risky_moves,
        )


def oracle_success_rate(games):
    """Share of palaces an omniscient captain could solve (upper bound)."""
    from .palace import solvable

    return float(np.mean([solvable(g) for g in games]))
