"""
The palace environments.

Part 1 (`LogicPalace`): 3 pits, 1 sleeping soldier, the exit and Colonel Kurtz,
each in a different cell. Percepts: breeze (pit adjacent), snore (soldier
adjacent), glow (exit here or adjacent), four walls and a scream.

Part 2 (`BayesPalace`): three different traps (fire F, spikes P, darts D) that
may share a cell, each with its own stimulus; soldier M, exit S and Kurtz CK
never share a cell with a trap but may share one with each other.

Both environments expose the same game API (`move`, `throw`, `leave`), so the
same agent can play either of them. The agent only ever sees percepts.
"""

import random
from dataclasses import dataclass, field

from .grid import DIRECTIONS, neighbours, step, walls

START = (0, 0)


@dataclass
class Percept:
    """What the captain senses after an action."""

    stimuli: dict          # e.g. {"breeze": True, "snore": False, "glow": False}
    walls: tuple           # (up, down, left, right)
    scream: bool = False
    at_exit: bool = False  # the captain recognises the exit door when standing on it
    found_kurtz: bool = False

    def as_list(self):
        """Boolean list in the order used by the assignment."""
        return [*self.stimuli.values(), *self.walls, self.scream]


@dataclass
class Game:
    """Shared game state and rules. Subclasses define the hidden world."""

    n: int = 6
    pos: tuple = START
    alive: bool = True
    escaped: bool = False
    has_kurtz: bool = False
    grenades: int = 1
    soldier_alive: bool = True
    actions: int = 0
    log: list = field(default_factory=list)

    # --- to be defined by each environment ---
    def deadly(self, cell):  # pragma: no cover - abstract
        raise NotImplementedError

    def stimuli(self, cell):  # pragma: no cover - abstract
        raise NotImplementedError

    def soldier_at(self, cell):  # pragma: no cover - abstract
        raise NotImplementedError

    def kurtz_at(self, cell):  # pragma: no cover - abstract
        raise NotImplementedError

    def exit_at(self, cell):  # pragma: no cover - abstract
        raise NotImplementedError

    # --- actions ---
    def percept(self, scream=False):
        """Percept at the current position."""
        return Percept(
            stimuli=self.stimuli(self.pos),
            walls=walls(self.pos, self.n),
            scream=scream,
            at_exit=self.exit_at(self.pos),
            found_kurtz=self.kurtz_at(self.pos),
        )

    def move(self, direction):
        """Move one cell. Walking into a wall leaves the captain where he is."""
        self.actions += 1
        target = step(self.pos, direction)
        self.log.append(("move", direction))
        if not (0 <= target[0] < self.n and 0 <= target[1] < self.n):
            return self.percept()
        self.pos = target
        if self.deadly(target):
            self.alive = False
            return self.percept()
        if self.kurtz_at(target):
            self.has_kurtz = True
        return self.percept()

    def throw(self, direction):
        """Throw the only grenade one cell away. A hit makes the soldier scream."""
        if self.grenades == 0:
            raise RuntimeError("No grenades left")
        self.actions += 1
        self.grenades -= 1
        target = step(self.pos, direction)
        self.log.append(("throw", direction))
        hit = (
            self.soldier_alive
            and 0 <= target[0] < self.n
            and 0 <= target[1] < self.n
            and self.soldier_at(target)
        )
        if hit:
            self.soldier_alive = False
        return self.percept(scream=hit)

    def leave(self):
        """Leave the palace. Only works on the exit cell; the mission needs Kurtz."""
        self.actions += 1
        self.log.append(("leave", None))
        if self.exit_at(self.pos):
            self.escaped = True
        return self.percept()

    @property
    def mission_complete(self):
        return self.escaped and self.has_kurtz


def _random_cell(n, rng, forbidden):
    while True:
        cell = (rng.randrange(n), rng.randrange(n))
        if cell not in forbidden:
            return cell


