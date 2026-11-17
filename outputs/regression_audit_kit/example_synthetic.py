"""End-to-end demo of regaudit on SYNTHETIC data (no simulator needed).

*** SYNTHETIC DEMO DATA - NOT ROBOT RESULTS. ***
A toy world: old scenes have a latent fragility; each random edit has a latent 'disruptiveness';
an edit breaks a parent success with probability disruptiveness x fragility. Replace `run()` with
your own simulator or test harness to audit a real skill.
"""
import random

import regaudit as ra

SEED = 7
rng = random.Random(SEED)
OLD = [f'old{i:03d}' for i in range(90)]
TARGET = [f'tgt{i:02d}' for i in range(12)]
fragility = {s: rng.betavariate(0.5, 4.0) for s in OLD}
parent_ok = {s: int(rng.random() < 0.8) for s in OLD} | {s: int(rng.random() < 0.3) for s in TARGET}
BOUNDS = {'approach_height': (0.05, 0.40), 'lift_height': (0.10, 0.40), 'position_tolerance': (0.005, 0.035)}


def run(edit, label):
    """SYNTHETIC stand-in for a simulator run of one configuration over all scenes."""
    if not edit:
        return dict(parent_ok)
    r = random.Random(f'{label}|{sorted(edit.items())}')
    disrupt, skill = r.random(), r.random()
    out = {}
    for s in OLD:
        if parent_ok[s]:
            out[s] = int(r.random() >= min(1.0, 3 * disrupt * fragility[s]))
        else:
            out[s] = int(r.random() < 0.3 * disrupt)
    for s in TARGET:
        out[s] = parent_ok[s] or int(r.random() < 0.6 * skill)
    return out


print('*** SYNTHETIC DEMO DATA - NOT ROBOT RESULTS ***')
parent = run({}, 'parent')
print('1. replay check:', ra.replay_check(parent, run({}, 'parent')))

past = ra.null_population(BOUNDS, 26, seed=1)
new = ra.null_population(BOUNDS, 24, seed=2)
print('3. null population: 26 past and 24 new random edits, e.g.', past[0])
past_out = {f'p{i}': run(e, f'p{i}') for i, e in enumerate(past)}
new_out = {f'n{i}': run(e, f'n{i}') for i, e in enumerate(new)}

eligible = [s for s in OLD if parent[s]]
past_lost = {c: set(ra.directional(parent, o, OLD)['lost']) for c, o in past_out.items()}
d0 = ra.directional(parent, new_out['n0'], OLD)
print('2. directional (edit n0): lost', len(d0['lost']), 'gained', len(d0['gained']), 'net', d0['net'],
      'conditional loss', tuple(round(x, 3) for x in d0['conditional_loss']))

counts = ra.loss_history(past_lost.values())
H = ra.history_suite(counts, eligible, k=8, seed=3)
U = ra.uniform_suite(eligible, k=8, seed=4)
print('4. history suite:', H)

caught_h = caught_u = lossy = 0
exp_u = 0.0
for c, o in new_out.items():
    lost = set(ra.directional(parent, o, OLD)['lost'])
    if not lost:
        continue
    lossy += 1
    caught_h += ra.zero_loss_gate(parent, o, TARGET, H)['suite_lost'] != []
    caught_u += ra.zero_loss_gate(parent, o, TARGET, U)['suite_lost'] != []
    exp_u += ra.expected_uniform_detection(len(eligible), len(lost), 8)
print(f'5. new edits with losses: {lossy}; caught by history suite {caught_h}, by uniform suite {caught_u}, '
      f'uniform expectation {exp_u:.1f}')
loo = ra.leave_one_out_detection(past_lost, eligible, k=8, seed=3)
print(f"   leave-one-out on past edits: history {loo['history_detect_rate']:.2f} vs uniform "
      f"{loo['uniform_expected_rate']:.2f}")
