"""Extension 1 population analysis (extension1_protocol.md §5). Reads the outputs of the frozen
analyze_audit.py and audit_gates.py; computes no new per-scene quantities.

Q1 target-improving candidates with >=1 old loss; Q2 offsetting gains and gate disagreement;
Q3 per-gate admissions, admitted-with-loss, missed-useful; Q4 assistant-candidate replication.
Wilson intervals over candidates describe this proposal distribution only.
"""
import argparse
import json
import math
from pathlib import Path

GATES = ('target_only', 'aggregate', 'preservation', 'aggregate_unrestricted')
OBJECTIVES = ('aggregate_objective', 'preservation_objective', 'preservation_5pct_tolerance')


def wilson(k, n, z=1.959964):
    if n == 0:
        return None
    p = k / n
    d = 1 + z * z / n
    c = (p + z * z / (2 * n)) / d
    h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return [k, n, round(p, 4), round(max(0.0, c - h), 4), round(min(1.0, c + h), 4)]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--analysis', type=Path, required=True)
    ap.add_argument('--gates', type=Path, required=True)
    ap.add_argument('--index', type=Path, required=True)
    ap.add_argument('--first-audit', type=Path, help='first audit_analysis.json for Q4 replication')
    ap.add_argument('--output', type=Path, required=True)
    args = ap.parse_args()
    analysis = json.loads(args.analysis.read_text())
    gates = json.loads(args.gates.read_text())
    index = {c['id']: c for c in json.loads(args.index.read_text())['candidates']}
    stab = analysis['decision_stability']['admission_probability']
    cands = analysis['candidates']
    excluded = [c for c in index if c not in cands]

    rows = []
    for cid, c in cands.items():
        t, o = c['target'], c['old']
        rows.append({'id': cid, 'origin': index[cid]['origin'], 'overrides': index[cid]['overrides'],
                     'target_parent': t['parent_successes'], 'target_candidate': t['candidate_successes'],
                     'target_net': t['net_count'], 'old_gain': o['gained'], 'old_loss': o['lost'],
                     'old_net': o['net_count'], 'old_parent_successes': o['parent_successes'],
                     'conditional_loss': o['conditional_loss'],
                     'useful': c['useful'], 'gates': c['gate_decisions'],
                     'p_admit': stab[cid],
                     'p_disagree_agg_pres': round(stab[cid]['aggregate'] - stab[cid]['preservation'], 4)})

    def subset(origin):
        return [r for r in rows if origin == 'all' or r['origin'] == origin]

    summary = {}
    for origin in ('all', 'random'):
        rs = subset(origin)
        improving = [r for r in rs if r['target_net'] > 0]
        s = {'n_candidates': len(rs),
             'target_improving': len(improving),
             'Q1_improving_with_old_loss': wilson(sum(r['old_loss'] > 0 for r in improving), len(improving)),
             'Q2_with_both_gain_and_loss': sum(r['old_loss'] > 0 and r['old_gain'] > 0 for r in rs),
             'Q2_offsetting_gain_ge_loss_gt0': sum(r['old_loss'] > 0 and r['old_gain'] >= r['old_loss'] for r in rs),
             'Q2_committed_agg_pres_disagreements': sum(r['gates']['aggregate'] and not r['gates']['preservation'] for r in rs),
             'Q2_mean_resampled_disagreement': round(sum(r['p_disagree_agg_pres'] for r in rs) / len(rs), 4) if rs else None,
             'Q2_max_resampled_disagreement': max((r['p_disagree_agg_pres'] for r in rs), default=None),
             'useful_counts': {obj: sum(r['useful'][obj] for r in rs) for obj in OBJECTIVES},
             'gates': {}}
        for gate in GATES:
            adm = [r for r in rs if r['gates'][gate]]
            s['gates'][gate] = {
                'admitted': len(adm),
                'admitted_with_audit_losses': sum(r['old_loss'] > 0 for r in adm),
                'total_audit_losses_among_admitted': sum(r['old_loss'] for r in adm),
                'admitted_not_improving_target': sum(r['target_net'] <= 0 for r in adm),
                'admitted_useful': {obj: sum(r['useful'][obj] for r in adm) for obj in OBJECTIVES},
                'missed_useful': {obj: sum(r['useful'][obj] and not r['gates'][gate] for r in rs) for obj in OBJECTIVES},
                'mean_resampled_admission': round(sum(r['p_admit'][gate] for r in rs) / len(rs), 4) if rs else None}
        summary[origin] = s

    out = {'evidence': 'extension 1: seeded random proposal population + 2 assistant candidates; '
                       'designed after the first audit; one robot, task and repair context',
           'gate_decisions_committed_utc': gates['committed_utc'],
           'excluded_candidates': excluded, 'summary': summary,
           'delivered': {g: analysis['delivered'][g]['delivered'] for g in analysis['delivered']},
           'candidates': rows,
           'validation_parent_repeat_check': analysis.get('validation_parent_repeat_check')}
    if args.first_audit:
        first = json.loads(args.first_audit.read_text())['candidates']
        out['Q4_replication'] = {
            cid: {'first_audit': {'target': f"{first[cid]['target']['parent_successes']}->{first[cid]['target']['candidate_successes']}/{first[cid]['target']['n']}",
                                  'old_loss': first[cid]['old']['lost'], 'old_gain': first[cid]['old']['gained'],
                                  'conditional_loss': first[cid]['ci95']['old_conditional_loss']},
                  'extension': {'target': f"{cands[cid]['target']['parent_successes']}->{cands[cid]['target']['candidate_successes']}/{cands[cid]['target']['n']}",
                                'old_loss': cands[cid]['old']['lost'], 'old_gain': cands[cid]['old']['gained'],
                                'conditional_loss': cands[cid]['ci95']['old_conditional_loss']}}
            for cid in ('candidate_a', 'candidate_b') if cid in first and cid in cands}
    args.output.write_text(json.dumps(out, indent=2))
    print(json.dumps({k: out[k] for k in ('excluded_candidates', 'summary', 'delivered')}, indent=2))
    if 'Q4_replication' in out:
        print(json.dumps(out['Q4_replication'], indent=2))
    print('id            origin     tgt  gain loss  agg pres tonly  p(agg-pres)')
    for r in rows:
        g = r['gates']
        print(f"{r['id']:<13} {r['origin']:<9} {r['target_net']:+4d} {r['old_gain']:4d} {r['old_loss']:4d}  "
              f"{'A' if g['aggregate'] else '-':>3} {'A' if g['preservation'] else '-':>4} {'A' if g['target_only'] else '-':>5}  {r['p_disagree_agg_pres']:.3f}")


if __name__ == '__main__':
    main()
