"""Generate the combined gate table for both candidate populations (no hand transcription).

Rows: the post-hoc population (Extension 1; population_analysis.json) and the pre-registered test
(Extension 2; ext2_analysis.json). Columns: admitted, admitted with audit losses, total audit
losses among admitted, aggregate-useful admitted and missed.

Usage: python make_combined_gate_table.py POPULATION_JSON EXT2_ANALYSIS_JSON OUT_DIR
Writes OUT_DIR/combined_gate_table.tex.
"""
import json
import sys
from pathlib import Path

pop = json.loads(Path(sys.argv[1]).read_text())
e2 = json.loads(Path(sys.argv[2]).read_text())
out = Path(sys.argv[3])

s1 = pop['summary']['all']
n1 = s1['n_candidates']
n2 = e2['n_candidates']
u1 = sum(r['useful']['aggregate_objective'] for r in pop['candidates'])
u2 = e2['useful_counts']['aggregate_objective']
assert sum(r['useful']['preservation_objective'] for r in pop['candidates']) == 0
assert e2['useful_counts']['preservation_objective'] == 0


def row(label, g):
    return (f"{label} & {g['admitted']} & {g['admitted_with_audit_losses']} & "
            f"{g['total_audit_losses_among_admitted']} & {g['admitted_useful']['aggregate_objective']} & "
            f"{g['missed_useful']['aggregate_objective']} \\\\")


rows1 = [row(lab, s1['gates'][k]) for k, lab in
         (('target_only', 'Target-only'), ('aggregate', 'Aggregate'), ('preservation', 'Preservation'))]
rows2 = [row(lab, e2['S_admission'][k]) for k, lab in
         (('target_gate', 'Target-only'), ('uniform_gate', 'Uniform suite, 8'),
          ('history4_gate', 'History suite, 4'), ('history_gate', 'History suite, 8'))]

table = r"""\begin{table}[t]
\centering
\small
\setlength{\tabcolsep}{3.0pt}
\begin{tabular}{lccccc}
\toprule
 & \multicolumn{3}{c}{Admitted} & \multicolumn{2}{c}{Agg.-useful} \\
\cmidrule(lr){2-4}\cmidrule(lr){5-6}
Gate & no. & w/ loss & losses & adm. & missed \\
\midrule
\multicolumn{6}{l}{\emph{Post-hoc population: %d candidates, %d agg.-useful}} \\
%s
\midrule
\multicolumn{6}{l}{\emph{Pre-registered test: %d new edits, %d agg.-useful}} \\
%s
\bottomrule
\end{tabular}
\caption{Committed gate decisions in the two candidate populations, scored on each population's audit (30 target and 90 old scenes; the parent solves 73 old scenes in both). Losses are summed over admitted candidates. No candidate in either population is useful under the zero-loss objective. Suite gates spend 4 target and $k$ old pairs and admit only with a target gain and zero suite losses.}
\label{tab:gates2}
\end{table}
""" % (n1, u1, '\n'.join(rows1), n2, u2, '\n'.join(rows2))
(out / 'combined_gate_table.tex').write_text(table)
print(table)
