"""Figure (extension 1, secondary/descriptive): each candidate's audit target change and old gains
against its old losses, marked by the strictest committed gate that admitted it.

Reads population_analysis.json only (no new per-scene quantities). Admission sets are nested here
(preservation within aggregate within target-only), so the encoding is an ordinal one-hue ramp
(blue steps 250/450/650 of the documented sequential ramp; the lightest clears 2:1 on white) with
a hollow gray marker for candidates no gate admitted. Ink stays in text tokens.
"""
import argparse
import json
from collections import Counter
from pathlib import Path

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D

INK, INK2, GRID, NONE = '#0b0b0b', '#52514e', '#e1e0d9', '#898781'
LEVELS = [('none', 'no gate', None),
          ('target_only', 'target-only', '#86b6ef'),
          ('aggregate', '+ aggregate', '#2a78d6'),
          ('preservation', '+ preservation', '#104281')]
LABEL = {'candidate_a': 'A', 'candidate_b': 'B'}
SHOW = {'candidate_a', 'candidate_b', 'r04', 'r14', 'r24'}


def level(gates):
    lv = 'none'
    for key, _, _ in LEVELS[1:]:
        if gates[key]:
            lv = key
    return lv


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--population', type=Path, required=True)
    ap.add_argument('--output', type=Path, nargs='+', required=True)
    args = ap.parse_args()
    rows = json.loads(args.population.read_text())['candidates']
    plt.rcParams.update({'font.family': 'sans-serif', 'font.size': 7, 'axes.edgecolor': '#c3c2b7',
                         'axes.linewidth': 0.6, 'xtick.color': INK2, 'ytick.color': INK2,
                         'xtick.major.width': 0.6, 'ytick.major.width': 0.6, 'pdf.fonttype': 42})
    fig, axes = plt.subplots(1, 2, figsize=(3.3, 2.0), sharey=True, layout='constrained',
                             gridspec_kw={'width_ratios': [1.35, 1]})
    panels = ((axes[0], 'target_net', 'audit target change (/30)'),
              (axes[1], 'old_gain', 'old gains'))
    for ax, xkey, xlabel in panels:
        ax.grid(True, color=GRID, linewidth=0.4)
        ax.set_axisbelow(True)
        dup = Counter((r[xkey], r['old_loss']) for r in rows)
        for key, _, color in LEVELS:
            pts = [(r[xkey], r['old_loss']) for r in rows if level(r['gates']) == key]
            if not pts:
                continue
            xs, ys = zip(*pts)
            if color is None:
                ax.scatter(xs, ys, s=16, facecolors='white', edgecolors=NONE, linewidths=0.7, zorder=2)
            else:
                ax.scatter(xs, ys, s=22, color=color, edgecolors='white', linewidths=0.5, zorder=3)
        for (x, y), n in dup.items():
            if n > 1:
                below = xkey == 'old_gain' and y > 0
                ax.annotate(f'×{n}', (x, y), xytext=(0, -4) if below else (4, -1), textcoords='offset points',
                            fontsize=5.5, color=INK2, va='top' if below else 'center',
                            ha='center' if below else 'left')
        for r in rows:
            show = SHOW if xkey == 'target_net' else {'r14'}
            if r['id'] in show:
                name = LABEL.get(r['id'], r['id'])
                off = {'candidate_a': (4, 1), 'r24': (4, -3), 'r14': (-4, -2),
                       'candidate_b': (-2, 4), 'r04': (2, 4)}[r['id']]
                ax.annotate(name, (r[xkey], r['old_loss']), xytext=off, textcoords='offset points',
                            fontsize=6, color=INK, ha='left' if off[0] >= 0 else 'right', va='center')
        ax.set_xlabel(xlabel, color=INK2)
        for side in ('top', 'right'):
            ax.spines[side].set_visible(False)
    a, b = axes
    a.axvline(0, color='#c3c2b7', linewidth=0.6, zorder=1)
    a.set_xticks([-10, 0, 10, 20])
    a.set_xlim(-12, 22)
    a.set_ylim(-1.2, 17.5)
    a.set_ylabel('old losses (/73)', color=INK2)
    b.plot([0, 17], [0, 17], color=INK2, linewidth=0.6, linestyle=(0, (3, 2)), zorder=1)
    b.text(11.8, 0.4, 'gains > losses', fontsize=5.5, color=INK2, ha='right')
    b.text(0.3, 12.0, 'losses >\ngains', fontsize=5.5, color=INK2, ha='left', linespacing=0.95)
    b.set_xlim(-0.8, 12)
    b.set_xticks([0, 5, 10])
    handles = [Line2D([], [], linestyle='', marker='o', markersize=4, markerfacecolor='white',
                      markeredgecolor=NONE, markeredgewidth=0.7, label=LEVELS[0][1])]
    handles += [Line2D([], [], linestyle='', marker='o', markersize=4.5, color=c, label=lab)
                for _, lab, c in LEVELS[1:]]
    fig.legend(handles=handles, loc='outside lower center', ncol=4, frameon=False, fontsize=6.3,
               handletextpad=0.15, columnspacing=0.8, title='strictest committed gate that admitted',
               title_fontsize=6.3)
    for out in args.output:
        fig.savefig(out, dpi=300, facecolor='white')
    plt.close(fig)


if __name__ == '__main__':
    main()
