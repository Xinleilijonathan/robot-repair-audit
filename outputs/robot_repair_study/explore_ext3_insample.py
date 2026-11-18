"""POST-HOC sensitivity analysis for Extension 3 (written after the proposals were collected and BEFORE any
Extension 3 rollout finished; committed before the queue completed). Not part of the frozen protocol.

Why: 4 of the 7 distinct agent edits are exact copies of earlier audited edits (A, B and two random
edits). Those earlier edits' own losses were counted when the 50-edit history suite was built, so the
frozen P1 is partly in-sample for them. This script recomputes P1 two ways:
  (a) leave-own-out: an edit identical to an earlier edit is scored against a history suite rebuilt
      from the other 49 earlier edits (same ranking rule and tie-break seed as make_ext3_materials.py);
      new edits keep the frozen 50-edit suite;
  (b) new edits only: edits identical to an earlier edit are dropped.
Bootstrap 95% CI over edits (10,000 resamples, seed 20261135). Reads the frozen analysis output.

Usage: python explore_ext3_insample.py --analysis results/ext3/ext3_analysis.json --suites ext3_suites.json
                                       --output results/exploratory/ext3_insample.json
"""
import argparse
import json
import random
from collections import Counter
from pathlib import Path

from analyze_ext2 import boot_ci, p_detect_uniform

TIE_SEED, BOOT_SEED, K = 20261131, 20261135, 8


def suite_without(suites, skip_id):
    succ = suites['parent_old_successes']
    counts = Counter()
    for e in suites['past_edits']:
        if e['id'] != skip_id:
            counts.update(e['lost_scenes'])
    tie = random.Random(TIE_SEED)
    tiebreak = {s: tie.random() for s in succ}
    return set(sorted(succ, key=lambda s: (-counts.get(s, 0), tiebreak[s]))[:K])


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--analysis', type=Path, required=True)
    ap.add_argument('--suites', type=Path, required=True)
    ap.add_argument('--output', type=Path, required=True)
    args = ap.parse_args()
    if args.output.exists():
        raise SystemExit(f'Refusing to overwrite {args.output}')
    a = json.loads(args.analysis.read_text())
    suites = json.loads(args.suites.read_text())
    n_s = len(suites['parent_old_successes'])
    assert suite_without(suites, None) == set(suites['history_suite']), 'ranking rule does not reproduce the frozen suite'
    rows = []
    for r in a['distinct_edits']:
        if r['old_lost'] == 0:
            continue
        past = r['same_overrides_as_past_edit']
        suite = suite_without(suites, past['id']) if past else set(suites['history_suite'])
        rows.append({'id': r['id'], 'copy_of_past_edit': past['id'] if past else None,
                     'old_lost': r['old_lost'], 'frozen_detect': r['detect']['history8_audit'],
                     'leave_own_out_detect': bool(set(r['lost_scenes']) & suite),
                     'uniform8_expected': round(p_detect_uniform(n_s, r['old_lost'], 8), 4)})
    new = [x for x in rows if x['copy_of_past_edit'] is None]
    out = {'label': 'POST-HOC sensitivity analysis; not part of the frozen Extension 3 protocol',
           'n_lossy': len(rows), 'n_lossy_new_edits': len(new),
           'leave_own_out': {'detect_rate': round(sum(x['leave_own_out_detect'] for x in rows) / len(rows), 4) if rows else None,
                             'uniform8_expected_rate': round(sum(x['uniform8_expected'] for x in rows) / len(rows), 4) if rows else None,
                             'difference_mean_ci95': boot_ci([x['leave_own_out_detect'] - x['uniform8_expected'] for x in rows],
                                                             10000, BOOT_SEED)},
           'new_edits_only': {'detect_rate': round(sum(x['frozen_detect'] for x in new) / len(new), 4) if new else None,
                              'uniform8_expected_rate': round(sum(x['uniform8_expected'] for x in new) / len(new), 4) if new else None,
                              'difference_mean_ci95': boot_ci([x['frozen_detect'] - x['uniform8_expected'] for x in new],
                                                              10000, BOOT_SEED + 1)},
           'edits': rows}
    args.output.write_text(json.dumps(out, indent=2))
    print(json.dumps(out, indent=2))


if __name__ == '__main__':
    main()
