"""Frozen analysis of Extension 3 (extension3_protocol.md §6): agent-proposed repairs.

UNIT: a distinct agent edit (exact duplicates are analysed once; a no-op edit equals the parent by
exact replay). Condition comparisons use proposals (each fresh agent session) as units.

PRIMARY (P1): among distinct agent edits with >= 1 audit loss, the share whose losses the 8-scene
history suite built from the 50 earlier candidates detects (read from the audit), minus the share an
8-scene uniform suite is expected to detect (exact hypergeometric expectation from each edit's loss
count). Bootstrap 95% CI over edits (10,000 resamples, seed 20261132). Supported iff the lower bound
is above 0; not tested (inconclusive) if fewer than 5 distinct edits have losses.

SECONDARY: S1 target improvers that lose old successes (Wilson 95%) and loss-free improvements;
S2 memory vs blind proposals (permutation test on mean old losses, 10,000, seed 20261134); S3 per
agent; S4 agent vs the 50 earlier edits; S5 the Extension 2 suite, k=4 suites and concentration;
S6 parent replay against Extension 1. Intervals describe these agents, prompts, panel, robot and task.
"""
import argparse
import json
import math
from pathlib import Path

import numpy as np

from analyze_ext2 import boot_ci, ok, p_detect_uniform, read_folder, replay

BOOT_SEED, PERM_SEED = 20261132, 20261134


def wilson(k, n, z=1.96):
    if n == 0:
        return None
    p = k / n
    den = 1 + z * z / n
    mid = (p + z * z / (2 * n)) / den
    half = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / den
    return [round(p, 4), round(max(0.0, mid - half), 4), round(min(1.0, mid + half), 4)]


