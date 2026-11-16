"""Frozen analysis of the single-context audit (audit_protocol.md §5-6).

Primary: paired audit outcomes per candidate, delivered-controller outcomes per gate,
missed useful updates, admitted candidates with audit losses.
Secondary (diagnostic): decision stability by resampling validation-sized draws from the
audit pools, placement-margin shift, approximate tolerance sensitivity, parent repeat check.
Intervals are Wilson 95% over scenes for ONE context and two fixed candidates; they do not
generalise across repair contexts, proposers, robots or tasks.
"""
import argparse
import hashlib
import json
import math
import sys
from pathlib import Path
from statistics import median

import numpy as np

sys.path.insert(0, str(Path(__file__).parent))
from audit import admit, paired_metrics  # noqa: E402

TOLERANCES = (0.020, 0.025, 0.030, 0.035, 0.040)


def wilson(k, n, z=1.959964):
    if n == 0:
        return None
    p = k / n
    d = 1 + z * z / n
    c = (p + z * z / (2 * n)) / d
    h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return [round(k / n, 4), round(max(0.0, c - h), 4), round(min(1.0, c + h), 4)]


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


def ok(row, tol=None):
    if tol is None:
        return int(bool(row['object_state_success']))
    return int(bool(row['lift_observed'] and row['released_and_retreated'] and row['stable']
                    and row['final_error_m'] <= tol and row['steps'] < 1800))


def regime_metrics(parent, cand, ids, tol=None):
    m = paired_metrics([ok(parent[s], tol) for s in ids], [ok(cand[s], tol) for s in ids])
    failures = m['n'] - m['parent_successes']
    m['conditional_gain'] = m['gained'] / failures if failures else None
    m['net_count'] = m['gained'] - m['lost']
    return m


