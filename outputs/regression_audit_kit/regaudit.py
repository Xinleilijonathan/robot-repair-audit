"""regaudit: directional regression audits for edited skills.

A small, dependency-free toolkit for auditing updates to a persistent skill (a robot controller,
a prompt, a policy, a tool) against the behaviour it already had. It implements the protocol used
in the accompanying paper:

  1. replay_check          - verify the unchanged parent reproduces its own outcomes exactly,
                             so every paired flip after an edit is caused by the edit.
  2. directional           - pair candidate and parent on the same scenes; report gains G and
                             losses L separately (and the conditional loss), never only the net.
  3. null_population       - seeded random edits from the same bounded interface: a baseline
                             any proposer (e.g. an agent) can be compared against.
  4. loss_history /        - record which old successes past edits broke, and build a small
     history_suite           regression suite from the most frequently broken ones.
  5. zero_loss_gate        - admit an edit only if it improves the target and loses nothing on
                             the suite; commit the decision before running the full audit.

Records are plain dicts: {'config': str, 'scene': str, 'success': 0 or 1}. Bring your own runner.
"""
from __future__ import annotations

import math
import random
from collections import Counter
from typing import Iterable, Mapping

Outcomes = Mapping[str, int]  # scene id -> 0/1 success


def wilson(k: int, n: int, z: float = 1.959964):
    """Wilson score interval for k successes out of n; returns (p, lo, hi) or None if n == 0."""
    if n == 0:
        return None
    p = k / n
    d = 1 + z * z / n
    c = (p + z * z / (2 * n)) / d
    h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return p, max(0.0, c - h), min(1.0, c + h)


def outcomes(records: Iterable[Mapping], config: str) -> dict[str, int]:
    """Collect one configuration's outcomes; rejects duplicate scenes and non-binary values."""
    out: dict[str, int] = {}
    for r in records:
        if r['config'] != config:
            continue
        if r['scene'] in out:
            raise ValueError(f"duplicate scene {r['scene']} for {config}")
        if r['success'] not in (0, 1, True, False):
            raise ValueError('success must be binary')
        out[r['scene']] = int(r['success'])
    return out


def replay_check(run_a: Outcomes, run_b: Outcomes) -> dict:
    """Determinism certificate for the parent: two runs of the same ordered scene sequence."""
    if set(run_a) != set(run_b):
        raise ValueError('runs cover different scenes')
    agree = sum(run_a[s] == run_b[s] for s in run_a)
    return {'scenes': len(run_a), 'agree': agree, 'exact': agree == len(run_a)}


def directional(parent: Outcomes, cand: Outcomes, old_scenes: Iterable[str]) -> dict:
    """Paired gains and losses on old scenes. J(cand) - J(parent) = (G - L) / n."""
    old = list(old_scenes)
    succ = [s for s in old if parent[s]]
    lost = sorted(s for s in succ if not cand[s])
    gained = sorted(s for s in old if not parent[s] and cand[s])
    n = len(old)
    return {'n': n, 'parent_successes': len(succ), 'lost': lost, 'gained': gained,
            'net': len(gained) - len(lost),
            'unconditional_loss': len(lost) / n if n else None,
            'conditional_loss': wilson(len(lost), len(succ)),
            'conditional_gain': wilson(len(gained), n - len(succ))}


def null_population(bounds: Mapping[str, tuple], n: int, seed: int, k_choices=(1, 2), decimals: int = 3):
    """Seeded random edits over a bounded parameter interface (the 'null proposer')."""
    rng = random.Random(seed)
    names = list(bounds)
    pop = []
    for _ in range(n):
        k = rng.choice(list(k_choices))
        chosen = sorted(rng.sample(names, k), key=names.index)
        edit = {}
        for p in chosen:
            lo, hi = bounds[p]
            edit[p] = min(max(round(rng.uniform(lo, hi), decimals), lo), hi)
        pop.append(edit)
    return pop


def loss_history(lost_sets: Iterable[Iterable[str]]) -> Counter:
    """How many past edits broke each old scene."""
    c: Counter = Counter()
    for lost in lost_sets:
        c.update(set(lost))
    return c


def history_suite(counts: Mapping[str, int], eligible: Iterable[str], k: int, seed: int) -> list[str]:
    """The k eligible scenes (parent successes) most often broken in the past; seeded tie-break."""
    elig = sorted(eligible)
    tie = random.Random(seed)
    key = {s: tie.random() for s in elig}
    return sorted(elig, key=lambda s: (-counts.get(s, 0), key[s]))[:k]


def uniform_suite(eligible: Iterable[str], k: int, seed: int) -> list[str]:
    return sorted(random.Random(seed).sample(sorted(eligible), k))


def expected_uniform_detection(n_eligible: int, m_losses: int, k: int) -> float:
    """P(a uniformly drawn k-scene suite contains at least one of m lost scenes)."""
    if m_losses <= 0:
        return 0.0
    if k >= n_eligible:
        return 1.0
    return 1 - math.comb(n_eligible - m_losses, k) / math.comb(n_eligible, k)


def zero_loss_gate(parent: Outcomes, cand: Outcomes, target_scenes: Iterable[str], suite: Iterable[str]) -> dict:
    """Admit iff the target improves, the suite holds >= 1 parent success, and no suite success is lost."""
    t = list(target_scenes)
    s = list(suite)
    t_net = sum(cand[x] for x in t) - sum(parent[x] for x in t)
    lost = [x for x in s if parent[x] and not cand[x]]
    evaluable = any(parent[x] for x in s)
    return {'admit': t_net > 0 and evaluable and not lost, 'target_net': t_net, 'suite_lost': lost,
            'evaluable': evaluable}


def leave_one_out_detection(lost_sets: Mapping[str, set], eligible: Iterable[str], k: int, seed: int) -> dict:
    """For each edit with losses, build a history suite from the OTHER edits and test detection."""
    elig = sorted(eligible)
    rows = {}
    for c, lost in lost_sets.items():
        if not lost:
            continue
        counts = loss_history(v for d, v in lost_sets.items() if d != c)
        suite = history_suite(counts, elig, k, seed)
        rows[c] = {'history_detect': bool(set(suite) & lost),
                   'uniform_expected': expected_uniform_detection(len(elig), len(lost), k)}
    n = len(rows)
    return {'edits_with_losses': n,
            'history_detect_rate': sum(r['history_detect'] for r in rows.values()) / n if n else None,
            'uniform_expected_rate': sum(r['uniform_expected'] for r in rows.values()) / n if n else None,
            'per_edit': rows}
