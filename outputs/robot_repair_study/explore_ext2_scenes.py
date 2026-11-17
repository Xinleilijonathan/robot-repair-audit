"""POST-HOC, descriptive (not pre-registered): per-scene loss counts in Extension 1 vs Extension 2.

For each of the 73 old scenes the audit parent solves, count how many Extension 1 candidates (26)
and how many new Extension 2 candidates (24) lose it. Reports a Spearman rank correlation between
the two counts and the share of Extension 2 losses on the Extension 1 top-k scenes. Also pools the
'every target improver lost old successes' count across both populations with a Wilson interval.
Writes the per-scene table used by plot_ext2.py.

Run from the study folder:
  python explore_ext2_scenes.py --output results/exploratory/ext2_scenes.json
"""
import argparse
import json
import math
from pathlib import Path

import numpy as np

from analyze_ext2 import ok, read_folder


def ranks(x):
    x = np.asarray(x, dtype=float)
    order = x.argsort(kind='mergesort')
    r = np.empty(len(x))
    r[order] = np.arange(len(x))
    for v in np.unique(x):  # average ranks for ties
        idx = x == v
        r[idx] = r[idx].mean()
    return r


def spearman(a, b):
    ra, rb = ranks(a), ranks(b)
    return float(np.corrcoef(ra, rb)[0, 1])


def wilson(k, n, z=1.959964):
    p = k / n
    d = 1 + z * z / n
    c = (p + z * z / (2 * n)) / d
    h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return [round(p, 4), round(c - h, 4), round(c + h, 4)]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--output', type=Path, required=True)
    args = ap.parse_args()
    if args.output.exists():
        raise SystemExit(f'Refusing to overwrite {args.output}')
    manifest = json.loads(Path('ext1_audit_scenes.json').read_text())
    suites = json.loads(Path('ext2_suites.json').read_text())
    ext1 = json.loads(Path('results/ext1/population_analysis.json').read_text())
    ext2 = json.loads(Path('results/ext2/ext2_analysis.json').read_text())
    _, parent = read_folder(Path('results/ext2/audit_parent'), manifest)
    old = [s['id'] for s in manifest if s['regime'] == 'old']
    S = [s for s in old if ok(parent[s])]
    c1 = suites['loss_counts_ext1']
    c2 = {s: 0 for s in S}
    for i in range(25, 49):
        _, cand = read_folder(Path(f'results/ext2/audit_r{i}'), manifest)
        for s in S:
            c2[s] += 1 - ok(cand[s])
    a = [c1[s] for s in S]
    b = [c2[s] for s in S]
    total2 = sum(b)
    top = suites['history_ranked']  # frozen order, seeded tie-break; top[:8] is the history suite
    share = {k: round(sum(c2[s] for s in top[:k]) / total2, 4) for k in (4, 8, 10, 20)}

    # 'every target improver lost old successes', pooled over both populations (random edits + A, B)
    imp1 = [r for r in ext1['candidates'] if r['target_net'] > 0] if 'candidates' in ext1 else None
    imp2 = [r for r in ext2['candidates'] if r['target_net'] > 0]
    pooled = None
    if imp1 is not None:
        k = sum(r['old_loss'] > 0 for r in imp1) + sum(r['old_lost'] > 0 for r in imp2)
        n = len(imp1) + len(imp2)
        pooled = {'improvers_with_loss': k, 'improvers': n, 'wilson95': wilson(k, n)}

    out = {
        'label': 'POST-HOC descriptive analysis; not part of the pre-registered Extension 2 protocol',
        'n_eligible': len(S),
        'ext1_total_losses': sum(a), 'ext2_total_losses': total2,
        'spearman_ext1_vs_ext2_counts': round(spearman(a, b), 4),
        'ext2_share_on_ext1_topk': share,
        'expected_share_if_uniform': {k: round(k / len(S), 4) for k in share},
        'ext2_scenes_never_lost_by_ext1': {
            'scenes': sum(c1[s] == 0 for s in S),
            'ext2_losses_on_them': sum(c2[s] for s in S if c1[s] == 0)},
        'target_improvers_pooled': pooled,
        'per_scene': [{'scene': s, 'ext1_losses': c1[s], 'ext2_losses': c2[s],
                       'history_suite': s in suites['history_suite'], 'uniform_suite': s in suites['uniform_suite']}
                      for s in S],
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(out, indent=2) + '\n')
    print(json.dumps({k: v for k, v in out.items() if k != 'per_scene'}, indent=2))


if __name__ == '__main__':
    main()
