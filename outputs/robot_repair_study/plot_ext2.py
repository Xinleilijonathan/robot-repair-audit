"""Figure (Extension 2): loss histories as regression suites.

Top: new (Extension 2) losses per old scene, scenes ordered by the frozen Extension 1 loss ranking;
the first eight form the pre-registered history suite. Bottom: the pre-registered primary and k = 4
comparisons as a dumbbell: share of lossy new edits in which the history suite detected a loss
(suite batch; Wilson 95% interval) against the hypergeometric expectation for a uniform suite.

Reads ext2_analysis.json (frozen analysis) and ext2_scenes.json (descriptive per-scene counts).
Drawn with matplotlib from data only. Colors: blue 450 for the history suite, neutral grays for
everything else; ink in text tokens.
"""
import argparse
import json
import math
from pathlib import Path

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Patch

INK, INK2, GRID, AXIS = '#0b0b0b', '#52514e', '#e1e0d9', '#c3c2b7'
BLUE, UNI, OTHER = '#2a78d6', '#898781', '#d3d2cb'


def wilson(k, n, z=1.959964):
    p = k / n
    d = 1 + z * z / n
    c = (p + z * z / (2 * n)) / d
    h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return c - h, c + h


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--analysis', type=Path, required=True)
    ap.add_argument('--scenes', type=Path, required=True)
    ap.add_argument('--suites', type=Path, required=True)
    ap.add_argument('--output', type=Path, nargs='+', required=True)
    args = ap.parse_args()
    a = json.loads(args.analysis.read_text())
    sc = json.loads(args.scenes.read_text())
    ranked = json.loads(args.suites.read_text())['history_ranked']
    per = {r['scene']: r for r in sc['per_scene']}
    assert set(per) == set(ranked)

    plt.rcParams.update({'font.family': 'sans-serif', 'font.size': 7, 'axes.edgecolor': AXIS,
                         'axes.linewidth': 0.6, 'xtick.color': INK2, 'ytick.color': INK2,
                         'xtick.major.width': 0.6, 'ytick.major.width': 0.6, 'pdf.fonttype': 42})
    fig, (top, bot) = plt.subplots(2, 1, figsize=(3.3, 2.55), layout='constrained',
                                   gridspec_kw={'height_ratios': [1.45, 1]})

    # --- top: per-scene new losses in frozen history order
    xs = range(len(ranked))
    ys = [per[s]['ext2_losses'] for s in ranked]
    cols = [BLUE if per[s]['history_suite'] else UNI if per[s]['uniform_suite'] else OTHER for s in ranked]
    top.bar(xs, ys, width=0.78, color=cols, linewidth=0, zorder=2)
    top.grid(True, axis='y', color=GRID, linewidth=0.4)
    top.set_axisbelow(True)
    top.set_xlim(-1, len(ranked))
    top.set_ylim(0, max(ys) + 1.9)
    top.set_xticks([0, 7, 19, 39, 59, 72], ['1', '8', '20', '40', '60', '73'])
    top.set_xlabel('old scenes, ranked by losses to the 26 Extension 1 edits', color=INK2)
    top.set_ylabel('losses to 24\nnew edits', color=INK2)
    s3 = a['S3_concentration']
    yb = max(ys[:8]) + 0.7
    top.plot([-0.4, 7.4], [yb, yb], color=INK2, linewidth=0.6)
    for e in (-0.4, 7.4):
        top.plot([e, e], [yb - 0.35, yb], color=INK2, linewidth=0.6)
    top.text(8.4, yb, f"{s3['on_history_suite']} of {s3['total_losses']} new losses\n"
             f"fall on these 8 scenes", fontsize=6, color=INK, va='center', ha='left', linespacing=0.95)
    top.legend(handles=[Patch(color=BLUE, label='history suite'), Patch(color=UNI, label='uniform suite'),
                        Patch(color=OTHER, label='other')],
               loc='upper right', frameon=False, fontsize=6, handlelength=0.9, handletextpad=0.35,
               borderaxespad=0.1)

    # --- bottom: dumbbell of detection rates
    n = a['n_lossy']
    rows = [('8 old scenes', a['P1_primary']['history8_batch_detect_rate'],
             a['P1_primary']['uniform8_expected_detect_rate'], a['P1_primary']['difference_mean_ci95']),
            ('4 old scenes', a['S2_k4']['history4_batch_detect_rate'],
             a['S2_k4']['uniform4_expected_detect_rate'], a['S2_k4']['difference_mean_ci95'])]
    for i, (lab, h, u, d) in enumerate(rows):
        y = len(rows) - 1 - i
        lo, hi = wilson(round(h * n), n)
        bot.plot([u, h], [y, y], color=AXIS, linewidth=1.2, zorder=1)
        bot.plot([lo, hi], [y, y], color=BLUE, linewidth=0.9, zorder=2, solid_capstyle='butt')
        for e in (lo, hi):
            bot.plot([e, e], [y - 0.09, y + 0.09], color=BLUE, linewidth=0.9, zorder=2)
        bot.scatter([u], [y], s=26, facecolors='white', edgecolors=UNI, linewidths=0.9, zorder=3)
        bot.scatter([h], [y], s=30, color=BLUE, edgecolors='white', linewidths=0.6, zorder=4)
        bot.text(1.03, y, f'{d[0]:+.2f}\n[{d[1]:.2f}, {d[2]:.2f}]', fontsize=5.8, color=INK, va='center',
                 ha='left', linespacing=0.95, transform=bot.get_yaxis_transform())
    bot.text(1.03, len(rows) - 0.42, 'diff. (95% CI)', fontsize=5.8, color=INK2, va='bottom', ha='left',
             transform=bot.get_yaxis_transform())
    bot.set_yticks(range(len(rows)), [r[0] for r in rows][::-1])
    bot.set_ylim(-0.6, len(rows) - 0.4)
    bot.set_xlim(0, 1)
    bot.set_xticks([0, 0.25, 0.5, 0.75, 1.0], ['0', '.25', '.5', '.75', '1'])
    bot.grid(True, axis='x', color=GRID, linewidth=0.4)
    bot.set_axisbelow(True)
    bot.tick_params(axis='y', length=0)
    bot.set_xlabel(f'share of the {n} lossy new edits whose losses the suite detects', color=INK2)
    hist_h = plt.Line2D([], [], linestyle='', marker='o', markersize=4.6, color=BLUE, label='history (observed)')
    uni_h = plt.Line2D([], [], linestyle='', marker='o', markersize=4.2, markerfacecolor='white',
                       markeredgecolor=UNI, markeredgewidth=0.9, label='uniform (expected)')
    bot.legend(handles=[hist_h, uni_h], loc='lower left', bbox_to_anchor=(-0.3, 1.0), ncol=2, frameon=False,
               fontsize=6, handletextpad=0.2, columnspacing=1.0, borderaxespad=0.1)
    for ax in (top, bot):
        for side in ('top', 'right'):
            ax.spines[side].set_visible(False)
    bot.spines['left'].set_visible(False)
    for out in args.output:
        fig.savefig(out, dpi=300, facecolor='white')
    plt.close(fig)


if __name__ == '__main__':
    main()
