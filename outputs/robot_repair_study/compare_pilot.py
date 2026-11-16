"""Descriptive development-panel comparison; no inferential independence claim."""
import argparse
import hashlib
import json
from pathlib import Path

def read(folder):
    metadata = json.loads((folder / 'metadata.json').read_text())
    assert hashlib.sha256((folder / 'runner_snapshot.py').read_bytes()).hexdigest() == metadata['script_sha256']
    rows = [json.loads(p.read_text()) for p in sorted(folder.glob('rollout_*.json'))]
    keys = [(r['scene_id'], r['repeat_within_scene']) for r in rows]
    assert len(keys) == len(set(keys)), 'Duplicate paired labels'
    return metadata, dict(zip(keys, rows))

def compare(parent, candidate, keys):
    cells = {'both_fail': 0, 'gain': 0, 'loss': 0, 'both_success': 0}
    for key in keys:
        a = bool(parent[key]['object_state_success'])
        b = bool(candidate[key]['object_state_success'])
        name = 'both_success' if a and b else 'loss' if a else 'gain' if b else 'both_fail'
        cells[name] += 1
    n = len(keys)
    successes = cells['loss'] + cells['both_success']
    return dict(n=n, **cells, parent_successes=successes,
        candidate_successes=cells['gain'] + cells['both_success'],
        net_gain=cells['gain']-cells['loss'],
        conditional_loss=cells['loss']/successes if successes else None)

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--parent', type=Path, required=True)
    parser.add_argument('--comparisons', type=Path, nargs='+', required=True)
    parser.add_argument('--target', required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    metadata, parent = read(args.parent)
    target = [k for k in parent if k[0] == args.target]
    old = [k for k in parent if k[0] != args.target]
    assert target and old
    result = {'evidence': 'exploratory development; repeat labels are not independent repairs',
        'target': args.target, 'comparisons': {}}
    for path in args.comparisons:
        cm, candidate = read(path)
        assert set(parent) == set(candidate), 'Incomplete or mismatched paired panel'
        assert cm['scenes'] == metadata['scenes'], 'Scene manifests differ'
        assert {r['success_definition'] for r in parent.values()} == {r['success_definition'] for r in candidate.values()}
        target_metrics, old_metrics = compare(parent, candidate, target), compare(parent, candidate, old)
        aggregate = target_metrics['net_gain'] > 0 and old_metrics['net_gain'] >= 0 and old_metrics['parent_successes'] > 0
        preserving = aggregate and old_metrics['loss'] == 0
        result['comparisons'][path.name] = {'parameters': cm['controller_overrides'],
            'target': target_metrics, 'old': old_metrics,
            'full_panel_aggregate': aggregate, 'full_panel_preservation': preserving,
            'gate_note': 'Diagnostic full-panel decisions, not frozen budget-matched validation.',
            'scenes': {s: compare(parent, candidate, [k for k in parent if k[0] == s]) for s in sorted({k[0] for k in parent})}}
    args.output.write_text(json.dumps(result, indent=2))
    print(json.dumps({k: {a:b for a,b in v.items() if a != 'scenes'} for k,v in result['comparisons'].items()}, indent=2))

if __name__ == '__main__':
    main()
