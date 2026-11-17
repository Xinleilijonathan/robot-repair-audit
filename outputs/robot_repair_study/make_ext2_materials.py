"""Extension 2 materials (extension2_protocol.md §2-§4). Refuses to overwrite.

1. Proposals: 24 NEW seeded random edits r25-r48 (seed 20261121), drawn with exactly the
   Extension 1 generator rules (make_random_proposals.py): k in {1, 2} parameters with equal
   probability, chosen uniformly without replacement, values uniform within the runner's bounds,
   rounded to 3 decimals. These candidates have never been run.
2. Suites, built ONLY from data recorded before Extension 2 (Extension 1 audit):
   - history suite: the old-scene parent successes of the Extension 1 audit panel, ranked by how
     many of the 26 Extension 1 candidates lost them; ties broken by a seeded random order
     (seed 20261122). The top 8 form the suite; its first 4 form the k=4 secondary suite.
   - uniform suite: 8 scenes drawn uniformly without replacement from the same parent successes
     (seed 20261123).
3. Validation (suite) manifest: Extension 1 validation targets vt01-vt04 plus the union of both
   suites, in one shuffled execution order (seed 20261124) shared by all configurations.
"""
import json
import random
from collections import Counter
from pathlib import Path

import numpy as np

STUDY = Path(__file__).resolve().parent
R1 = STUDY / 'results' / 'ext1'
PROP_SEED, TIE_SEED, UNI_SEED, ORDER_SEED = 20261121, 20261122, 20261123, 20261124
N, FIRST_ID, K = 24, 25, 8
BOUNDS = {  # identical to make_random_proposals.py / run_stock_scene.py allowed_overrides
    'approach_height': (0.05, 0.40),
    'lift_height': (0.10, 0.40),
    'position_tolerance': (0.005, 0.035),
    'grasp_position_tolerance': (0.005, 0.035),
    'stability_duration': (0.05, 0.50),
    'gripper_dwell': (0.10, 1.00),
}
STOCK = {'approach_height': 0.30, 'lift_height': 0.30, 'position_tolerance': 0.015,
         'grasp_position_tolerance': 0.015, 'stability_duration': 0.10, 'gripper_dwell': 0.20}
EXT1_IDS = ['candidate_a', 'candidate_b'] + [f'r{i:02d}' for i in range(1, 25)]


def load(folder):
    rows = {}
    for p in sorted(folder.glob('rollout_*.json')):
        r = json.loads(p.read_text())
        assert r['scene_id'] not in rows
        rows[r['scene_id']] = r
    return rows


def main():
    prop_dir = STUDY / 'proposals' / 'ext2'
    suites_path = STUDY / 'ext2_suites.json'
    manifest_path = STUDY / 'ext2_validation_scenes.json'
    for p in (prop_dir, suites_path, manifest_path):
        if p.exists():
            raise SystemExit(f'Refusing to overwrite frozen material {p}')

    # 1. proposals (same algorithm and call order as make_random_proposals.py, new seed and ids)
    rng = np.random.default_rng(PROP_SEED)
    names = list(BOUNDS)
    index = []
    configs = {}
    for i in range(FIRST_ID, FIRST_ID + N):
        k = int(rng.integers(1, 3))
        chosen = sorted(rng.choice(names, size=k, replace=False).tolist(), key=names.index)
        config = {p: round(float(rng.uniform(*BOUNDS[p])), 3) for p in chosen}
        for p, v in config.items():
            lo, hi = BOUNDS[p]
            config[p] = min(max(v, lo), hi)
        cid = f'r{i:02d}'
        configs[cid] = config
        index.append({'id': cid, 'origin': 'random', 'overrides': config})

    # 2. suites from the Extension 1 audit (recorded before Extension 2)
    audit = json.loads((STUDY / 'ext1_audit_scenes.json').read_text())
    by_id = {s['id']: s for s in audit}
    old = [s['id'] for s in audit if s['regime'] == 'old']
    parent = load(R1 / 'audit_parent')
    succ = sorted(s for s in old if parent[s]['object_state_success'])
    counts = Counter()
    for c in EXT1_IDS:
        rows = load(R1 / f'audit_{c}')
        counts.update(s for s in succ if not rows[s]['object_state_success'])
    tie = random.Random(TIE_SEED)
    tiebreak = {s: tie.random() for s in succ}
    ranked = sorted(succ, key=lambda s: (-counts.get(s, 0), tiebreak[s]))
    history = ranked[:K]
    uniform = sorted(random.Random(UNI_SEED).sample(succ, K))

    # 3. validation (suite) manifest
    vman = {s['id']: s for s in json.loads((STUDY / 'ext1_validation_scenes.json').read_text())}
    targets = [f'vt{i:02d}' for i in range(1, 5)]
    entries = []
    for sid in targets:
        e = dict(vman[sid])
        e.update({'split': 'ext2_validation', 'suite': ['target']})
        entries.append(e)
    for sid in sorted(set(history) | set(uniform)):
        e = dict(by_id[sid])
        e.update({'split': 'ext2_validation',
                  'suite': [x for x, members in (('history', history), ('uniform', uniform)) if sid in members]})
        entries.append(e)
    random.Random(ORDER_SEED).shuffle(entries)

    prop_dir.mkdir(parents=True)
    for cid, config in configs.items():
        (prop_dir / f'{cid}.json').write_text(json.dumps(config))
    (prop_dir / 'index.json').write_text(json.dumps({'seed': PROP_SEED, 'stock_values': STOCK, 'bounds': BOUNDS,
                                                     'candidates': index}, indent=1))
    suites = {'source': 'Extension 1 audit panel (ext1_audit_scenes.json), parent results/ext1/audit_parent, '
                        '26 Extension 1 candidate audits; all recorded before Extension 2',
              'parent_old_successes': succ,
              'loss_counts_ext1': {s: counts.get(s, 0) for s in ranked},
              'history_ranked': ranked,
              'history_suite': history,
              'history_suite_k4': history[:4],
              'uniform_suite': uniform,
              'target_ids': targets,
              'seeds': {'proposals': PROP_SEED, 'history_tiebreak': TIE_SEED, 'uniform': UNI_SEED,
                        'validation_order': ORDER_SEED}}
    suites_path.write_text(json.dumps(suites, indent=1))
    manifest_path.write_text(json.dumps(entries, indent=1))

    for row in index:
        print(row['id'], row['overrides'])
    print('parent old successes:', len(succ))
    print('history suite (ext1 loss counts):', [(s, counts.get(s, 0)) for s in history])
    print('uniform suite (ext1 loss counts):', [(s, counts.get(s, 0)) for s in uniform])
    print('overlap:', sorted(set(history) & set(uniform)))
    print('validation manifest:', len(entries), 'scenes, order:', [e['id'] for e in entries])


if __name__ == '__main__':
    main()
