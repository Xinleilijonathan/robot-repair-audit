"""Generate the extension-1 gate table from population_analysis.json and audit_analysis.json
(no hand transcription).

Usage: python make_population_table.py POPULATION_JSON EXT1_AUDIT_ANALYSIS_JSON OUT_DIR
Writes OUT_DIR/population_table.tex.
"""
import json
import sys
from pathlib import Path

pop = json.loads(Path(sys.argv[1]).read_text())
ana = json.loads(Path(sys.argv[2]).read_text())
out = Path(sys.argv[3])
s = pop['summary']['all']
n = s['n_candidates']
SHORT = {'candidate_a': 'A', 'candidate_b': 'B', 'parent': 'parent'}
nt, no = ana['n_target'], ana['n_old']

rows = []
for gate, label in (('target_only', 'Target-only'), ('aggregate', 'Aggregate'), ('preservation', 'Preservation')):
    g = s['gates'][gate]
    d = ana['delivered'][gate]
    rows.append(f"{label} & {g['admitted']} & {g['admitted_with_audit_losses']} & "
                f"{g['total_audit_losses_among_admitted']} & {g['admitted_useful']['aggregate_objective']} & "
                f"{g['missed_useful']['aggregate_objective']} & "
                f"{SHORT.get(d['delivered'], d['delivered'])} \\\\")
table = r"""\begin{table}[t]
\centering
\small
\setlength{\tabcolsep}{3.0pt}
\begin{tabular}{lcccccc}
\toprule
 & \multicolumn{3}{c}{Admitted} & \multicolumn{2}{c}{Agg.-useful} & \\
\cmidrule(lr){2-4}\cmidrule(lr){5-6}
Gate & /%d & w/ loss & losses & adm. & missed & Deliv. \\
\midrule
%s
\bottomrule
\end{tabular}
\caption{Post-hoc extension: committed gate decisions over %d candidates (A, B and 24 seeded random edits), scored on a fresh audit of %d target and %d old scenes. Losses are summed over admitted candidates. Under the aggregate objective %d candidates are useful; under the zero-loss objective, none.}
\label{tab:population}
\end{table}
""" % (n, '\n'.join(rows), n, nt, no, s['useful_counts']['aggregate_objective'])
(out / 'population_table.tex').write_text(table)
print(table)