def summarize(parent, cand, target_ids, old_ids):
    t = regime_metrics(parent, cand, target_ids)
    o = regime_metrics(parent, cand, old_ids)
    return {'target': t, 'old': o,
            'ci95': {'parent_target_success': wilson(t['parent_successes'], t['n']),
                     'candidate_target_success': wilson(t['candidate_successes'], t['n']),
                     'old_conditional_loss': wilson(o['lost'], o['parent_successes']),
                     'old_conditional_gain': wilson(o['gained'], o['n'] - o['parent_successes']),
                     'parent_old_success': wilson(o['parent_successes'], o['n']),
                     'candidate_old_success': wilson(o['candidate_successes'], o['n'])},
            'useful': {'aggregate_objective': t['net_count'] > 0 and o['net_count'] >= 0,
                       'preservation_objective': t['net_count'] > 0 and o['lost'] == 0,
                       'preservation_5pct_tolerance': t['net_count'] > 0 and o['parent_successes'] > 0
                       and o['lost'] / o['parent_successes'] <= 0.05}}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--manifest', type=Path, required=True)
    ap.add_argument('--parent', type=Path, required=True)
    ap.add_argument('--candidates', type=Path, nargs='+', required=True)
    ap.add_argument('--gates', type=Path, required=True)
    ap.add_argument('--validation-manifest', type=Path)
    ap.add_argument('--validation-parent', type=Path)
    ap.add_argument('--validation-parent-repeat', type=Path)
    ap.add_argument('--draws', type=int, default=5000)
    ap.add_argument('--output', type=Path, required=True)
    args = ap.parse_args()

    manifest = json.loads(args.manifest.read_text())
    gates = json.loads(args.gates.read_text())
    target_ids = sorted(s['id'] for s in manifest if s['regime'] == 'target')
    old_ids = sorted(s['id'] for s in manifest if s['regime'] == 'old')
    geometry = {s['id']: (s['radius_m'], s['angle_deg']) for s in manifest}
    _, parent = read_folder(args.parent, manifest)
    cands = {}
    for f in args.candidates:
        cmeta, rows = read_folder(f, manifest)
        key = f.name.removeprefix('audit_')  # proposal identity, e.g. candidate_a
        assert key in gates['candidates'], f'no committed gate decision for {key}'
        assert gates['candidates'][key]['overrides'] == cmeta['controller_overrides'], f'{key} overrides differ'
        cands[key] = rows
    assert set(cands) == set(gates['candidates']), 'gate decisions refer to different candidates'

    out = {'evidence': 'frozen single-context audit; 1 repair context, 2 fixed candidates',
           'gate_decisions_committed_utc': gates['committed_utc'],
           'n_target': len(target_ids), 'n_old': len(old_ids), 'candidates': {}, 'delivered': {}}
    for name, cand in cands.items():
        s = summarize(parent, cand, target_ids, old_ids)
        shifts = [cand[k]['final_error_m'] - parent[k]['final_error_m'] for k in old_ids if ok(parent[k])]
        s['placement_error_shift_on_old_parent_successes_m'] = {
            'n': len(shifts), 'median': median(shifts) if shifts else None,
            'worse_gt_5mm': sum(x > 0.005 for x in shifts), 'better_gt_5mm': sum(x < -0.005 for x in shifts)}
        s['approx_tolerance_sensitivity'] = {
            f'{tol:.3f}': {'target': {k: v for k, v in regime_metrics(parent, cand, target_ids, tol).items()
                                      if k in ('parent_successes', 'candidate_successes', 'lost', 'gained')},
                           'old': {k: v for k, v in regime_metrics(parent, cand, old_ids, tol).items()
                                   if k in ('parent_successes', 'candidate_successes', 'lost', 'gained')}}
            for tol in TOLERANCES}
        s['loss_scenes'] = [{'id': k, 'radius_m': geometry[k][0], 'angle_deg': geometry[k][1],
                             'parent_err': round(parent[k]['final_error_m'], 4),
                             'cand_err': round(cand[k]['final_error_m'], 4),
                             'cand_failure': cand[k]['controller_status'].get('failure_reason')}
                            for k in old_ids if ok(parent[k]) and not ok(cand[k])]
        s['gain_scenes'] = [{'id': k, 'radius_m': geometry[k][0], 'angle_deg': geometry[k][1],
                             'parent_failure': parent[k]['controller_status'].get('failure_reason')}
                            for k in old_ids if not ok(parent[k]) and ok(cand[k])]
        s['gate_decisions'] = {g: gates['candidates'][name][g]
                               for g in ('target_only', 'aggregate', 'preservation', 'aggregate_unrestricted')}
        out['candidates'][name] = s

    # Delivered-controller audit outcomes per gate (parent retained after rejection).
    for gate, delivered in gates['delivered'].items():
        if delivered == 'parent':
            t = sum(ok(parent[k]) for k in target_ids); o = sum(ok(parent[k]) for k in old_ids)
            d = {'delivered': 'parent', 'target_success': wilson(t, len(target_ids)),
                 'old_success': wilson(o, len(old_ids)), 'old_losses': 0, 'old_gains': 0}
        else:
            s = out['candidates'][delivered]
            d = {'delivered': delivered,
                 'target_success': s['ci95']['candidate_target_success'],
                 'old_success': s['ci95']['candidate_old_success'],
                 'old_losses': s['old']['lost'], 'old_gains': s['old']['gained']}
        missed = {obj: [n for n, s in out['candidates'].items()
                        if s['useful'][obj] and not (gate != 'frozen' and s['gate_decisions'].get(gate))]
                  for obj in ('aggregate_objective', 'preservation_objective', 'preservation_5pct_tolerance')}
        admitted_with_losses = [n for n, s in out['candidates'].items()
                                if gate != 'frozen' and s['gate_decisions'].get(gate) and s['old']['lost'] > 0]
        out['delivered'][gate] = {**d, 'missed_useful': missed, 'admitted_with_audit_losses': admitted_with_losses}

    # Secondary: decision stability, validation-sized draws from the AUDIT pools (diagnostic).
    rng = np.random.default_rng(20261116)
    stability = {n: {'target_only': 0, 'aggregate': 0, 'preservation': 0, 'aggregate_unrestricted': 0}
                 for n in cands}
    for _ in range(args.draws):
        t4 = list(rng.choice(target_ids, 4, replace=False))
        o8 = list(rng.choice(old_ids, 8, replace=False))
        t12 = list(rng.choice(target_ids, 12, replace=False))
        for name, cand in cands.items():
            res = admit([ok(parent[k]) for k in o8], [ok(cand[k]) for k in o8],
                        [ok(parent[k]) for k in t4], [ok(cand[k]) for k in t4])
            st = stability[name]
            st['target_only'] += sum(ok(cand[k]) for k in t12) > sum(ok(parent[k]) for k in t12)
            st['aggregate'] += res['aggregate']
            st['preservation'] += res['preservation']
            st['aggregate_unrestricted'] += res['target']['net_change'] > 0 and res['old']['net_change'] >= 0
    out['decision_stability'] = {'draws': args.draws, 'seed': 20261116, 'admission_probability':
                                 {n: {g: round(v / args.draws, 4) for g, v in st.items()} for n, st in stability.items()}}

    if args.validation_parent and args.validation_parent_repeat and args.validation_manifest:
        vman = json.loads(args.validation_manifest.read_text())
        _, v1 = read_folder(args.validation_parent, vman)
        _, v2 = read_folder(args.validation_parent_repeat, vman)
        out['validation_parent_repeat_check'] = {
            'labels': len(v1), 'outcome_agreement': sum(ok(v1[k]) == ok(v2[k]) for k in v1),
            'max_abs_final_error_diff_m': max(abs(v1[k]['final_error_m'] - v2[k]['final_error_m']) for k in v1),
            'step_count_mismatches': sum(v1[k]['steps'] != v2[k]['steps'] for k in v1)}

    args.output.write_text(json.dumps(out, indent=2))
    brief = {n: {'target': f"{s['target']['parent_successes']}->{s['target']['candidate_successes']}/{s['target']['n']}",
                 'old_loss': s['old']['lost'], 'old_gain': s['old']['gained'],
                 'old_parent_successes': s['old']['parent_successes'], 'useful': s['useful'],
                 'gates': s['gate_decisions']} for n, s in out['candidates'].items()}
    print(json.dumps({'candidates': brief, 'delivered': out['delivered'],
                      'decision_stability': out['decision_stability'],
                      'validation_parent_repeat_check': out.get('validation_parent_repeat_check')}, indent=2))


if __name__ == '__main__':
    main()
