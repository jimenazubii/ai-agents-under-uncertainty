"""Grid geometry shared by every environment and agent."""

from collections import deque

# Directions use (row, col) offsets. Row 0 is the top of the palace.
DIRECTIONS = {"U": (-1, 0), "D": (1, 0), "L": (0, -1), "R": (0, 1)}


def neighbours(cell, n):
    """Orthogonally adjacent cells inside an n x n grid."""
    r, c = cell
    result = []
    for dr, dc in DIRECTIONS.values():
        rr, cc = r + dr, c + dc
        if 0 <= rr < n and 0 <= cc < n:
            result.append((rr, cc))
    return result


def step(cell, direction):
    """Cell reached by moving one step in `direction` (may be outside the grid)."""
    dr, dc = DIRECTIONS[direction]
    return cell[0] + dr, cell[1] + dc


def direction_to(src, dst):
    """Direction letter that moves from `src` to the adjacent cell `dst`."""
    for d, (dr, dc) in DIRECTIONS.items():
        if (src[0] + dr, src[1] + dc) == dst:
            return d
    raise ValueError(f"{dst} is not adjacent to {src}")


def walls(cell, n):
    """Wall percepts (up, down, left, right): True where the grid ends."""
    r, c = cell
    return r == 0, r == n - 1, c == 0, c == n - 1


def bfs_path(start, goal, allowed):
    """
    Shortest path from `start` to `goal` moving only through `allowed` cells.

    `goal` must be in `allowed`. Returns the list of cells after `start`
    (empty if start == goal) or None if the goal is unreachable.
    Breadth-first search is optimal here because every move costs 1.
    """
    if start == goal:
        return []
    allowed = set(allowed)
    n = 1 + max(max(r, c) for r, c in allowed | {start, goal})
    parent = {start: None}
    queue = deque([start])
    while queue:
        cell = queue.popleft()
        for nxt in neighbours(cell, n):
            if nxt in parent or nxt not in allowed:
                continue
            parent[nxt] = cell
            if nxt == goal:
                path = [nxt]
                while parent[path[-1]] != start:
                    path.append(parent[path[-1]])
                return path[::-1]
            queue.append(nxt)
    return None


def bfs_distances(start, allowed):
    """Distance (in moves) from `start` to every reachable cell in `allowed`."""
    allowed = set(allowed) | {start}
    n = 1 + max(max(r, c) for r, c in allowed)
    dist = {start: 0}
    queue = deque([start])
    while queue:
        cell = queue.popleft()
        for nxt in neighbours(cell, n):
            if nxt in allowed and nxt not in dist:
                dist[nxt] = dist[cell] + 1
                queue.append(nxt)
    return dist
