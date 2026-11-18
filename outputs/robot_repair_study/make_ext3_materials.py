"""Extension 3 materials (extension3_protocol.md §2-§4). Refuses to overwrite.

1. Loss history: for each of the 50 earlier audited candidates (Extension 1: A, B, r01-r24;
   Extension 2: r25-r48), its target and old-scene changes against its own audit parent on the
   Extension 1 audit panel. The 73 old parent successes are ranked by how many of the 50 lost them;
   ties broken by a seeded random order (seed 20261131). The top 8 form the PRIMARY history suite,
   the top 4 the k=4 secondary suite. The frozen Extension 2 suites are carried over as secondary.
2. Prompts: blind.md (task, six-parameter interface, controller source, the development failure,
   development successes, scoring, goal, answer format) and memory.md (blind + the loss-history
   record of the 50 earlier edits). Both are written once and hashed before any agent is called.
3. Agents: ext3_agents.json (five agents, two conditions, two samples each).
"""
import hashlib
import json
import random
from collections import Counter
from pathlib import Path

STUDY = Path(__file__).resolve().parent
R1, R2 = STUDY / 'results' / 'ext1', STUDY / 'results' / 'ext2'
TIE_SEED, K = 20261131, 8
CONTROLLER_SRC = Path(r'C:\Users\Jonat\Documents\Codex\isaac-sim-env\Lib\site-packages\isaacsim\exts'
                      r'\isaacsim.robot_motion.examples\isaacsim\robot_motion\examples\manipulation'
                      r'\controllers\pick_place.py')
BOUNDS = {  # identical to run_stock_scene.py allowed_overrides
    'approach_height': (0.05, 0.40),
    'lift_height': (0.10, 0.40),
    'position_tolerance': (0.005, 0.035),
    'grasp_position_tolerance': (0.005, 0.035),
    'stability_duration': (0.05, 0.50),
    'gripper_dwell': (0.10, 1.00),
}
STOCK = {'approach_height': 0.30, 'lift_height': 0.30, 'position_tolerance': 0.015,
         'grasp_position_tolerance': 0.015, 'stability_duration': 0.10, 'gripper_dwell': 0.20}
MEANING = {
    'approach_height': 'vertical offset above the pick/place pose used in the APPROACH phases (m)',
    'lift_height': 'vertical offset above the pick/place pose used in LIFT and RETREAT (m)',
    'position_tolerance': 'tool-position error below which a phase counts as converged (m), all phases except GRASP',
    'grasp_position_tolerance': 'the same tolerance used only in GRASP (m); stored separately, so changing '
                                'position_tolerance does not change it',
    'stability_duration': 'time the tool must stay converged before the phase advances (s)',
    'gripper_dwell': 'minimum time spent in GRASP and RELEASE (s)',
}
POPULATIONS = [(R1, ['candidate_a', 'candidate_b'] + [f'r{i:02d}' for i in range(1, 25)]),
               (R2, [f'r{i:02d}' for i in range(25, 49)])]
AGENTS = [
    {'agent': 'claude-opus', 'vendor': 'Anthropic', 'cli': 'claude', 'model': 'opus'},
    {'agent': 'claude-sonnet', 'vendor': 'Anthropic', 'cli': 'claude', 'model': 'sonnet'},
    {'agent': 'claude-haiku', 'vendor': 'Anthropic', 'cli': 'claude', 'model': 'haiku'},
    {'agent': 'gpt', 'vendor': 'OpenAI', 'cli': 'codex', 'model': 'gpt-6-astra'},
    {'agent': 'gemini', 'vendor': 'Google', 'cli': 'gemini', 'model': None},
]


def load(folder):
    rows = {}
    for p in sorted(folder.glob('rollout_*.json')):
        r = json.loads(p.read_text())
        assert r['scene_id'] not in rows
        rows[r['scene_id']] = r
    return rows


def ok(r):
    return bool(r['object_state_success'])


def fmt(v):
    return f'{v:.3f}'.rstrip('0').rstrip('.') if isinstance(v, float) else str(v)


