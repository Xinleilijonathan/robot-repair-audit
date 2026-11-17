"""EXPLORATORY, post hoc (Nov 16): robustness of the loss-history effect (see explore_history.py).

Stricter holdout: the suite for candidate c is built only from candidates that edit NONE of the
parameters c edits ("leave-one-family-out"), so near-duplicate edits cannot drive the effect.
Also reports per-candidate detection for the assistant repairs and the target improvers.
Reads existing rollouts only; no simulation; NOT pre-registered.
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
    index = {c['id']: c for c in json.loads((STUDY / 'proposals' / 'ext1' / 'index.json').read_text())['candidates']}
    params = {c: set(index[c]['overrides']) for c in IDS}
    man = json.loads((STUDY / 'ext1_audit_scenes.json').read_text())
    old = [s['id'] for s in man if s['regime'] == 'old']
    tgt = [s['id'] for s in man if s['regime'] == 'target']
    par = load(R / 'audit_parent')
    succ = [s for s in old if par[s]['object_state_success']]
    lost, tnet = {}, {}
    for c in IDS:
        rows = load(R / f'audit_{c}')
        lost[c] = {s for s in succ if not rows[s]['object_state_success']}
        tnet[c] = sum(rows[s]['object_state_success'] for s in tgt) - sum(par[s]['object_state_success'] for s in tgt)
    n = len(succ)
    lossy = [c for c in IDS if lost[c]]
    rng = random.Random(20261120)
    for mode in ('leave-one-out', 'leave-one-family-out'):
        print(f'\n{mode}:')
        for k in (4, 8):
            det_h = det_u = 0.0
            rows_out = []
            donors_min = 99
            for c in lossy:
                donors = [d for d in IDS if d != c and (mode == 'leave-one-out' or not (params[d] & params[c]))]
                donors_min = min(donors_min, len(donors))
                other = Counter(s for d in donors for s in lost[d])
                suite = sorted(succ, key=lambda s: (-other.get(s, 0), rng.random()))[:k]
                hit = sum(s in lost[c] for s in suite)
                m = len(lost[c])
                pu = 1 - math.comb(n - m, k) / math.comb(n, k)
                det_h += hit > 0
                det_u += pu
                if c in ('candidate_a', 'candidate_b') or tnet[c] > 0:
                    rows_out.append(f'{c}:{hit}/{m}(u={pu:.2f})')
            L = len(lossy)
            print(f'  k={k}: history P(detect)={det_h / L:.3f} vs uniform {det_u / L:.3f} '
                  f'(min donors {donors_min}); improvers/assistant: ' + ', '.join(rows_out))


if __name__ == '__main__':
    main()
