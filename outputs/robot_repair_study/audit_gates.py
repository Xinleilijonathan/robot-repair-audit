"""Commit budget-matched gate decisions from the frozen validation draw (audit_protocol.md §4).

Run after the three validation batches and BEFORE any audit batch. Refuses to overwrite.
Uses audit.admit so gate logic is the unit-tested implementation.
"""
import argparse
import hashlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from audit import admit  # noqa: E402

AGG_TARGET = [f'vt{i:02d}' for i in range(1, 5)]
AGG_OLD = [f'vo{i:02d}' for i in range(1, 9)]
TONLY_TARGET = [f'vt{i:02d}' for i in range(1, 13)]


def read_folder(folder, manifest):
    metadata = json.loads((folder / 'metadata.json').read_text())
    assert hashlib.sha256((folder / 'runner_snapshot.py').read_bytes()).hexdigest() == metadata['script_sha256']
    assert metadata['scenes'] == manifest, f'{folder} did not run the frozen validation manifest'
    rows = {}
    for path in sorted(folder.glob('rollout_*.json')):
        row = json.loads(path.read_text())
        assert row['repeat_within_scene'] == 0
        assert row['scene_id'] not in rows
        rows[row['scene_id']] = int(bool(row['object_state_success']))
    assert set(rows) == {s['id'] for s in manifest}, f'{folder} incomplete'
    return metadata, rows


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--manifest', type=Path, required=True)
    ap.add_argument('--parent', type=Path, required=True)
    ap.add_argument('--candidates', type=Path, nargs='+', required=True, help='in proposal order (tie-break)')
    ap.add_argument('--output', type=Path, required=True)
    args = ap.parse_args()
    if args.output.exists():
        raise SystemExit(f'Refusing to overwrite committed gate decisions {args.output}')
    manifest = json.loads(args.manifest.read_text())
    pmeta, parent = read_folder(args.parent, manifest)
    assert pmeta['controller_overrides'] == {}
    decisions = {'committed_utc': datetime.now(timezone.utc).isoformat(),
                 'manifest_sha256': hashlib.sha256(args.manifest.read_bytes()).hexdigest(),
                 'parent_folder': args.parent.name, 'rule_note':
                 'Budget-matched: aggregate/preservation share 4 target + 8 old pairs (24 rollouts); '
                 'target-only uses 12 target pairs (24 rollouts). Parent rollouts are shared across candidates.',
                 'candidates': {}, 'delivered': {}}
    admitted = {g: [] for g in ('target_only', 'aggregate', 'preservation', 'aggregate_unrestricted')}
    for order, folder in enumerate(args.candidates):
        cmeta, cand = read_folder(folder, manifest)
        key = folder.name.removeprefix('audit_validation_')  # proposal identity, e.g. candidate_a
        res = admit([parent[s] for s in AGG_OLD], [cand[s] for s in AGG_OLD],
                    [parent[s] for s in AGG_TARGET], [cand[s] for s in AGG_TARGET])
        t12_parent = sum(parent[s] for s in TONLY_TARGET)
        t12_cand = sum(cand[s] for s in TONLY_TARGET)
        unrestricted = res['target']['net_change'] > 0 and res['old']['net_change'] >= 0
        entry = {'overrides': cmeta['controller_overrides'],
                 'aggregate_evidence': {'target': res['target'], 'old': res['old'],
                                        'evaluable': res['evaluable']},
                 'target_only_evidence': {'parent_successes': t12_parent, 'candidate_successes': t12_cand, 'n': 12},
                 'target_only': t12_cand > t12_parent,
                 'aggregate': res['aggregate'], 'preservation': res['preservation'],
                 'aggregate_unrestricted': unrestricted}
        entry['validation_folder'] = folder.name
        decisions['candidates'][key] = entry
        agg_score = res['target']['candidate_successes'] + res['old']['candidate_successes']
        for gate, score in (('target_only', t12_cand), ('aggregate', agg_score),
                            ('preservation', agg_score), ('aggregate_unrestricted', agg_score)):
            if entry[gate]:
                admitted[gate].append((-score, order, key))
    decisions['delivered']['frozen'] = 'parent'
    for gate, items in admitted.items():
        decisions['delivered'][gate] = sorted(items)[0][2] if items else 'parent'
    args.output.write_text(json.dumps(decisions, indent=2))
    print(json.dumps(decisions, indent=2))


if __name__ == '__main__':
    main()
