"""POST-HOC (not pre-registered): sensitivity of Extension 2's primary result to where detection is read.

Written after `analyze_ext2.py` reported S4 (candidate suite-batch outcomes agreed with audit outcomes
on 367 of 384 suite-scene labels). The frozen P1 reads history detection from the suite batch (20
scenes, shuffled order). This script (a) lists every disagreeing label with its direction and final
placement errors, and (b) recomputes P1 with detection read from the full audit instead, using the
same bootstrap seed. It changes nothing in the frozen analysis; outputs are labelled exploratory.

Run from the study folder:
  python explore_ext2_agreement.py --output results/exploratory/ext2_agreement.json
"""
import argparse
import json
from pathlib import Path

from analyze_ext2 import BOOT_SEED, boot_ci, mcnemar_exact, ok, p_detect_uniform, read_folder

R = Path('results/ext2')


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--output', type=Path, required=True)
    args = ap.parse_args()
    if args.output.exists():
        raise SystemExit(f'Refusing to overwrite {args.output}')
    manifest = json.loads(Path('ext1_audit_scenes.json').read_text())
    vmanifest = json.loads(Path('ext2_validation_scenes.json').read_text())
    suites = json.loads(Path('ext2_suites.json').read_text())
    gates = json.loads((R / 'ext2_gate_decisions.json').read_text())
    H8, U8 = suites['history_suite'], suites['uniform_suite']
    suite_scenes = H8 + U8
    _, parent = read_folder(R / 'audit_parent', manifest)
    _, vparent = read_folder(R / 'ext2_validation_parent', vmanifest)
    old = [s['id'] for s in manifest if s['regime'] == 'old']
    S = [s for s in old if ok(parent[s])]
    n = len(S)

    cells, rows = [], []
    for i in range(25, 49):
        key = f'r{i}'
        _, cand = read_folder(R / f'audit_{key}', manifest)
        _, vcand = read_folder(R / gates['candidates'][key]['validation_folder'], vmanifest)
        L = {s for s in S if not ok(cand[s])}
        for s in suite_scenes:
            if ok(cand[s]) != ok(vcand[s]):
                cells.append({'candidate': key, 'scene': s, 'suite': 'history' if s in H8 else 'uniform',
                              'parent_audit': ok(parent[s]), 'parent_batch': ok(vparent[s]),
                              'candidate_batch': ok(vcand[s]), 'candidate_audit': ok(cand[s]),
                              'final_error_batch_m': round(vcand[s]['final_error_m'], 5),
                              'final_error_audit_m': round(cand[s]['final_error_m'], 5)})
        if L:
            rows.append({'id': key, 'm': len(L),
                         'history8_batch': int(bool(gates['candidates'][key]['history']['lost'])),
                         'history8_audit': int(bool(L & set(H8))),
                         'uniform8_batch': int(bool(gates['candidates'][key]['uniform']['lost'])),
                         'uniform8_audit': int(bool(L & set(U8))),
                         'uniform8_expected': p_detect_uniform(n, len(L), 8)})

    def p1(field):
        diffs = [r[field] - r['uniform8_expected'] for r in rows]
        return {'history8_detect_rate': round(sum(r[field] for r in rows) / len(rows), 4),
                'uniform8_expected_detect_rate': round(sum(r['uniform8_expected'] for r in rows) / len(rows), 4),
                'difference_mean_ci95': boot_ci(diffs, 10000, BOOT_SEED)}

    b = sum(r['history8_audit'] and not r['uniform8_audit'] for r in rows)
    c = sum(r['uniform8_audit'] and not r['history8_audit'] for r in rows)
    out = {
        'label': 'POST-HOC sensitivity analysis; not part of the pre-registered Extension 2 protocol',
        'n_lossy': len(rows),
        'disagreeing_labels': len(cells),
        'by_direction': {
            'batch_fail_audit_success': sum(c_['candidate_batch'] == 0 and c_['candidate_audit'] == 1 for c_ in cells),
            'batch_success_audit_fail': sum(c_['candidate_batch'] == 1 and c_['candidate_audit'] == 0 for c_ in cells)},
        'by_suite': {'history': sum(c_['suite'] == 'history' for c_ in cells),
                     'uniform': sum(c_['suite'] == 'uniform' for c_ in cells)},
        'candidates_with_disagreement': sorted({c_['candidate'] for c_ in cells}),
        'P1_as_frozen_batch_detection': p1('history8_batch'),
        'P1_with_audit_detection': p1('history8_audit'),
        'realized_uniform_audit': {'uniform8_audit_detect_rate': round(sum(r['uniform8_audit'] for r in rows) / len(rows), 4),
                                   'history_only': b, 'uniform_only': c, 'mcnemar_exact_p': round(mcnemar_exact(b, c), 4)},
        'per_candidate': rows,
        'cells': cells,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(out, indent=2) + '\n')
    print(json.dumps({k: v for k, v in out.items() if k not in ('cells', 'per_candidate')}, indent=2))
    for c_ in cells:
        print(c_)


if __name__ == '__main__':
    main()
