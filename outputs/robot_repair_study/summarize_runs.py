"""Summarize completed exploratory runs without treating repeats as repairs."""
import argparse
import hashlib
import json
from collections import defaultdict
from pathlib import Path

parser = argparse.ArgumentParser()
parser.add_argument('folder', type=Path)
args = parser.parse_args()
metadata = json.loads((args.folder / 'metadata.json').read_text())
assert hashlib.sha256((args.folder / 'runner_snapshot.py').read_bytes()).hexdigest() == metadata['script_sha256']
groups = defaultdict(list)
for path in sorted(args.folder.glob('rollout_*.json')):
    row = json.loads(path.read_text())
    groups[row['scene_id']].append(row)
summary = {'completed_rollouts': sum(map(len, groups.values())), 'scenes': {}}
for scene, rows in groups.items():
    summary['scenes'][scene] = {
        'successes': sum(r['object_state_success'] for r in rows), 'n': len(rows),
        'errors_m': [round(r['final_error_m'], 6) for r in rows],
        'failures': [r['controller_status'].get('failure_reason') for r in rows if not r['object_state_success']],
        'steps': [r['steps'] for r in rows],
    }
(args.folder / 'summary.json').write_text(json.dumps(summary, indent=2))
print(json.dumps(summary, indent=2))
