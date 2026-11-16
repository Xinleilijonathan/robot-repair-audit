"""Generate a descriptive scientific figure from completed pilot comparisons."""
import argparse
import json
from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np

parser = argparse.ArgumentParser()
parser.add_argument('summary', type=Path)
parser.add_argument('output', type=Path)
args = parser.parse_args()
data = json.loads(args.summary.read_text())
comparisons = data['comparisons']
names = list(comparisons)
scenes = list(comparisons[names[0]]['scenes'])
first = comparisons[names[0]]['scenes']
matrix = [[first[s]['parent_successes']/first[s]['n'] for s in scenes]]
matrix += [[v['scenes'][s]['candidate_successes']/v['scenes'][s]['n'] for s in scenes] for v in comparisons.values()]
fig, ax = plt.subplots(figsize=(12, 3.8), layout='constrained')
im = ax.imshow(np.asarray(matrix), vmin=0, vmax=1, cmap='Blues', aspect='auto')
ax.set_xticks(range(len(scenes)), [s.replace('_', '\n') for s in scenes], fontsize=9)
ax.set_yticks(range(len(matrix)), ['Parent (discovery)'] + [s.replace('radial_', '').replace('_', ' ') for s in names], fontsize=10)
for i, row in enumerate(matrix):
    for j, v in enumerate(row):
        ax.text(j, i, f'{round(v*3)}/3', ha='center', va='center', color='white' if v > 0.6 else 'black', fontsize=9)
ax.set_title('Exploratory robot repair: successes across three resets per scene', pad=15)
fig.colorbar(im, ax=ax, label='Success fraction', shrink=0.8)
fig.savefig(args.output, dpi=180, facecolor='white')
plt.close(fig)
