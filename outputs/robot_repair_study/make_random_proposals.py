"""Extension 1 random proposal population (extension1_protocol.md §2). Seed 20261119.

A seeded, non-agent proposal distribution over the runner's bounded six-parameter interface:
k in {1, 2} parameters (equal probability), chosen uniformly without replacement, each value
uniform within the runner's bounds, rounded to 3 decimals. Refuses to overwrite.
"""
import json
from pathlib import Path

import numpy as np

SEED = 20261119
N = 24
BOUNDS = {  # must match allowed_overrides in run_stock_scene.py
    'approach_height': (0.05, 0.40),
    'lift_height': (0.10, 0.40),
    'position_tolerance': (0.005, 0.035),
    'grasp_position_tolerance': (0.005, 0.035),
    'stability_duration': (0.05, 0.50),
    'gripper_dwell': (0.10, 1.00),
}
STOCK = {'approach_height': 0.30, 'lift_height': 0.30, 'position_tolerance': 0.015,
         'grasp_position_tolerance': 0.015, 'stability_duration': 0.10, 'gripper_dwell': 0.20}

out = Path(__file__).parent / 'proposals' / 'ext1'
if out.exists():
    raise SystemExit(f'Refusing to overwrite frozen proposals {out}')
out.mkdir(parents=True)
rng = np.random.default_rng(SEED)
names = list(BOUNDS)
index = []
for i in range(1, N + 1):
    k = int(rng.integers(1, 3))
    chosen = sorted(rng.choice(names, size=k, replace=False).tolist(), key=names.index)
    config = {p: round(float(rng.uniform(*BOUNDS[p])), 3) for p in chosen}
    for p, v in config.items():  # rounding must not leave the runner's bounds
        lo, hi = BOUNDS[p]
        config[p] = min(max(v, lo), hi)
    cid = f'r{i:02d}'
    (out / f'{cid}.json').write_text(json.dumps(config))
    index.append({'id': cid, 'origin': 'random', 'overrides': config})
index = [{'id': 'candidate_a', 'origin': 'assistant', 'overrides': {'lift_height': 0.20}},
         {'id': 'candidate_b', 'origin': 'assistant', 'overrides': {'position_tolerance': 0.025}}] + index
(out / 'index.json').write_text(json.dumps({'seed': SEED, 'stock_values': STOCK, 'bounds': BOUNDS,
                                            'candidates': index}, indent=1))
for row in index:
    print(row['id'], row['origin'], row['overrides'])
