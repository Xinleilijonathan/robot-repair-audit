"""Generate the frozen single-context audit manifests (see audit_protocol.md).

Deterministic: seed 20261115. Refuses to overwrite existing manifests.
Pick positions are planar (x = r cos a, y = r sin a, z = 0.0258); place is fixed.
"""
import json
import math
from pathlib import Path

import numpy as np

SEED = 20261115
PLACE = [0.0, 0.5, 0.0258]
Z = 0.0258
TARGET_R, TARGET_A = (0.79, 0.81), (-62.0, -58.0)      # neighbourhood of r80_a-60
WORKSPACE_R, WORKSPACE_A = (0.35, 0.85), (-60.0, 60.0)  # development panel's bounding region
EXCLUDE_R, EXCLUDE_A = (0.77, 0.83), (-64.0, -56.0)     # keeps old draws away from the target
COUNTS = {'vt': 12, 'vo': 8, 'at': 40, 'ao': 120}

here = Path(__file__).parent
out_validation = here / 'audit_validation_scenes.json'
out_audit = here / 'audit_scenes.json'
for path in (out_validation, out_audit):
    if path.exists():
        raise SystemExit(f'Refusing to overwrite frozen manifest {path}')

rng = np.random.default_rng(SEED)


def scene(scene_id, split, regime, r, a):
    rad = math.radians(a)
    return {'id': scene_id, 'split': split, 'regime': regime,
            'radius_m': round(float(r), 5), 'angle_deg': round(float(a), 4),
            'pick': [round(r * math.cos(rad), 7), round(r * math.sin(rad), 7), Z],
            'place': PLACE}


def draw_target():
    return rng.uniform(*TARGET_R), rng.uniform(*TARGET_A)


def draw_old():
    while True:
        r, a = rng.uniform(*WORKSPACE_R), rng.uniform(*WORKSPACE_A)
        if not (EXCLUDE_R[0] <= r <= EXCLUDE_R[1] and EXCLUDE_A[0] <= a <= EXCLUDE_A[1]):
            return r, a


groups = {}
for prefix, n in COUNTS.items():  # fixed draw order: vt, vo, at, ao
    split = 'validation' if prefix[0] == 'v' else 'audit'
    regime = 'target' if prefix[1] == 't' else 'old'
    width = 2 if split == 'validation' else 3
    groups[prefix] = [scene(f'{prefix}{i + 1:0{width}d}', split, regime,
                            *(draw_target() if regime == 'target' else draw_old()))
                      for i in range(n)]

validation = groups['vt'] + groups['vo']
audit = groups['at'] + groups['ao']
# One fixed shuffled execution order per manifest, shared by every configuration.
validation = [validation[i] for i in rng.permutation(len(validation))]
audit = [audit[i] for i in rng.permutation(len(audit))]
out_validation.write_text(json.dumps(validation, indent=1))
out_audit.write_text(json.dumps(audit, indent=1))
print(f'validation: {len(validation)} scenes; audit: {len(audit)} scenes (seed {SEED})')
