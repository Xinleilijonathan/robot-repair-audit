"""EXPLORATORY, post hoc (Nov 16): do different edits break the SAME old scenes? If so, a regression
suite curated from earlier edits' losses ("loss history") should catch a new edit's losses at a
budget where uniform sampling misses them.

Extension audit only (26 candidates on one 90-scene old panel). Leave-one-candidate-out: the suite
for candidate c ranks old parent successes by how many OTHER candidates lost them. Reads existing
rollouts only; no simulation. NOT pre-registered: any use must be labelled exploratory.
"""
import json
import math
import random
from collections import Counter
from pathlib import Path

STUDY = Path(__file__).resolve().parent
R = STUDY / 'results' / 'ext1'
IDS = ['candidate_a', 'candidate_b'] + [f'r{i:02d}' for i in range(1, 25)]


def load(folder):
    rows = {}
    for p in sorted(folder.glob('rollout_*.json')):
        r = json.loads(p.read_text())
        rows[r['scene_id']] = r
    return rows


def main():
    man = json.loads((STUDY / 'ext1_audit_scenes.json').read_text())
    old = [s['id'] for s in man if s['regime'] == 'old']
    par = load(R / 'audit_parent')
    succ = [s for s in old if par[s]['object_state_success']]
    lost = {}
    for c in IDS:
        rows = load(R / f'audit_{c}')
        lost[c] = {s for s in succ if not rows[s]['object_state_success']}
    counts = Counter(s for L in lost.values() for s in L)
    total = sum(counts.values())
    per_scene = sorted((counts.get(s, 0) for s in succ), reverse=True)
    print('parent successes:', len(succ), '| loss events:', total, '| scenes never lost:',
          sum(v == 0 for v in per_scene))
    print('losses per scene (sorted, top 15):', per_scene[:15])
    for q in (5, 10, 15):
        print(f'share of all loss events on the {q} most-lost scenes: {sum(per_scene[:q]) / total:.3f}')
    lossy = [c for c in IDS if lost[c]]
    n = len(succ)
    rng = random.Random(20261120)
    print('\nleave-one-candidate-out detection of >=1 loss (and mean losses caught), budget k old scenes:')
    for k in (4, 8, 12):
        det_h, det_u, cau_h, cau_u = 0.0, 0.0, 0.0, 0.0
        for c in lossy:
            other = Counter(s for d, L in lost.items() if d != c for s in L)
            ranked = sorted(succ, key=lambda s: (-other.get(s, 0), rng.random()))
            suite = ranked[:k]
            hits = sum(s in lost[c] for s in suite)
            det_h += hits > 0
            cau_h += hits
            m = len(lost[c])
            det_u += 1 - math.comb(n - m, k) / math.comb(n, k)
            cau_u += k * m / n
        L = len(lossy)
        print(f'  k={k:2d}: history suite P(detect)={det_h / L:.3f}, mean caught={cau_h / L:.2f} | '
              f'uniform parent successes P(detect)={det_u / L:.3f}, mean caught={cau_u / L:.2f}')
    # which candidates share losses: Jaccard between lost sets of candidates with >=3 losses
    big = [c for c in lossy if len(lost[c]) >= 3]
    jac = [len(lost[a] & lost[b]) / len(lost[a] | lost[b]) for i, a in enumerate(big) for b in big[i + 1:]]
    exp = []
    for i, a in enumerate(big):
        for b in big[i + 1:]:
            ma, mb = len(lost[a]), len(lost[b])
            e_int = ma * mb / n
            exp.append(e_int / (ma + mb - e_int))
    print(f'\nmean pairwise Jaccard of lost sets: {sum(jac) / len(jac):.3f} '
          f'(independent-placement expectation ~{sum(exp) / len(exp):.3f}), pairs={len(jac)}')


if __name__ == '__main__':
    main()
