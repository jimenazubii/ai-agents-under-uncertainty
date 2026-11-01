"""Console interface shared by kurtz.py (Part 1) and palacio.py (Part 2)."""

import argparse
import time

from .agent import Agent
from .grid import DIRECTIONS, neighbours, step

KEYS = {"w": "U", "s": "D", "a": "L", "d": "R"}


def render(game, kb, reveal=False):
    """Draw what the captain knows. With `reveal`, show the true palace too."""
    n = game.n
    safe = kb.safe_cells()
    p_death = kb.p_death()
    soldier = kb.known_soldier() if kb.soldier_alive else None
    pits = {c for c in safe_cells_complement(n, safe) if kb.p_trap()[c] > 1 - 1e-12}
    lines = ["    " + " ".join(f"{k:^4}" for k in range(n))]
    for r in range(n):
        row = []
        for k in range(n):
            cell = (r, k)
            if cell == game.pos:
                sym = "CW+K" if game.has_kurtz else "CW"
            elif reveal:
                sym = truth_symbol(game, cell)
            elif cell == kb.exit_cell:
                sym = "EXIT"
            elif cell == kb.kurtz_cell:
                sym = "K"
            elif cell in kb.visited:
                sym = "·"
            elif cell == soldier:
                sym = "M!"
            elif cell in pits:
                sym = "X!"
            elif cell in safe:
                sym = "ok"
            elif p_death[cell] > 0:
                sym = f"{round(100 * p_death[cell]):d}%"
            else:
                sym = "?"
            row.append(f"{sym:^4}")
        lines.append(f"{r:>3} " + " ".join(row))
    return "\n".join(lines)


def safe_cells_complement(n, safe):
    return {(r, k) for r in range(n) for k in range(n)} - safe


def truth_symbol(game, cell):
    if hasattr(game, "pits"):
        if cell in game.pits:
            return "P"
    else:
        traps = "".join(t for t, c in game.traps.items() if c == cell)
        if traps:
            return traps
    parts = []
    if cell == game.soldier:
        parts.append("M" if game.soldier_alive else "m")
    if cell == game.kurtz:
        parts.append("K")
    if cell == game.exit:
        parts.append("S")
    return "".join(parts) or "·"


def describe(percept):
    sensed = [name for name, value in percept.stimuli.items() if value]
    if percept.scream:
        sensed.append("SCREAM")
    if percept.at_exit:
        sensed.append("standing on the exit")
    return ", ".join(sensed) if sensed else "nothing"


def status(game, kb):
    risks = []
    for nb in neighbours(game.pos, game.n):
        d = next(k for k, v in DIRECTIONS.items() if step(game.pos, k) == nb)
        risks.append(f"{d}: {100 * kb.p_death()[nb]:.0f}%")
    return (f"Kurtz on board: {'yes' if game.has_kurtz else 'no'} | grenades: {game.grenades} | "
            f"risk of moving -> {', '.join(risks)}")


def interactive(game, kb, plots=None):
    print("Moves: w/a/s/d · grenade: g + direction (e.g. gd) · leave: x · hint: h · quit: q")
    print("Map: CW you · ok deduced safe · X! pit/trap · M! soldier · % risk of death · ? unknown\n")
    percept = game.percept()
    kb.tell(game.pos, percept)
    helper = Agent(kb, risk_threshold=0.5)
    while game.alive and not game.escaped:
        print(render(game, kb))
        print(f"You sense: {describe(percept)}")
        print(status(game, kb))
        if plots:
            plots(kb, game.pos)
        cmd = input("> ").strip().lower()
        if cmd == "q":
            break
        if cmd == "h":
            print("Hint:", helper.decide(game))
            continue
        if cmd == "x":
            percept = game.leave()
            if not game.escaped:
                print("This is not the exit.")
            continue
        if cmd in KEYS:
            percept = game.move(KEYS[cmd])
            if game.alive:
                kb.tell(game.pos, percept)
            continue
        if len(cmd) == 2 and cmd[0] == "g" and cmd[1] in KEYS and game.grenades:
            direction = KEYS[cmd[1]]
            percept = game.throw(direction)
            kb.tell_grenade(step(game.pos, direction), percept.scream)
            continue
        print("Unknown command.")
    finish(game, kb)


def automatic(game, kb, risk, delay):
    def show(g, k, action):
        print(f"\nAction: {action}")
        print(render(g, k))
        if delay:
            time.sleep(delay)

    result = Agent(kb, risk_threshold=risk, on_step=show).run(game)
    print(f"\nOutcome: {result.outcome} after {result.actions} actions "
          f"(risky moves: {result.risky_moves}, grenade used: {result.grenade_used})")
    finish(game, kb)


def finish(game, kb):
    if game.mission_complete:
        print("\nMission complete: Willard and Kurtz have left the palace.")
    elif not game.alive:
        print("\nCaptain Willard has died.")
    print("\nTrue palace:")
    print(render(game, kb, reveal=True))


def main(env_cls, kb_cls, description, plots=None):
    parser = argparse.ArgumentParser(description=description)
    parser.add_argument("--auto", action="store_true", help="let the autonomous agent play")
    parser.add_argument("--seed", type=int, default=None, help="random seed for the palace")
    parser.add_argument("--risk", type=float, default=0.0,
                        help="max probability of death the agent accepts when stuck (default 0)")
    parser.add_argument("--delay", type=float, default=0.0, help="seconds between steps in --auto")
    parser.add_argument("--plots", action="store_true", help="show belief heatmaps (Part 2)")
    args = parser.parse_args()

    game = env_cls.random(seed=args.seed)
    kb = kb_cls()
    if args.auto:
        automatic(game, kb, args.risk, args.delay)
    else:
        interactive(game, kb, plots if args.plots else None)
