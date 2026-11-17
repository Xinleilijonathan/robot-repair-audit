"""EXPLORATORY, post hoc (Nov 16): does the parent's own success margin predict which old successes
an edit breaks, and would spending the old-scene budget on low-margin scenes catch more losses?

Reads existing audit rollouts only (first audit: A, B; extension: 26 candidates). No simulation.
NOT a frozen analysis: any use in the paper must be labelled exploratory, and a confirmatory test
needs a fresh, pre-registered draw.

Margin of a parent success = 3.0 cm tolerance minus the parent's final placement error.
"""
import argparse
import json
import random
from pathlib import Path

STUDY = Path(__file__).resolve().parent
R = STUDY / 'results'
TOL = 0.03
EXT_IDS = ['candidate_a', 'candidate_b'] + [f'r{i:02d}' for i in range(1, 25)]


def load(folder):
    rows = {}
    for p in sorted(folder.glob('rollout_*.json')):
        r = json.loads(p.read_text())
        rows[r['scene_id']] = r
    return rows


def auc(pos, neg):
    if not pos or not neg:
        return None
    wins = sum((p > n) + 0.5 * (p == n) for p in pos for n in neg)
    return wins / (len(pos) * len(neg))


def panel(manifest, parent_dir, cand_dirs):
    man = json.loads(manifest.read_text())
    old = [s['id'] for s in man if s['regime'] == 'old']
    par = load(parent_dir)
    succ = [s for s in old if par[s]['object_state_success']]
    err = {s: par[s]['final_error_m'] for s in old}
    lost = {}
    for c, d in cand_dirs.items():
        rows = load(d)
        lost[c] = {s for s in succ if not rows[s]['object_state_success']}
    return old, succ, err, lost, par


def describe(name, old, succ, err, lost):
    out = {'n_old': len(old), 'n_parent_successes': len(succ)}
    es = sorted(err[s] for s in succ)
    out['parent_success_error_cm_quantiles'] = {q: round(100 * es[int(q * (len(es) - 1))], 2)
                                               for q in (0.1, 0.25, 0.5, 0.75, 0.9)}
    pos, neg = [], []
    for c, L in lost.items():
        for s in succ:
            (pos if s in L else neg).append(err[s])
    out['pooled_auc_parent_error_predicts_loss'] = round(auc(pos, neg), 3)
    out['n_loss_events'] = len(pos)
    per = {c: round(auc([err[s] for s in L], [err[s] for s in succ if s not in L]), 3)
           for c, L in lost.items() if len(L) >= 3}
    out['per_candidate_auc_(>=3 losses)'] = per
    bins = [(0.0, 0.01), (0.01, 0.015), (0.015, 0.02), (0.02, 0.025), (0.025, 0.0301)]
    tab = []
    for lo, hi in bins:
        ss = [s for s in succ if lo <= err[s] < hi]
        k = sum(s in L for L in lost.values() for s in ss)
        tab.append({'parent_error_cm': f'{100 * lo:.1f}-{100 * min(hi, TOL):.1f}', 'scenes': len(ss),
                    'loss_rate_per_candidate_scene': round(k / (len(ss) * len(lost)), 3) if ss else None,
                    'share_of_all_losses': round(k / len(pos), 3) if pos else None})
    out['loss_rate_by_parent_error'] = tab
    top = sorted(succ, key=lambda s: -err[s])[:max(1, round(0.2 * len(succ)))]
    out['share_of_losses_in_most_fragile_20pct'] = round(
        sum(s in L for L in lost.values() for s in top) / len(pos), 3) if pos else None
    return out


def power(old, succ, err, lost, budgets, pool_size, draws, seed):
    rng = random.Random(seed)
    lossy = [c for c, L in lost.items() if L]
    succ_set = set(succ)
    res = {}
    for k in budgets:
        hit = {'uniform_old': 0, 'uniform_parent_successes': 0, 'margin_targeted': 0}
        for _ in range(draws):
            pool = rng.sample(old, pool_size)
            uni = rng.sample(pool, k)
            ps = [s for s in pool if s in succ_set]
            uni_ps = rng.sample(ps, min(k, len(ps)))
            tgt = sorted(ps, key=lambda s: -err[s])[:k]
            for c in lossy:
                L = lost[c]
                hit['uniform_old'] += any(s in L for s in uni)
                hit['uniform_parent_successes'] += any(s in L for s in uni_ps)
                hit['margin_targeted'] += any(s in L for s in tgt)
        res[f'k={k}'] = {m: round(v / (draws * len(lossy)), 3) for m, v in hit.items()}
    return {'candidates_with_losses': len(lossy), 'screening_pool': pool_size, 'draws': draws,
            'P(detect >=1 loss)': res}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--output', type=Path)
    ap.add_argument('--draws', type=int, default=5000)
    args = ap.parse_args()
    out = {'evidence': 'EXPLORATORY post-hoc analysis of existing audit rollouts; not pre-registered'}
    first = panel(STUDY / 'audit_scenes.json', R / 'audit_parent',
                  {c: R / f'audit_{c}' for c in ('candidate_a', 'candidate_b')})
    ext = panel(STUDY / 'ext1_audit_scenes.json', R / 'ext1' / 'audit_parent',
                {c: R / 'ext1' / f'audit_{c}' for c in EXT_IDS})
    out['first_audit'] = describe('first', *first[:4])
    out['extension'] = describe('ext', *ext[:4])
    out['extension_power'] = power(*ext[:4], budgets=(4, 8, 12), pool_size=40, draws=args.draws, seed=20261120)
    out['first_audit_power'] = power(*first[:4], budgets=(4, 8, 12), pool_size=40, draws=args.draws, seed=20261120)
    text = json.dumps(out, indent=2)
    print(text)
    if args.output:
        if args.output.exists():
            raise SystemExit(f'{args.output} exists; refusing to overwrite')
        args.output.write_text(text)


if __name__ == '__main__':
    main()
