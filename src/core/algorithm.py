"""
Speed-Recruiting Schedule Generator
====================================

Algorithm
---------
Students are split into sessions automatically: S = ceil(N / K).
Each session has at most K students, so per-session n ≤ K always holds.
The last session may have fewer students if N is not divisible by K.

Per session, two phases:

Phase 1 – **Min-Cost Max-Flow** (NetworkX)
    Build a flow network:
      source  →  student[s]   capacity=M,    weight=0
      student →  partner[p]   capacity=1,    weight=0   (at most one visit)
      partner →  sink         capacity=⌊nM/K⌋ or ⌈nM/K⌉, weight=0

    where n = students in this session (≤ K).

Phase 2 – **Bipartite Edge Colouring** (Vizing + Kempe chains)
    Assign each (student, partner) edge a colour ≡ round number so that:
      • no two edges of the same colour share a vertex  →
        each student meets exactly one partner per round, and
        each partner hosts at most one student per round.

Complexity per session
----------------------
  Phase 1: O(n·K·M) via NetworkX min_cost_flow (network-simplex)
  Phase 2: O(n·M·K) – each of the n·M edges may trigger a chain of length ≤ K
"""

from __future__ import annotations

import networkx as nx

from .constraints import GenerateParams


# Schedule type:
#   schedule[session_idx][student_in_session_idx][round_idx] = partner_number (1-indexed)
SessionSchedule = list[list[int]]  # one session: [student][round]
FullSchedule = list[SessionSchedule]  # all sessions


def generate_schedule(params: GenerateParams) -> FullSchedule:
    """
    Generate a speed-recruiting schedule split into sessions.

    Returns
    -------
    schedule : list of sessions
        ``schedule[session][student_in_session][round]`` = partner number (1-indexed).
        len(schedule) = n_sessions
        len(schedule[i]) = session_sizes[i]
        len(schedule[i][j]) = M
    """
    full: FullSchedule = []
    for session_size in params.session_sizes:
        session_schedule = _generate_session(
            session_size, params.n_partners, params.n_rounds
        )
        full.append(session_schedule)
    return full


def _generate_session(n: int, k: int, m: int) -> SessionSchedule:
    """Generate schedule for a single session with n students (n ≤ k)."""
    pairs = _flow_assignment(n, k, m)
    coloring = _edge_colour_bipartite(pairs, n, k, m)

    schedule: SessionSchedule = [[0] * m for _ in range(n)]
    for (s, p), r in coloring.items():
        schedule[s][r] = p + 1  # 1-indexed partner number

    return schedule


def _flow_assignment(n: int, k: int, m: int) -> list[tuple[int, int]]:
    """
    Return a list of ``(student_idx, partner_idx)`` pairs such that:
      * each student appears exactly M times   (meets M distinct partners), and
      * each partner appears ⌊nM/K⌋ or ⌈nM/K⌉ times   (balanced load).
    """
    G = nx.DiGraph()
    SRC, SNK = "__src__", "__snk__"

    total = n * m
    base = total // k
    extra = total % k

    for s in range(n):
        G.add_edge(SRC, f"s{s}", capacity=m, weight=0)

    for s in range(n):
        for p in range(k):
            G.add_edge(f"s{s}", f"p{p}", capacity=1, weight=0)

    for p in range(k):
        cap = base + (1 if p < extra else 0)
        if cap > 0:
            G.add_edge(f"p{p}", SNK, capacity=cap, weight=0)

    flow: dict[str, dict[str, int]] = nx.max_flow_min_cost(G, SRC, SNK)

    pairs: list[tuple[int, int]] = []
    for s in range(n):
        for p in range(k):
            if flow.get(f"s{s}", {}).get(f"p{p}", 0) > 0:
                pairs.append((s, p))

    if len(pairs) != n * m:
        raise RuntimeError(
            f"Flow yielded {len(pairs)} pairs, expected {n * m}. "
            "This should not happen for valid inputs."
        )

    return pairs


def _edge_colour_bipartite(
    pairs: list[tuple[int, int]],
    n_students: int,
    n_partners: int,
    n_rounds: int,
) -> dict[tuple[int, int], int]:
    s_colors: list[set[int]] = [set() for _ in range(n_students)]
    p_colors: list[set[int]] = [set() for _ in range(n_partners)]
    s_at: list[dict[int, int]] = [{} for _ in range(n_students)]
    p_at: list[dict[int, int]] = [{} for _ in range(n_partners)]
    result: dict[tuple[int, int], int] = {}

    for s, p in pairs:
        free_s = _first_free(s_colors[s], n_rounds)
        free_p = _first_free(p_colors[p], n_rounds)

        if free_s == free_p or free_s not in p_colors[p]:
            colour = free_s
        else:
            _kempe_swap(
                p_start=p,
                c1=free_s,
                c2=free_p,
                s_at=s_at,
                p_at=p_at,
                s_colors=s_colors,
                p_colors=p_colors,
                result=result,
            )
            colour = free_s

        result[(s, p)] = colour
        s_colors[s].add(colour)
        s_at[s][colour] = p
        p_colors[p].add(colour)
        p_at[p][colour] = s

    return result


def _first_free(used: set[int], limit: int) -> int:
    for c in range(limit):
        if c not in used:
            return c
    raise RuntimeError(
        "No free colour available – constraints violated. "
        f"Used colours: {used}, limit: {limit}"
    )


def _kempe_swap(
    p_start: int,
    c1: int,
    c2: int,
    s_at: list[dict[int, int]],
    p_at: list[dict[int, int]],
    s_colors: list[set[int]],
    p_colors: list[set[int]],
    result: dict[tuple[int, int], int],
) -> None:
    path: list[tuple[int, int, int]] = []
    p = p_start

    while True:
        if c1 not in p_colors[p]:
            break
        s = p_at[p][c1]
        path.append((s, p, c1))

        if c2 not in s_colors[s]:
            break
        next_p = s_at[s][c2]
        path.append((s, next_p, c2))
        p = next_p

    for s, p, c in path:
        s_colors[s].discard(c)
        s_at[s].pop(c, None)
        p_colors[p].discard(c)
        p_at[p].pop(c, None)
        result.pop((s, p), None)

    for s, p, old_c in path:
        new_c = c2 if old_c == c1 else c1
        s_colors[s].add(new_c)
        s_at[s][new_c] = p
        p_colors[p].add(new_c)
        p_at[p][new_c] = s
        result[(s, p)] = new_c