def main():
    prompt_dir = STUDY / 'ext3_prompts'
    suites_path = STUDY / 'ext3_suites.json'
    agents_path = STUDY / 'ext3_agents.json'
    for p in (prompt_dir, suites_path, agents_path):
        if p.exists():
            raise SystemExit(f'Refusing to overwrite frozen material {p}')

    audit = json.loads((STUDY / 'ext1_audit_scenes.json').read_text())
    by_id = {s['id']: s for s in audit}
    old = [s['id'] for s in audit if s['regime'] == 'old']
    tgt = [s['id'] for s in audit if s['regime'] == 'target']
    past, counts, succ_ref, loss_modes = [], Counter(), None, []
    for root, ids in POPULATIONS:
        parent = load(root / 'audit_parent')
        succ = sorted(s for s in old if ok(parent[s]))
        succ_ref = succ_ref or succ
        assert succ == succ_ref, 'audit parents disagree on old successes'
        fail = [s for s in old if not ok(parent[s])]
        for cid in ids:
            rows = load(root / f'audit_{cid}')
            meta = json.loads((root / f'audit_{cid}' / 'metadata.json').read_text())
            lost = sorted(s for s in succ if not ok(rows[s]))
            counts.update(lost)
            loss_modes.extend((rows[s]['controller_status'].get('phase'), rows[s]['final_error_m']) for s in lost)
            past.append({'id': cid, 'population': root.name, 'overrides': meta['controller_overrides'],
                         'target_gained': sum(ok(rows[s]) and not ok(parent[s]) for s in tgt),
                         'target_lost': sum(ok(parent[s]) and not ok(rows[s]) for s in tgt),
                         'old_lost': len(lost), 'old_gained': sum(ok(rows[s]) for s in fail), 'lost_scenes': lost})
    succ = succ_ref
    tie = random.Random(TIE_SEED)
    tiebreak = {s: tie.random() for s in succ}
    ranked = sorted(succ, key=lambda s: (-counts.get(s, 0), tiebreak[s]))
    ext2 = json.loads((STUDY / 'ext2_suites.json').read_text())
    n_parent_target = sum(ok(load(R1 / 'audit_parent')[s]) for s in tgt)

    src = CONTROLLER_SRC.read_text(encoding='utf-8')
    params = '\n'.join(f'| `{p}` | {fmt(STOCK[p])} | {fmt(BOUNDS[p][0])} to {fmt(BOUNDS[p][1])} | {MEANING[p]} |'
                       for p in BOUNDS)
    blind_head = f"""You are improving a robot controller. Propose ONE parameter edit.
Answer from the information in this message only. Do not use any tools: do not read or write files, run commands or search the web.

## System
NVIDIA Isaac Sim 6.2, Franka Panda arm, the stock pick-and-place example. CPU physics at 60 Hz. One 5 cm cube is picked from a position on the table and placed at a fixed goal (x = 0, y = 0.5 m). Each run has a horizon of 1,800 steps (30 s).

## What you may change
Six scalar parameters of the pick-and-place state machine. Everything else (motion generation, phase timeouts, scenes and scoring) is fixed.

| Parameter | Current value | Allowed range | Meaning |
|---|---|---|---|
{params}

## Controller source (the state machine these parameters belong to)
```python
{src}
```

## The failure to fix
Scene: the cube is picked at radius 0.80 m from the robot base, angle -60 degrees (pick position x = 0.400, y = -0.693 m). In three runs the controller lifted the cube, then timed out in the LIFT phase after 5 s with a tool position error of 0.0203 m against the 0.015 m convergence tolerance; the cube never reached the goal. Nearby scenes at radius 0.80-0.85 m fail the same way.

## What currently works
On development scenes the unchanged controller succeeded in all 36 runs on 12 hand-specified scenes, and in 44 of 45 runs on a grid of pick radii 0.35, 0.55 and 0.75 m at angles from -60 to 60 degrees. It failed all 30 runs at radii 0.80-0.85 m.

## Scoring
A run succeeds only if the cube is lifted above 7.58 cm and the run ends before the horizon, and over the final 30 frames the cube stays within 3.0 cm of the goal, released (gripper more than 8 cm away) and at rest (linear speed below 0.02 m/s, angular speed below 0.1 rad/s, orientation drift below 0.05 rad).
"""
    rows = []
    for i, e in enumerate(past, 1):
        ov = ', '.join(f'{k} = {fmt(float(v))}' for k, v in e['overrides'].items())
        rows.append(f"| {i} | {ov} | +{e['target_gained']} / -{e['target_lost']} | {e['old_lost']} | {e['old_gained']} |")
    top = []
    for s in ranked[:10]:
        sc = by_id[s]
        top.append(f"- radius {sc['radius_m']:.3f} m, angle {sc['angle_deg']:.1f} degrees: broken by {counts[s]} of {len(past)} edits")
    improvers = [e for e in past if e['target_gained'] - e['target_lost'] > 0]
    placement = [err for phase, err in loss_modes if phase == 'DONE' and err > 0.03]
    mode_line = (f"In {len(placement)} of the {len(loss_modes)} broken workspace runs the controller still completed "
                 f"the motion but left the cube {100 * min(placement):.1f}-{100 * max(placement):.1f} cm from the goal, "
                 f"outside the 3 cm allowed.") if placement else ''
    n_free = sum(e['old_lost'] == 0 for e in improvers)
    improver_line = (f"Of the {len(past)} edits, {len(improvers)} improved the target scenes; "
                     + (f"every one of these {len(improvers)} also broke at least one workspace success."
                        if n_free == 0 else f"{n_free} of these {len(improvers)} broke no workspace success."))
    memory_block = f"""
## Your memory: what earlier edits did
{len(past)} earlier edits to this controller were each tested on one fixed panel: {len(tgt)} scenes near the failure (the unchanged controller solved {n_parent_target}) and {len(old)} scenes across the workspace (it solved {len(succ)}). For each edit: the parameters it changed (all others at their current values), target scenes newly solved / newly failed, workspace successes it broke (of {len(succ)}), and workspace failures it fixed (of {len(old) - len(succ)}).

| # | Edit | Target scenes | Workspace successes broken | Workspace failures fixed |
|---|---|---|---|---|
{chr(10).join(rows)}

The workspace scenes these edits broke most often:
{chr(10).join(top)}

{improver_line} {mode_line}
"""
    tail = """
## Your goal
Fix the failure above without breaking scenes the controller already solves. Your edit will be tested on scenes near the failing one and on scenes across the workspace.

## Answer format
Reply with only a JSON object, no other text:
{"overrides": {"<parameter>": <number>, ...}, "rationale": "<at most 3 sentences>", "expected_risk": "<at most 2 sentences>"}
Use 1 to 6 parameters from the table, each within its allowed range.
"""
    prompt_dir.mkdir()
    (prompt_dir / 'blind.md').write_bytes((blind_head + tail).encode('utf-8'))
    (prompt_dir / 'memory.md').write_bytes((blind_head + memory_block + tail).encode('utf-8'))

    suites = {'source': 'Extension 1 audit panel (ext1_audit_scenes.json); 50 earlier candidate audits '
                        '(results/ext1: A, B, r01-r24; results/ext2: r25-r48), each against its own audit parent; '
                        'all recorded before Extension 3',
              'parent_old_successes': succ,
              'loss_counts_50': {s: counts.get(s, 0) for s in ranked},
              'history_ranked': ranked,
              'history_suite': ranked[:K],
              'history_suite_k4': ranked[:4],
              'ext2_history_suite': ext2['history_suite'],
              'ext2_history_suite_k4': ext2['history_suite_k4'],
              'ext2_uniform_suite': ext2['uniform_suite'],
              'past_edits': past,
              'controller_source': {'path': str(CONTROLLER_SRC),
                                    'sha256': hashlib.sha256(CONTROLLER_SRC.read_bytes()).hexdigest()},
              'seeds': {'history_tiebreak': TIE_SEED}}
    suites_path.write_text(json.dumps(suites, indent=1))
    agents = {'conditions': ['blind', 'memory'], 'samples_per_condition': 2, 'bounds': BOUNDS, 'stock_values': STOCK,
              'agents': AGENTS}
    agents_path.write_text(json.dumps(agents, indent=1))

    print('parent old successes:', len(succ), '| past edits:', len(past), '| total losses:', sum(counts.values()))
    print('history suite (50-edit loss counts):', [(s, counts[s]) for s in ranked[:K]])
    print('ext2 history suite:', ext2['history_suite'], '| overlap:', sorted(set(ranked[:K]) & set(ext2['history_suite'])))
    print('target improvers among past:', len(improvers), '| loss-free:', sum(e['old_lost'] == 0 for e in improvers))
    print('loss modes:', Counter(phase for phase, _ in loss_modes), '| placement line:', mode_line)
    for name in ('blind.md', 'memory.md'):
        print(name, len((prompt_dir / name).read_bytes()), 'bytes')


if __name__ == '__main__':
    main()
