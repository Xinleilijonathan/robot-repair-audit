"""POST-HOC check for Extension 3 (written after the frozen analysis ran). Not part of the frozen protocol.

Four agent edits have exactly the same overrides as earlier audited edits. This compares each one's
Extension 3 audit folder with the earlier edit's audit folder (separate process, one to three days apart).

Usage: python explore_ext3_copy_replay.py --output results/exploratory/ext3_copy_replay.json
"""
import argparse
import json
from pathlib import Path

from analyze_ext2 import read_folder, replay

PAIRS = [('opus_m1', 'results/ext2/audit_r44'), ('haiku_b1', 'results/ext1/audit_candidate_a'),
         ('haiku_m1', 'results/ext1/audit_r04'), ('gpt_b1', 'results/ext1/audit_candidate_b')]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--output', type=Path, required=True)
    args = ap.parse_args()
    if args.output.exists():
        raise SystemExit(f'Refusing to overwrite {args.output}')
    manifest = json.loads(Path('ext1_audit_scenes.json').read_text())
    manifest = manifest['scenes'] if isinstance(manifest, dict) else manifest
    out = {'label': 'POST-HOC check; not part of the frozen Extension 3 protocol', 'pairs': []}
    for new, old in PAIRS:
        _, a = read_folder(Path('results/ext3/audit_' + new), manifest)
        _, b = read_folder(Path(old), manifest)
        out['pairs'].append({'ext3_edit': new, 'earlier_folder': old, **replay(a, b)})
    args.output.write_text(json.dumps(out, indent=2))
    print(json.dumps(out, indent=2))


if __name__ == '__main__':
    main()
