"""Frozen analysis of Extension 2 (extension2_protocol.md §6): do loss histories predict future regressions?

PRIMARY (P1): among new candidates with >= 1 audit loss (old parent successes lost on the full
120-scene audit), the share whose losses the 8-scene HISTORY suite detects in the suite batch,
minus the share an 8-scene UNIFORM suite is expected to detect (exact hypergeometric expectation
from each candidate's audit loss count). Bootstrap 95% CI over candidates (10,000 resamples,
seed 20261125). H1 is supported iff the CI's lower bound is above 0.

SECONDARY: realized uniform suite (McNemar exact); k=4 version; concentration of new losses on the
history suite; gate admissions with audit losses and missed useful candidates; suite-batch vs audit
agreement; parent replay against Extension 1. EXPLORATORY: leave-one-out history within the new
population. Intervals describe this proposal distribution, robot, task and context only.
"""
import argparse
import hashlib
import json
import math
from pathlib import Path

import numpy as np

BOOT_SEED = 20261125


def read_folder(folder, manifest):
    metadata = json.loads((folder / 'metadata.json').read_text())
    assert hashlib.sha256((folder / 'runner_snapshot.py').read_bytes()).hexdigest() == metadata['script_sha256']
    assert metadata['scenes'] == manifest, f'{folder} did not run the frozen manifest'
    rows = {}
    for path in sorted(folder.glob('rollout_*.json')):
        row = json.loads(path.read_text())
        assert row['scene_id'] not in rows and row['repeat_within_scene'] == 0
        rows[row['scene_id']] = row
    assert set(rows) == {s['id'] for s in manifest}, f'{folder} incomplete'
    return metadata, rows


def ok(row):
    return int(bool(row['object_state_success']))


def p_detect_uniform(n, m, k):
    if m <= 0:
        return 0.0
    if k >= n:
        return 1.0
    return 1 - math.comb(n - m, k) / math.comb(n, k)


def boot_ci(diffs, draws, seed):
    if not diffs:
        return None
    rng = np.random.default_rng(seed)
    arr = np.asarray(diffs, dtype=float)
    means = arr[rng.integers(0, len(arr), size=(draws, len(arr)))].mean(axis=1)
    return [round(float(arr.mean()), 4), round(float(np.percentile(means, 2.5)), 4),
            round(float(np.percentile(means, 97.5)), 4)]


def mcnemar_exact(b, c):
    n = b + c
    if n == 0:
        return 1.0
    tail = sum(math.comb(n, i) for i in range(min(b, c) + 1)) / 2 ** n
    return min(1.0, 2 * tail)


