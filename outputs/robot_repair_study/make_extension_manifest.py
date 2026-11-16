"""Extension 1 scene manifests (extension1_protocol.md §3). Seed 20261118. Refuses to overwrite.

Same populations as make_audit_manifest.py; different seed and audit sizes (30 target / 90 old).
"""
import json
import math
from pathlib import Path

import numpy as np

SEED = 20261118
PLACE = [0.0, 0.5, 0.0258]
Z = 0.0258
TARGET_R, TARGET_A = (0.79, 0.81), (-62.0, -58.0)
WORKSPACE_R, WORKSPACE_A = (0.35, 0.85), (-60.0, 60.0)
EXCLUDE_R, EXCLUDE_A = (0.77, 0.83), (-64.0, -56.0)
COUNTS = {'vt': 12, 'vo': 8, 'at': 30, 'ao': 90}

here = Path(__file__).parent
out_validation = here / 'ext1_validation_scenes.json'
out_audit = here / 'ext1_audit_scenes.json'
for path in (out_validation, out_audit):
    if path.exists():
        raise SystemExit(f'Refusing to overwrite frozen manifest {path}')
rng = np.random.default_rng(SEED)


def scene(scene_id, split, regime, r, a):
    rad = math.radians(a)
    return {'id': scene_id, 'split': split, 'regime': regime,
            'radius_m': round(float(r), 5), 'angle_deg': round(float(a), 4),
            'pick': [round(r * math.cos(rad), 7), round(r * math.sin(rad), 7), Z], 'place': PLACE}


def draw_target():
    return rng.uniform(*TARGET_R), rng.uniform(*TARGET_A)


def draw_old():
    while True:
        r, a = rng.uniform(*WORKSPACE_R), rng.uniform(*WORKSPACE_A)
        if not (EXCLUDE_R[0] <= r <= EXCLUDE_R[1] and EXCLUDE_A[0] <= a <= EXCLUDE_A[1]):
            return r, a


groups = {}
for prefix, n in COUNTS.items():
    split = 'validation' if prefix[0] == 'v' else 'audit'
    regime = 'target' if prefix[1] == 't' else 'old'
    width = 2 if split == 'validation' else 3
    groups[prefix] = [scene(f'{prefix}{i + 1:0{width}d}', split, regime,
                            *(draw_target() if regime == 'target' else draw_old())) for i in range(n)]
validation = groups['vt'] + groups['vo']
audit = groups['at'] + groups['ao']
validation = [validation[i] for i in rng.permutation(len(validation))]
audit = [audit[i] for i in rng.permutation(len(audit))]
out_validation.write_text(json.dumps(validation, indent=1))
out_audit.write_text(json.dumps(audit, indent=1))
print(f'validation: {len(validation)} scenes; audit: {len(audit)} scenes (seed {SEED})')
