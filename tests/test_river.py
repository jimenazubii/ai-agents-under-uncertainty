"""Tests for the river MDP."""

import random

import pytest

from river_mdp import (ACTIONS, all_states, create_river_grid, find_exit,
                       river_strength_for_cols, transition_probs, value_iteration)


@pytest.fixture
def river():
    random.seed(0)
    grid = create_river_grid(7, 6, nislas=2)
    return grid, river_strength_for_cols(7, 6)


def test_transitions_are_distributions(river):
    grid, strengths = river
    for s in all_states(grid):
        for a in ACTIONS:
            probs = transition_probs(grid, strengths, s, a)
            assert abs(sum(probs.values()) - 1) < 1e-9
            assert all(grid[i][j] != "I" for i, j in probs)


def test_policy_reaches_exit_with_high_probability(river):
    grid, strengths = river
    _, policy = value_iteration(grid, strengths)
    exit_pos = find_exit(grid)
    rng = random.Random(1)
    reached = 0
    for _ in range(300):
        s = (0, 0)
        for _ in range(200):
            if s == exit_pos:
                reached += 1
                break
            probs = transition_probs(grid, strengths, s, policy[s])
            s = rng.choices(list(probs), weights=probs.values())[0]
    assert reached / 300 > 0.95