def replay(a_rows, b_rows):
    ids = sorted(a_rows)
    return {'labels': len(ids), 'outcome_agreement': sum(ok(a_rows[s]) == ok(b_rows[s]) for s in ids),
            'max_abs_final_error_diff_m': max(abs(a_rows[s]['final_error_m'] - b_rows[s]['final_error_m']) for s in ids),
            'step_count_mismatches': sum(a_rows[s]['steps'] != b_rows[s]['steps'] for s in ids)}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--audit-manifest', type=Path, required=True)
    ap.add_argument('--parent', type=Path, required=True)
    ap.add_argument('--candidates', type=Path, nargs='+', required=True)
    ap.add_argument('--gates', type=Path, required=True)
    ap.add_argument('--suites', type=Path, required=True)
    ap.add_argument('--ext1-parent', type=Path, required=True)
    ap.add_argument('--validation-manifest', type=Path, required=True)
    ap.add_argument('--validation-parent', type=Path, required=True)
    ap.add_argument('--validation-parent-repeat', type=Path)
    ap.add_argument('--bootstrap', type=int, default=10000)
    ap.add_argument('--output', type=Path, required=True)
    args = ap.parse_args()
    if args.output.exists():
        raise SystemExit(f'Refusing to overwrite {args.output}')

    manifest = json.loads(args.audit_manifest.read_text())
    vmanifest = json.loads(args.validation_manifest.read_text())
    gates = json.loads(args.gates.read_text())
    suites = json.loads(args.suites.read_text())
    H8, H4, U8 = suites['history_suite'], suites['history_suite_k4'], suites['uniform_suite']
    old = [s['id'] for s in manifest if s['regime'] == 'old']
    tgt = [s['id'] for s in manifest if s['regime'] == 'target']
    _, parent = read_folder(args.parent, manifest)
    _, ext1_parent = read_folder(args.ext1_parent, manifest)
    _, vparent = read_folder(args.validation_parent, vmanifest)
    S = [s for s in old if ok(parent[s])]
    F = [s for s in old if not ok(parent[s])]
    n_s = len(S)

    rows, lost_sets = [], {}
    for folder in args.candidates:
        cmeta, cand = read_folder(folder, manifest)
        key = folder.name.removeprefix('audit_')
        g = gates['candidates'][key]
        assert g['overrides'] == cmeta['controller_overrides'], f'{key} overrides differ from gate record'
        _, vcand = read_folder(args.gates.parent / g['validation_folder'], vmanifest)
        L = {s for s in S if not ok(cand[s])}
        G = {s for s in F if ok(cand[s])}
        lost_sets[key] = L
        tp, tc = sum(ok(parent[s]) for s in tgt), sum(ok(cand[s]) for s in tgt)
        m = len(L)
        tnet = tc - tp
        old_net = len(G) - m
        agree = [(ok(vcand[s]) == ok(cand[s])) for s in set(H8) | set(U8)]
        rows.append({
            'id': key, 'overrides': cmeta['controller_overrides'],
            'target_parent': tp, 'target_candidate': tc, 'target_net': tnet,
            'old_lost': m, 'old_gained': len(G), 'old_net': old_net,
            'conditional_loss': round(m / n_s, 4) if n_s else None,
            'useful': {'aggregate_objective': tnet > 0 and old_net >= 0,
                       'preservation_objective': tnet > 0 and m == 0,
                       'preservation_5pct_tolerance': tnet > 0 and n_s > 0 and m / n_s <= 0.05},
            'gates': {k: g[k] for k in ('target_gate', 'uniform_gate', 'history_gate', 'history4_gate')},
            'detect': {'history8_batch': bool(g['history']['lost']), 'uniform8_batch': bool(g['uniform']['lost']),
                       'history4_batch': bool(g['history_k4']['lost']),
                       'history8_audit': bool(L & set(H8)), 'uniform8_audit': bool(L & set(U8)),
                       'history4_audit': bool(L & set(H4)),
                       'uniform8_expected': round(p_detect_uniform(n_s, m, 8), 4),
                       'uniform4_expected': round(p_detect_uniform(n_s, m, 4), 4),
                       'current_practice8_expected': round(p_detect_uniform(len(old), m, 8), 4)},
            'losses_on_history_suite': len(L & set(H8)), 'losses_on_uniform_suite': len(L & set(U8)),
            'suite_batch_vs_audit_agreement': [sum(agree), len(agree)]})

    lossy = [r for r in rows if r['old_lost'] > 0]
    d = lambda r, k: float(r['detect'][k])
    out = {'evidence': 'Extension 2: confirmatory test of a hypothesis generated from Extension 1 (loss-history '
                       'suites); 24 new seeded random edits; one robot, task and repair context',
           'gate_decisions_committed_utc': gates['committed_utc'],
           'n_candidates': len(rows), 'n_lossy': len(lossy), 'n_parent_old_successes': n_s}
    out['P1_primary'] = {
        'history8_batch_detect_rate': round(sum(d(r, 'history8_batch') for r in lossy) / len(lossy), 4) if lossy else None,
        'uniform8_expected_detect_rate': round(sum(d(r, 'uniform8_expected') for r in lossy) / len(lossy), 4) if lossy else None,
        'difference_mean_ci95': boot_ci([d(r, 'history8_batch') - d(r, 'uniform8_expected') for r in lossy],
                                        args.bootstrap, BOOT_SEED)}
    ci = out['P1_primary']['difference_mean_ci95']
    out['P1_primary']['H1_supported'] = bool(ci and ci[1] > 0)
    b = sum(r['detect']['history8_batch'] and not r['detect']['uniform8_batch'] for r in lossy)
    c = sum(r['detect']['uniform8_batch'] and not r['detect']['history8_batch'] for r in lossy)
    out['S1_realized_uniform'] = {
        'uniform8_batch_detect_rate': round(sum(d(r, 'uniform8_batch') for r in lossy) / len(lossy), 4) if lossy else None,
        'history_only': b, 'uniform_only': c, 'mcnemar_exact_p': round(mcnemar_exact(b, c), 4)}
    out['S2_k4'] = {
        'history4_batch_detect_rate': round(sum(d(r, 'history4_batch') for r in lossy) / len(lossy), 4) if lossy else None,
        'uniform4_expected_detect_rate': round(sum(d(r, 'uniform4_expected') for r in lossy) / len(lossy), 4) if lossy else None,
        'difference_mean_ci95': boot_ci([d(r, 'history4_batch') - d(r, 'uniform4_expected') for r in lossy],
                                        args.bootstrap, BOOT_SEED + 1),
        'current_practice8_expected_detect_rate': round(sum(d(r, 'current_practice8_expected') for r in lossy) / len(lossy), 4) if lossy else None}
    tot = sum(r['old_lost'] for r in rows)
    out['S3_concentration'] = {'total_losses': tot,
                               'on_history_suite': sum(r['losses_on_history_suite'] for r in rows),
                               'on_uniform_suite': sum(r['losses_on_uniform_suite'] for r in rows),
                               'share_on_history_suite': round(sum(r['losses_on_history_suite'] for r in rows) / tot, 4) if tot else None,
                               'share_expected_if_uniform': round(len(H8) / n_s, 4) if n_s else None}
    adm = {}
    for gate in ('target_gate', 'uniform_gate', 'history_gate', 'history4_gate'):
        a = [r for r in rows if r['gates'][gate]]
        adm[gate] = {'admitted': len(a), 'admitted_with_audit_losses': sum(r['old_lost'] > 0 for r in a),
                     'total_audit_losses_among_admitted': sum(r['old_lost'] for r in a),
                     'admitted_useful': {o: sum(r['useful'][o] for r in a) for o in rows[0]['useful']},
                     'missed_useful': {o: sum(r['useful'][o] and not r['gates'][gate] for r in rows) for o in rows[0]['useful']}}
    out['S_admission'] = adm
    out['useful_counts'] = {o: sum(r['useful'][o] for r in rows) for o in rows[0]['useful']}
    out['target_improving'] = sum(r['target_net'] > 0 for r in rows)
    out['target_improving_with_old_loss'] = sum(r['target_net'] > 0 and r['old_lost'] > 0 for r in rows)
    ag = [sum(r['suite_batch_vs_audit_agreement'][i] for r in rows) for i in (0, 1)]
    out['S4_suite_batch_vs_audit_agreement'] = {
        'candidate_outcomes_agree': ag,
        'parent_outcomes_agree': [sum(ok(vparent[s]) == ok(parent[s]) for s in set(H8) | set(U8)), len(set(H8) | set(U8))]}
    out['S5_replay'] = {'audit_parent_vs_ext1_audit_parent': replay(parent, ext1_parent)}
    if args.validation_parent_repeat:
        _, vrep = read_folder(args.validation_parent_repeat, vmanifest)
        out['S5_replay']['validation_parent_repeat'] = replay(vparent, vrep)
    # EXPLORATORY: leave-one-out history built from the new population (and from ext1 + new)
    ext1_counts = suites['loss_counts_ext1']
    loo = {'new_only': [], 'ext1_plus_new': []}
    for r in lossy:
        others = [lost_sets[o] for o in lost_sets if o != r['id']]
        for mode in loo:
            cnt = {s: sum(s in L for L in others) + (ext1_counts.get(s, 0) if mode == 'ext1_plus_new' else 0) for s in S}
            suite = sorted(S, key=lambda s: (-cnt[s], s))[:8]
            loo[mode].append(float(bool(lost_sets[r['id']] & set(suite))) - r['detect']['uniform8_expected'])
    out['exploratory_loo_history_minus_uniform8'] = {k: boot_ci(v, args.bootstrap, BOOT_SEED + 2) for k, v in loo.items()}
    out['candidates'] = rows
    args.output.write_text(json.dumps(out, indent=2))
    print(json.dumps({k: v for k, v in out.items() if k != 'candidates'}, indent=2))
    print('id   tgt  lost gain | H8b U8b H4b | U8exp | gates t/u/h')
    for r in rows:
        dd, g = r['detect'], r['gates']
        print(f"{r['id']:<4} {r['target_net']:+3d} {r['old_lost']:4d} {r['old_gained']:4d} | "
              f"{int(dd['history8_batch']):3d} {int(dd['uniform8_batch']):3d} {int(dd['history4_batch']):3d} | "
              f"{dd['uniform8_expected']:.2f} | {int(g['target_gate'])}/{int(g['uniform_gate'])}/{int(g['history_gate'])}")


if __name__ == '__main__':
    main()
