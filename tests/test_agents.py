"""Correctness tests for the knowledge bases and the autonomous agent."""

import random

import numpy as np
import pytest

from palace_ai.agent import Agent
from palace_ai.bayes import BayesBeliefs
from palace_ai.grid import direction_to, neighbours
from palace_ai.knowledge import LogicKB
from palace_ai.palace import START, BayesPalace, LogicPalace

ENVIRONMENTS = [(LogicPalace, LogicKB), (BayesPalace, BayesBeliefs)]


def random_safe_walk(env_cls, kb_cls, seed, steps=25):
    """Walk randomly through cells the KB has proved safe; yield (game, kb) at each step."""
    game, kb = env_cls.random(seed=seed), kb_cls()
    kb.tell(game.pos, game.percept())
    rng = random.Random(seed)
    yield game, kb
    for _ in range(steps):
        options = [c for c in neighbours(game.pos, game.n) if c in kb.safe_cells()]
        if not options:
            return
        percept = game.move(direction_to(game.pos, rng.choice(options)))
        assert game.alive, "the agent entered a cell the KB had proved safe and died"
        kb.tell(game.pos, percept)
        yield game, kb


@pytest.mark.parametrize("env_cls,kb_cls", ENVIRONMENTS)
def test_deductions_are_sound(env_cls, kb_cls):
    """Every cell declared safe is safe, and every located soldier is really there."""
    for seed in range(150):
        for game, kb in random_safe_walk(env_cls, kb_cls, seed):
            for cell in kb.safe_cells():
                assert not game.deadly(cell)
            soldier = kb.known_soldier()
            if soldier is not None:
                assert soldier == game.soldier


@pytest.mark.parametrize("env_cls,kb_cls", ENVIRONMENTS)
def test_true_world_keeps_positive_probability(env_cls, kb_cls):
    for seed in range(100):
        for game, kb in random_safe_walk(env_cls, kb_cls, seed):
            assert kb.p_soldier()[game.soldier] > 0
            assert kb.p_exit()[game.exit] > 0


def test_logic_kb_starts_with_all_models():
    kb = LogicKB()
    assert kb.n_models == 6545 * 32          # C(35, 3) pit sets x 32 soldier cells
    assert np.isclose(kb.p_pit()[0, 1], 3 / 35)


def test_logic_posterior_matches_rejection_sampling():
    """Model-checking probabilities equal the true Bayesian posterior."""
    game = LogicPalace.random(seed=0)
    kb = LogicKB()
    percept = game.percept()
    kb.tell(START, percept)
    rng = random.Random(1)
    hits, accepted = np.zeros((6, 6)), 0
    for _ in range(60_000):
        sample = LogicPalace.random(seed=rng.random())
        if sample.stimuli(START) == percept.stimuli:
            accepted += 1
            for cell in sample.pits:
                hits[cell] += 1
    empirical = hits / accepted
    assert np.abs(empirical - kb.p_pit()).max() < 0.02


@pytest.mark.parametrize("env_cls,kb_cls", ENVIRONMENTS)
def test_cautious_agent_never_dies(env_cls, kb_cls):
    for seed in range(200):
        result = Agent(kb_cls(), risk_threshold=0).run(env_cls.random(seed=seed))
        assert result.outcome in {"escaped", "stuck"}
        assert result.risky_moves == 0


@pytest.mark.parametrize("env_cls,kb_cls", ENVIRONMENTS)
def test_agent_completes_easy_palaces(env_cls, kb_cls):
    results = [Agent(kb_cls()).run(env_cls.random(seed=s)) for s in range(100)]
    assert sum(r.success for r in results) >= 55