@dataclass
class LogicPalace(Game):
    """Part 1 palace: every element in a different cell."""

    pits: frozenset = frozenset()
    soldier: tuple = None
    kurtz: tuple = None
    exit: tuple = None

    @classmethod
    def random(cls, n=6, n_pits=3, seed=None):
        rng = random.Random(seed)
        used = {START}
        pits = []
        for _ in range(n_pits):
            cell = _random_cell(n, rng, used)
            pits.append(cell)
            used.add(cell)
        soldier = _random_cell(n, rng, used)
        used.add(soldier)
        kurtz = _random_cell(n, rng, used)
        used.add(kurtz)
        exit_ = _random_cell(n, rng, used)
        return cls(n=n, pits=frozenset(pits), soldier=soldier, kurtz=kurtz, exit=exit_)

    def deadly(self, cell):
        return cell in self.pits or (self.soldier_alive and cell == self.soldier)

    def soldier_at(self, cell):
        return cell == self.soldier

    def kurtz_at(self, cell):
        return cell == self.kurtz

    def exit_at(self, cell):
        return cell == self.exit

    def stimuli(self, cell):
        around = set(neighbours(cell, self.n))
        return {
            "breeze": bool(around & self.pits),
            "snore": self.soldier_alive and self.soldier in around,
            "glow": self.exit in around or self.exit == cell,
        }

    def symbol(self, cell):
        """Ground-truth symbol of a cell (for displays after the game)."""
        if cell in self.pits:
            return "P"
        if cell == self.soldier:
            return "E" if self.soldier_alive else "x"
        if cell == self.kurtz:
            return "K"
        if cell == self.exit:
            return "S"
        return "·"


TRAPS = ("F", "P", "D")


@dataclass
class BayesPalace(Game):
    """Part 2 palace: typed traps that may overlap; M, S and CK off the traps."""

    traps: dict = None    # {"F": cell, "P": cell, "D": cell}
    soldier: tuple = None
    kurtz: tuple = None
    exit: tuple = None

    @classmethod
    def random(cls, n=6, seed=None):
        rng = random.Random(seed)
        traps = {t: _random_cell(n, rng, {START}) for t in TRAPS}
        off_limits = {START} | set(traps.values())
        soldier = _random_cell(n, rng, off_limits)
        exit_ = _random_cell(n, rng, off_limits)
        kurtz = _random_cell(n, rng, off_limits)
        return cls(n=n, traps=traps, soldier=soldier, kurtz=kurtz, exit=exit_)

    def deadly(self, cell):
        return cell in self.traps.values() or (self.soldier_alive and cell == self.soldier)

    def soldier_at(self, cell):
        return cell == self.soldier

    def kurtz_at(self, cell):
        return cell == self.kurtz

    def exit_at(self, cell):
        return cell == self.exit

    def stimuli(self, cell):
        zone = set(neighbours(cell, self.n)) | {cell}
        result = {f"e{t}": self.traps[t] in zone for t in TRAPS}
        result["eM"] = self.soldier_alive and self.soldier in zone
        result["eS"] = self.exit in zone
        return result


def solvable(game):
    """
    Upper bound used in the evaluation: can an omniscient captain complete the
    mission? He must reach Kurtz and then the exit without entering a deadly
    cell; the soldier's cell counts as passable because the grenade can always
    be thrown from the previous cell. Unless the soldier shares the cell with
    Kurtz or the exit (possible only in Part 2) this is exact.
    """
    from .grid import bfs_path

    n = game.n
    blocked = {c for c in ((r, k) for r in range(n) for k in range(n))
               if game.deadly(c) and not game.soldier_at(c)}
    allowed = {(r, k) for r in range(n) for k in range(n)} - blocked
    to_kurtz = bfs_path(START, game.kurtz, allowed)
    to_exit = bfs_path(game.kurtz, game.exit, allowed)
    return to_kurtz is not None and to_exit is not None


__all__ = ["DIRECTIONS", "START", "Percept", "Game", "LogicPalace", "BayesPalace", "solvable"]