def perm_test(a, b, draws, seed):
    if not a or not b:
        return None
    rng = np.random.default_rng(seed)
    pool = np.asarray(a + b, dtype=float)
    obs = abs(np.mean(a) - np.mean(b))
    hits = 0
    for _ in range(draws):
        rng.shuffle(pool)
        hits += abs(pool[:len(a)].mean() - pool[len(a):].mean()) >= obs - 1e-12
    return round((hits + 1) / (draws + 1), 4)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--audit-manifest', type=Path, required=True)
    ap.add_argument('--parent', type=Path, required=True)
    ap.add_argument('--ext1-parent', type=Path, required=True)
    ap.add_argument('--index', type=Path, required=True)
    ap.add_argument('--results', type=Path, required=True)
    ap.add_argument('--suites', type=Path, required=True)
    ap.add_argument('--bootstrap', type=int, default=10000)
    ap.add_argument('--output', type=Path, required=True)
    args = ap.parse_args()
    if args.output.exists():
        raise SystemExit(f'Refusing to overwrite {args.output}')

    manifest = json.loads(args.audit_manifest.read_text())
    index = json.loads(args.index.read_text())
    suites = json.loads(args.suites.read_text())
    H8, H4 = set(suites['history_suite']), set(suites['history_suite_k4'])
    E8, E4 = set(suites['ext2_history_suite']), set(suites['ext2_history_suite_k4'])
    old = [s['id'] for s in manifest if s['regime'] == 'old']
    tgt = [s['id'] for s in manifest if s['regime'] == 'target']
    _, parent = read_folder(args.parent, manifest)
    _, ext1_parent = read_folder(args.ext1_parent, manifest)
    S = [s for s in old if ok(parent[s])]
    F = [s for s in old if not ok(parent[s])]
    n_s = len(S)
    assert sorted(S) == sorted(suites['parent_old_successes']), 'parent old successes differ from the frozen record'

    props = index['candidates']
    by_id = {p['id']: p for p in props}
    past_by_key = {json.dumps(e['overrides'], sort_keys=True): e for e in suites['past_edits']}
    edits = {}
    for p in props:
        if not p['run'] and not p['noop']:
            continue
        if p['noop']:
            cand, cmeta_ov = parent, p['overrides']
        else:
            cmeta, cand = read_folder(args.results / f"audit_{p['id']}", manifest)
            assert cmeta['controller_overrides'] == p['overrides'], f"{p['id']} overrides differ from the index"
            cmeta_ov = p['overrides']
        L = {s for s in S if not ok(cand[s])}
        G = {s for s in F if ok(cand[s])}
        tp, tc = sum(ok(parent[s]) for s in tgt), sum(ok(cand[s]) for s in tgt)
        m, tnet, onet = len(L), tc - tp, len(G) - len(L)
        past = past_by_key.get(json.dumps(cmeta_ov, sort_keys=True))
        edits[p['id']] = {
            'id': p['id'], 'agent': p['agent'], 'condition': p['condition'], 'overrides': cmeta_ov,
            'noop': bool(p['noop']), 'target_parent': tp, 'target_candidate': tc, 'target_net': tnet,
            'old_lost': m, 'old_gained': len(G), 'old_net': onet, 'conditional_loss': round(m / n_s, 4),
            'lost_scenes': sorted(L),
            'useful': {'aggregate_objective': tnet > 0 and onet >= 0, 'preservation_objective': tnet > 0 and m == 0,
                       'preservation_5pct_tolerance': tnet > 0 and m / n_s <= 0.05},
            'detect': {'history8_audit': bool(L & H8), 'history4_audit': bool(L & H4),
                       'ext2_history8_audit': bool(L & E8), 'ext2_history4_audit': bool(L & E4),
                       'uniform8_expected': round(p_detect_uniform(n_s, m, 8), 4),
                       'uniform4_expected': round(p_detect_uniform(n_s, m, 4), 4)},
            'losses_on_history_suite': len(L & H8),
            'same_overrides_as_past_edit': None if past is None else
                {'id': past['id'], 'population': past['population'],
                 'identical_lost_set': sorted(L) == past['lost_scenes']}}

    rows = list(edits.values())
    lossy = [r for r in rows if r['old_lost'] > 0]
    d = lambda r, k: float(r['detect'][k])
    rate = lambda rs, k: round(sum(d(r, k) for r in rs) / len(rs), 4) if rs else None
    out = {'evidence': 'Extension 3: agent-proposed repairs (five CLI agents, blind vs memory prompts); '
                       'one robot, task, panel and repair context',
           'n_proposals': len(props), 'n_excluded': sum(p['excluded'] for p in props),
           'n_duplicates': sum(bool(p['duplicate_of']) for p in props), 'n_noop': sum(bool(p['noop']) for p in props),
           'n_distinct_edits': len(rows), 'n_lossy': len(lossy), 'n_parent_old_successes': n_s}
    p1 = {'history8_detect_rate': rate(lossy, 'history8_audit'),
          'uniform8_expected_detect_rate': rate(lossy, 'uniform8_expected')}
    if len(lossy) >= 5:
        p1['difference_mean_ci95'] = boot_ci([d(r, 'history8_audit') - d(r, 'uniform8_expected') for r in lossy],
                                             args.bootstrap, BOOT_SEED)
        p1['H1_supported'] = bool(p1['difference_mean_ci95'][1] > 0)
    else:
        p1['difference_mean_ci95'] = None
        p1['H1_supported'] = 'inconclusive: fewer than 5 distinct edits with losses'
    out['P1_primary'] = p1

    imp = [r for r in rows if r['target_net'] > 0]
    out['S1_target_improvers'] = {
        'n_target_improving': len(imp), 'with_old_loss': sum(r['old_lost'] > 0 for r in imp),
        'with_old_loss_wilson95': wilson(sum(r['old_lost'] > 0 for r in imp), len(imp)),
        'loss_free_improvements': [r['id'] for r in imp if r['old_lost'] == 0],
        'useful_counts': {o: sum(r['useful'][o] for r in rows) for o in ('aggregate_objective', 'preservation_objective',
                                                                         'preservation_5pct_tolerance')}}
    # S2: proposals as units (duplicates and no-ops take their distinct edit's result)
    def result_of(p):
        return edits[p['duplicate_of'] or p['id']]
    units = [dict(result_of(p), proposal=p['id'], condition=p['condition'], agent=p['agent'])
             for p in props if not p['excluded']]
    s2 = {}
    for cond in ('blind', 'memory'):
        u = [x for x in units if x['condition'] == cond]
        s2[cond] = {'n_proposals': len(u), 'n_excluded': sum(p['excluded'] and p['condition'] == cond for p in props),
                    'mean_old_lost': round(float(np.mean([x['old_lost'] for x in u])), 3) if u else None,
                    'mean_old_gained': round(float(np.mean([x['old_gained'] for x in u])), 3) if u else None,
                    'mean_target_net': round(float(np.mean([x['target_net'] for x in u])), 3) if u else None,
                    'target_improving': sum(x['target_net'] > 0 for x in u),
                    'loss_free_target_improving': sum(x['target_net'] > 0 and x['old_lost'] == 0 for x in u),
                    'aggregate_useful': sum(x['useful']['aggregate_objective'] for x in u)}
    s2['permutation_p_mean_old_lost'] = perm_test([x['old_lost'] for x in units if x['condition'] == 'blind'],
                                                  [x['old_lost'] for x in units if x['condition'] == 'memory'],
                                                  10000, PERM_SEED)
    out['S2_memory_vs_blind'] = s2
    out['S3_per_proposal'] = [{k: x[k] for k in ('proposal', 'agent', 'condition', 'overrides', 'target_net',
                                                 'old_lost', 'old_gained', 'useful')} for x in units]
    past = suites['past_edits']
    pimp = [e for e in past if e['target_gained'] - e['target_lost'] > 0]
    out['S4_vs_50_earlier'] = {
        'earlier_target_improving': len(pimp), 'earlier_improvers_with_loss': sum(e['old_lost'] > 0 for e in pimp),
        'earlier_improvers_mean_conditional_loss': round(float(np.mean([e['old_lost'] / n_s for e in pimp])), 4),
        'agent_improvers_mean_conditional_loss': round(float(np.mean([r['conditional_loss'] for r in imp])), 4) if imp else None,
        'pooled_improvers_with_loss_wilson95': wilson(sum(e['old_lost'] > 0 for e in pimp) + sum(r['old_lost'] > 0 for r in imp),
                                                      len(pimp) + len(imp))}
    tot = sum(r['old_lost'] for r in rows)
    out['S5_other_suites'] = {
        'history4_detect_rate': rate(lossy, 'history4_audit'), 'uniform4_expected_detect_rate': rate(lossy, 'uniform4_expected'),
        'history4_difference_mean_ci95': boot_ci([d(r, 'history4_audit') - d(r, 'uniform4_expected') for r in lossy],
                                                 args.bootstrap, BOOT_SEED + 1),
        'ext2_history8_detect_rate': rate(lossy, 'ext2_history8_audit'),
        'ext2_history8_difference_mean_ci95': boot_ci([d(r, 'ext2_history8_audit') - d(r, 'uniform8_expected') for r in lossy],
                                                      args.bootstrap, BOOT_SEED + 2),
        'total_losses': tot, 'on_history_suite': sum(r['losses_on_history_suite'] for r in rows),
        'share_on_history_suite': round(sum(r['losses_on_history_suite'] for r in rows) / tot, 4) if tot else None,
        'share_expected_if_uniform': round(len(H8) / n_s, 4)}
    out['S6_replay'] = {'audit_parent_vs_ext1_audit_parent': replay(parent, ext1_parent)}
    out['distinct_edits'] = rows
    args.output.write_text(json.dumps(out, indent=2))
    print(json.dumps({k: v for k, v in out.items() if k not in ('distinct_edits', 'S3_per_proposal')}, indent=2))
    print('proposal     cond   tgt  lost gain | H8 U8exp | overrides')
    for x in units:
        print(f"{x['proposal']:<12} {x['condition']:<6} {x['target_net']:+3d} {x['old_lost']:4d} {x['old_gained']:4d} | "
              f"{int(x['detect']['history8_audit']):2d} {x['detect']['uniform8_expected']:.2f} | {x['overrides']}")


if __name__ == '__main__':
    main()
