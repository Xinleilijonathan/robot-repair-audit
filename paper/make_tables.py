"""Generate LaTeX tables for the paper directly from analysis outputs (no hand transcription).

Usage: python make_tables.py ANALYSIS_JSON GATES_JSON OUT_DIR
Writes OUT_DIR/audit_table.tex and OUT_DIR/gate_table.tex.
"""
import json
import sys
from pathlib import Path

analysis = json.loads(Path(sys.argv[1]).read_text())
gates = json.loads(Path(sys.argv[2]).read_text())
out = Path(sys.argv[3])
NAMES = {'candidate_a': 'A: lift 0.20\\,m', 'candidate_b': 'B: tol.\\ 0.025\\,m'}
SHORT = {'candidate_a': 'A', 'candidate_b': 'B', 'parent': 'parent'}


def pct(ci):
    if ci is None:
        return '--'
    p, lo, hi = ci
    return f'{100 * p:.1f} [{100 * lo:.1f}, {100 * hi:.1f}]'


nt, no = analysis['n_target'], analysis['n_old']
cands = analysis['candidates']
first = next(iter(cands.values()))
rows = [f"Parent & {first['target']['parent_successes']} & {first['old']['parent_successes']} & -- & -- & -- & -- \\\\"]
for key, c in cands.items():
    u = c['useful']
    rows.append(f"{NAMES.get(key, key)} & {c['target']['candidate_successes']} & {c['old']['candidate_successes']} & "
                f"{c['old']['gained']} & {c['old']['lost']} & {pct(c['ci95']['old_conditional_loss'])} & "
                f"{'yes' if u['aggregate_objective'] else 'no'}/{'yes' if u['preservation_objective'] else 'no'} \\\\")
audit_table = r"""\begin{table}[t]
\centering
\small
\setlength{\tabcolsep}{1.9pt}
\begin{tabular}{lcccccc}
\toprule
 & Target & Old & \multicolumn{2}{c}{Old} & Cond.\ loss, \%% & Useful \\
\cmidrule(lr){4-5}
 & /%d & /%d & gain & loss & [95\%% CI] & agg./pres. \\
\midrule
%s
\bottomrule
\end{tabular}
\caption{Frozen audit: %d target and %d old scenes, one reset each, paired against the parent. Conditional loss is losses divided by parent old successes, with a Wilson interval over scenes for this single context. Usefulness follows the objectives declared before the audit.}
\label{tab:audit}
\end{table}
""" % (nt, no, '\n'.join(rows), nt, no)

stab = analysis['decision_stability']['admission_probability']
grow = []
for gate, label in (('frozen', 'Frozen'), ('target_only', 'Target-only'), ('aggregate', 'Aggregate'),
                    ('preservation', 'Preservation')):
    d = analysis['delivered'][gate]
    dec = ' & '.join('--' if gate == 'frozen' else ('admit' if gates['candidates'][k][gate] else 'reject')
                     for k in cands)
    pa = ' & '.join('--' if gate == 'frozen' else f"{stab[k][gate]:.2f}" for k in cands)
    grow.append(f"{label} & {dec} & {SHORT.get(d['delivered'], d['delivered'])} & "
                f"{round(d['target_success'][0] * nt)} & {round(d['old_success'][0] * no)} & {d['old_losses']} & "
                f"{pa} \\\\")
gate_table = r"""\begin{table}[t]
\centering
\small
\setlength{\tabcolsep}{2.6pt}
\begin{tabular}{lcccccccc}
\toprule
 & \multicolumn{2}{c}{Committed} & & \multicolumn{3}{c}{Delivered (audit)} & \multicolumn{2}{c}{P(admit)} \\
\cmidrule(lr){2-3}\cmidrule(lr){5-7}\cmidrule(lr){8-9}
Gate & A & B & Deliv. & Tgt & Old & Loss & A & B \\
\midrule
%s
\bottomrule
\end{tabular}
\caption{Gate decisions committed from the 24-rollout validation draw before the audit ran, and the delivered controller's audit outcomes (target /%d, old /%d). P(admit) is a diagnostic: the admission rate over %s validation-sized draws resampled from the audit pools.}
\label{tab:gates}
\end{table}
""" % ('\n'.join(grow), nt, no, f"{analysis['decision_stability']['draws']:,}".replace(',', '{,}'))
(out / 'audit_table.tex').write_text(audit_table)
(out / 'gate_table.tex').write_text(gate_table)
print(audit_table)
print(gate_table)
