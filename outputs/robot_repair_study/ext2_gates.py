"""Commit Extension 2 gate decisions from the suite (validation) batches (extension2_protocol.md §5).

Run after all suite batches and BEFORE any audit batch. Refuses to overwrite.
Per candidate, paired against the suite-batch parent:
  target evidence  : vt01-vt04 (4 pairs)
  history suite    : 8 old scenes most often lost by the 26 Extension 1 candidates
  uniform suite    : 8 old scenes drawn uniformly from the same parent successes
  history suite k=4: the first 4 history scenes (secondary)
Gates (zero-loss rules; each spends 4 target + k old pairs):
  history_gate : target net > 0, >= 1 parent success in the history suite, and zero history losses
  uniform_gate : target net > 0, >= 1 parent success in the uniform suite, and zero uniform losses
  history4_gate: as history_gate on the k=4 suite (secondary)
  target_gate  : target net > 0 (reference)
"""
import argparse
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path


def read_folder(folder, manifest):
    metadata = json.loads((folder / 'metadata.json').read_text())
    assert hashlib.sha256((folder / 'runner_snapshot.py').read_bytes()).hexdigest() == metadata['script_sha256']
    assert metadata['scenes'] == manifest, f'{folder} did not run the frozen suite manifest'
    rows = {}
    for path in sorted(folder.glob('rollout_*.json')):
        row = json.loads(path.read_text())
        assert row['repeat_within_scene'] == 0
        assert row['scene_id'] not in rows
        rows[row['scene_id']] = int(bool(row['object_state_success']))
    assert set(rows) == {s['id'] for s in manifest}, f'{folder} incomplete'
    return metadata, rows


def suite_evidence(parent, cand, ids):
    lost = [s for s in ids if parent[s] == 1 and cand[s] == 0]
    gained = [s for s in ids if parent[s] == 0 and cand[s] == 1]
    return {'n': len(ids), 'parent_successes': sum(parent[s] for s in ids),
            'candidate_successes': sum(cand[s] for s in ids), 'lost': lost, 'gained': gained}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--manifest', type=Path, required=True)
    ap.add_argument('--suites', type=Path, required=True)
    ap.add_argument('--parent', type=Path, required=True)
    ap.add_argument('--candidates', type=Path, nargs='+', required=True, help='in proposal order')
    ap.add_argument('--output', type=Path, required=True)
    args = ap.parse_args()
    if args.output.exists():
        raise SystemExit(f'Refusing to overwrite committed gate decisions {args.output}')
    manifest = json.loads(args.manifest.read_text())
    suites = json.loads(args.suites.read_text())
    pmeta, parent = read_folder(args.parent, manifest)
    assert pmeta['controller_overrides'] == {}
    tids, hist, hist4, uni = (suites['target_ids'], suites['history_suite'], suites['history_suite_k4'],
                              suites['uniform_suite'])
    out = {'committed_utc': datetime.now(timezone.utc).isoformat(),
           'manifest_sha256': hashlib.sha256(args.manifest.read_bytes()).hexdigest(),
           'suites_sha256': hashlib.sha256(args.suites.read_bytes()).hexdigest(),
           'parent_folder': args.parent.name,
           'parent_suite_successes': {'target': sum(parent[s] for s in tids),
                                      'history': sum(parent[s] for s in hist),
                                      'uniform': sum(parent[s] for s in uni)},
           'rule_note': 'Zero-loss gates; each spends 4 target + k old pairs. Parent rollouts shared.',
           'candidates': {}}
    for folder in args.candidates:
        cmeta, cand = read_folder(folder, manifest)
        key = folder.name.removeprefix('ext2_validation_')
        t = suite_evidence(parent, cand, tids)
        h = suite_evidence(parent, cand, hist)
        h4 = suite_evidence(parent, cand, hist4)
        u = suite_evidence(parent, cand, uni)
        tnet = t['candidate_successes'] - t['parent_successes']
        out['candidates'][key] = {
            'overrides': cmeta['controller_overrides'], 'validation_folder': folder.name,
            'target': t, 'history': h, 'history_k4': h4, 'uniform': u, 'target_net': tnet,
            'target_gate': tnet > 0,
            'history_gate': tnet > 0 and h['parent_successes'] > 0 and not h['lost'],
            'history4_gate': tnet > 0 and h4['parent_successes'] > 0 and not h4['lost'],
            'uniform_gate': tnet > 0 and u['parent_successes'] > 0 and not u['lost']}
    args.output.write_text(json.dumps(out, indent=2))
    print(json.dumps({k: {g: v[g] for g in ('target_net', 'target_gate', 'history_gate', 'uniform_gate')}
                      | {'history_lost': len(v['history']['lost']), 'uniform_lost': len(v['uniform']['lost'])}
                      for k, v in out['candidates'].items()}, indent=1))


if __name__ == '__main__':
    main()
