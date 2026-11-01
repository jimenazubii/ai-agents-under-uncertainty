"""
Part 1 · Finding Colonel Kurtz with a logical agent.

    python kurtz.py                  # play: you guide Willard, the KB deduces what is safe
    python kurtz.py --auto           # the autonomous agent plays (BFS over deduced-safe cells)
    python kurtz.py --auto --risk 0.3 --seed 7
"""

from palace_ai.cli import main
from palace_ai.knowledge import LogicKB
from palace_ai.palace import LogicPalace

if __name__ == "__main__":
    main(LogicPalace, LogicKB, "Part 1: logical agent (model checking) in the palace")
