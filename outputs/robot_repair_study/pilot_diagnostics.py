"""Development-pilot diagnostics: parent-parent agreement, placement-margin shifts,
approximate tolerance sensitivity, and elapsed cost.

Descriptive only. Repeat labels are not independent repairs. Tolerance sensitivity is
APPROXIMATE: it re-scores with final-frame error (the runner stores only the final
settle frame, not all 30) while keeping every other v2 predicate as recorded. The
frozen evaluator remains v2 at 0.030 m; sensitivity rows are not alternative results.
"""
import argparse
import hashlib
import json
from pathlib import Path
from statistics import median


def read_folder(folder):
    metadata = json.loads((folder / 'metadata.json').read_text())
    assert hashlib.sha256((folder / 'runner_snapshot.py').read_bytes()).hexdigest() == metadata['script_sha256']
    rows = {}
    for path in sorted(folder.glob('rollout_*.json')):
        row = json.loads(path.read_text())
        rows[(row['scene_id'], row['repeat_within_scene'])] = row
    return metadata, rows


def rescore(row, tol):
    """Approximate success at an alternative placement tolerance (final-frame error)."""
    return bool(row['lift_observed'] and row['released_and_retreated'] and row['stable']
                and row['final_error_m'] <= tol and row['steps'] < 1800)


def cells(parent, cand, keys, score):
    out = {'both_fail': 0, 'gain': 0, 'loss': 0, 'both_success': 0}
    for k in keys:
        a, b = score(parent[k]), score(cand[k])
        out['both_success' if a and b else 'loss' if a else 'gain' if b else 'both_fail'] += 1
    return out


def cost(rows, metadata_path):
    vals = list(rows.values())
    return {'rollouts': len(vals),
            'startup_seconds': vals[0]['startup_seconds'],
            'setup_seconds': vals[0]['setup_seconds'],
            'sum_reset_seconds': round(sum(r['reset_seconds'] for r in vals), 1),
            'sum_execution_seconds': round(sum(r['execution_seconds'] for r in vals), 1),
            'sum_evaluation_seconds': round(sum(r['evaluation_seconds'] for r in vals), 1),
            'median_execution_seconds': round(median(r['execution_seconds'] for r in vals), 2),
            'peak_working_set_gb': round(max(r['process_peak_working_set_bytes'] or 0 for r in vals) / 2**30, 2)}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--discovery', type=Path, nargs='+', required=True,
                    help='original parent folders (pooled by label, metadata not merged)')
    ap.add_argument('--parent', type=Path, required=True)
    ap.add_argument('--candidates', type=Path, nargs='+', required=True)
    ap.add_argument('--target', required=True)
    ap.add_argument('--ledger', type=Path)
    ap.add_argument('--output', type=Path, required=True)
    args = ap.parse_args()

    discovery = {}
    for folder in args.discovery:
        _, rows = read_folder(folder)
        assert not set(rows) & set(discovery)
        discovery.update(rows)
    pmeta, parent = read_folder(args.parent)
    assert set(discovery) == set(parent), 'discovery and repeat parent label sets differ'

    diffs = [abs(discovery[k]['final_error_m'] - parent[k]['final_error_m']) for k in parent]
    step_diffs = sum(discovery[k]['steps'] != parent[k]['steps'] for k in parent)
    transitions = cells(discovery, parent, list(parent), lambda r: bool(r['object_state_success']))
    report = {'evidence': 'exploratory development diagnostics',
              'parent_parent': {'labels': len(parent), **transitions,
                                'max_abs_final_error_diff_m': max(diffs),
                                'labels_with_different_step_count': step_diffs},
              'within_scene_repeat_variation': {}, 'candidates': {}, 'costs': {}}

    # Within-process repeat variation: do the three resets of a scene differ?
    scenes = sorted({k[0] for k in parent})
    varying = [s for s in scenes if len({round(parent[(s, i)]['final_error_m'], 6) for i in range(3)}) > 1]
    report['within_scene_repeat_variation'] = {'scenes': len(scenes), 'scenes_with_differing_repeats': varying}

    target = [k for k in parent if k[0] == args.target]
    old = [k for k in parent if k[0] != args.target]
    old_parent_success = [k for k in old if parent[k]['object_state_success']]
    for folder in args.candidates:
        cmeta, cand = read_folder(folder)
        assert set(cand) == set(parent) and cmeta['scenes'] == pmeta['scenes']
        shifts = [cand[k]['final_error_m'] - parent[k]['final_error_m'] for k in old_parent_success]
        sens = {}
        for tol in (0.020, 0.025, 0.030, 0.035, 0.040):
            score = lambda r, t=tol: rescore(r, t)
            sens[f'{tol:.3f}'] = {'target': cells(parent, cand, target, score),
                                  'old': cells(parent, cand, old, score)}
        # check the approximation reproduces the frozen labels at 0.030
        agree = sum(rescore(r, 0.030) == bool(r['object_state_success'])
                    for rows in (parent, cand) for r in rows.values())
        report['candidates'][folder.name] = {
            'overrides': cmeta['controller_overrides'],
            'old_parent_success_labels': len(old_parent_success),
            'placement_error_shift_on_old_parent_successes_m': {
                'median': median(shifts), 'min': min(shifts), 'max': max(shifts),
                'n_worse_by_more_than_5mm': sum(s > 0.005 for s in shifts),
                'n_better_by_more_than_5mm': sum(s < -0.005 for s in shifts)},
            'approx_tolerance_sensitivity': sens,
            'approx_rescore_agreement_at_0.030': f'{agree}/{2 * len(parent)}'}
        report['costs'][folder.name] = cost(cand, folder)
    report['costs'][args.parent.name] = cost(parent, args.parent)
    if args.ledger:
        from datetime import datetime
        for entry in json.loads(args.ledger.read_text()):
            s = datetime.fromisoformat(entry['started_utc'].replace('Z', '+00:00')[:26] + '+00:00')
            e = datetime.fromisoformat(entry['ended_utc'].replace('Z', '+00:00')[:26] + '+00:00')
            report['costs'].setdefault(entry['batch'], {})['batch_wall_minutes'] = round((e - s).total_seconds() / 60, 2)
    args.output.write_text(json.dumps(report, indent=2))
    print(json.dumps(report, indent=2))


if __name__ == '__main__':
    main()
