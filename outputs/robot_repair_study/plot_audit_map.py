"""Figure: where each candidate gains and loses on the frozen audit, in pick (angle, radius).

Colors follow the documented diverging poles (gain = blue #2a78d6, loss = red #e34948) with
unchanged scenes in recessive grays; marker shape is a redundant cue (triangle = gain,
X = loss). Pairwise CVD/normal-vision OKLab separation and contrast were checked numerically
(worst CVD dE 8.7, normal dE >= 17.8, contrast >= 3.6:1 on white).
"""
import argparse
import json
from pathlib import Path

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
from matplotlib.patches import Rectangle

GAIN, LOSS = '#2a78d6', '#e34948'
KEEP_OK, KEEP_FAIL = '#c3c2b7', '#898781'
INK, INK2, GRID = '#0b0b0b', '#52514e', '#e1e0d9'


def load(folder):
    rows = {}
    for path in sorted(Path(folder).glob('rollout_*.json')):
        r = json.loads(path.read_text())
        rows[r['scene_id']] = bool(r['object_state_success'])
    return rows


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--manifest', type=Path, required=True)
    ap.add_argument('--parent', type=Path, required=True)
    ap.add_argument('--candidates', type=Path, nargs=2, required=True)
    ap.add_argument('--labels', nargs=2, default=['A (lift 0.20 m)', 'B (tolerance 0.025 m)'])
    ap.add_argument('--output', type=Path, nargs='+', required=True)
    args = ap.parse_args()
    manifest = json.loads(args.manifest.read_text())
    parent = load(args.parent)
    plt.rcParams.update({'font.family': 'sans-serif', 'font.size': 7, 'axes.edgecolor': '#c3c2b7',
                         'axes.linewidth': 0.6, 'xtick.color': INK2, 'ytick.color': INK2,
                         'xtick.major.width': 0.6, 'ytick.major.width': 0.6, 'pdf.fonttype': 42})
    fig, axes = plt.subplots(1, 2, figsize=(3.3, 2.05), sharey=True, layout='constrained')
    for ax, folder, label in zip(axes, args.candidates, args.labels):
        cand = load(folder)
        groups = {'keep_ok': [], 'keep_fail': [], 'gain': [], 'loss': []}
        counts = {'tg': 0, 'tp': 0, 'gain': 0, 'loss': 0, 'nt': 0}
        for s in manifest:
            a, b = parent[s['id']], cand[s['id']]
            kind = 'keep_ok' if a and b else 'keep_fail' if not a and not b else 'gain' if b else 'loss'
            groups[kind].append((s['angle_deg'], s['radius_m']))
            if s['regime'] == 'target':
                counts['nt'] += 1; counts['tp'] += a; counts['tg'] += b
            else:
                counts[kind] = counts.get(kind, 0) + (kind in ('gain', 'loss'))
        ax.grid(True, color=GRID, linewidth=0.4)
        ax.set_axisbelow(True)
        ax.add_patch(Rectangle((-62, 0.79), 4, 0.02, fill=False, edgecolor=INK2, linewidth=0.6, zorder=1))
        ax.annotate('target', (-60, 0.81), xytext=(-48, 0.875), fontsize=6.5, color=INK2,
                    arrowprops=dict(arrowstyle='-', color=INK2, linewidth=0.5))
        style = {'keep_ok': dict(marker='o', s=7, color=KEEP_OK, linewidths=0),
                 'keep_fail': dict(marker='o', s=9, facecolors='none', edgecolors=KEEP_FAIL, linewidths=0.5),
                 'gain': dict(marker='^', s=22, color=GAIN, edgecolors='white', linewidths=0.4),
                 'loss': dict(marker='X', s=30, color=LOSS, edgecolors='white', linewidths=0.4)}
        for kind in ('keep_ok', 'keep_fail', 'gain', 'loss'):
            if groups[kind]:
                xs, ys = zip(*groups[kind])
                ax.scatter(xs, ys, zorder=3 if kind in ('gain', 'loss') else 2, **style[kind])
        ax.set_title(label, fontsize=7, color=INK, pad=11)
        ax.text(0.5, 1.015, f"target {counts['tp']}→{counts['tg']}/{counts['nt']}, "
                f"old +{counts['gain']}/−{counts['loss']}", transform=ax.transAxes,
                ha='center', va='bottom', fontsize=6, color=INK2)
        ax.set_xlim(-66, 64)
        ax.set_ylim(0.33, 0.90)
        ax.set_xticks([-60, -30, 0, 30, 60])
        ax.set_xlabel('pick angle (deg)', color=INK2)
        for side in ('top', 'right'):
            ax.spines[side].set_visible(False)
    axes[0].set_ylabel('pick radius (m)', color=INK2)
    handles = [Line2D([], [], linestyle='', marker='^', markersize=5, color=GAIN, label='gain'),
               Line2D([], [], linestyle='', marker='X', markersize=5.5, color=LOSS, label='loss'),
               Line2D([], [], linestyle='', marker='o', markersize=3, color=KEEP_OK, label='both succeed'),
               Line2D([], [], linestyle='', marker='o', markersize=3.5, markerfacecolor='none',
                      markeredgecolor=KEEP_FAIL, markeredgewidth=0.6, label='both fail')]
    fig.legend(handles=handles, loc='outside lower center', ncol=4, frameon=False, fontsize=6.5,
               handletextpad=0.2, columnspacing=0.9)
    for out in args.output:
        fig.savefig(out, dpi=300, facecolor='white')
    plt.close(fig)


if __name__ == '__main__':
    main()
