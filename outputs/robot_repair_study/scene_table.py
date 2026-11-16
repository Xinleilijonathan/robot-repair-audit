"""Per-scene/per-repeat outcome table across run folders (descriptive diagnostic only).

Usage: python scene_table.py LABEL=FOLDER [LABEL=FOLDER ...] [--json OUT]
Several folders may share one label (e.g. two discovery-parent folders); their
rollouts are pooled by (scene_id, repeat_within_scene) WITHOUT inventing combined
metadata. Each folder's runner hash is verified individually.
"""
import argparse
import hashlib
import json
from collections import OrderedDict
from pathlib import Path


def read_folder(folder):
    metadata = json.loads((folder / 'metadata.json').read_text())
    digest = hashlib.sha256((folder / 'runner_snapshot.py').read_bytes()).hexdigest()
    assert digest == metadata['script_sha256'], f'runner hash mismatch in {folder}'
    rows = {}
    for path in sorted(folder.glob('rollout_*.json')):
        row = json.loads(path.read_text())
        key = (row['scene_id'], row['repeat_within_scene'])
        assert key not in rows, f'duplicate {key} in {folder}'
        rows[key] = row
    return metadata, rows


def phase(row):
    if row['object_state_success']:
        return 'OK'
    reason = row['controller_status'].get('failure_reason') or ''
    if reason:
        return reason.split(' ')[0]
    return 'EVAL:' + ','.join(k for k in ('lift_observed', 'released_and_retreated', 'stable')
                              if not row.get(k)) + f"|err={row['final_error_m']:.3f}"


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('runs', nargs='+')
    parser.add_argument('--json', type=Path)
    args = parser.parse_args()
    labelled = OrderedDict()
    order = []
    for spec in args.runs:
        label, folder = spec.split('=', 1)
        metadata, rows = read_folder(Path(folder))
        for scene in metadata['scenes']:
            sid = scene['id'] if isinstance(scene, dict) else scene
            if sid not in order:
                order.append(sid)
        merged = labelled.setdefault(label, {})
        overlap = set(merged) & set(rows)
        assert not overlap, f'overlapping keys within label {label}: {sorted(overlap)[:3]}'
        merged.update(rows)
    labels = list(labelled)
    keys = sorted({k for rows in labelled.values() for k in rows},
                  key=lambda k: (order.index(k[0]) if k[0] in order else 999, k[1]))
    out = []
    print('scene_id      rep  ' + '  '.join(f'{l:>22}' for l in labels))
    for key in keys:
        cells = []
        rec = {'scene_id': key[0], 'repeat_within_scene': key[1]}
        for label in labels:
            row = labelled[label].get(key)
            if row is None:
                cells.append(f'{"-":>22}')
                rec[label] = None
            else:
                p = phase(row)
                cells.append(f'{p[:16]:>16} {row["final_error_m"]:.3f}')
                rec[label] = {'success': bool(row['object_state_success']), 'phase': p,
                              'final_error_m': row['final_error_m'], 'steps': row['steps'],
                              'execution_seconds': row.get('execution_seconds')}
        out.append(rec)
        print(f'{key[0]:<12} {key[1]:>3}  ' + '  '.join(cells))
    totals = {l: sum(r['object_state_success'] for r in labelled[l].values()) for l in labels}
    print('totals', json.dumps(totals))
    if args.json:
        args.json.write_text(json.dumps({'labels': labels, 'totals': totals, 'rows': out}, indent=2))


if __name__ == '__main__':
    main()
