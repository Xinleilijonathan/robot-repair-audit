import pathlib,json,statistics,hashlib
root=pathlib.Path(__file__).resolve().parents[1]
base=root/'outputs/robot_repair_study'
rows=[json.loads(p.read_text()) for p in sorted((base/'results/feasibility').glob('rollout_*.json'))]
assert len(rows)==18
summary={'n':len(rows),'successes':sum(r['object_state_success'] for r in rows),'median_rollout_seconds':statistics.median(r['wall_seconds'] for r in rows),'total_rollout_seconds':sum(r['wall_seconds'] for r in rows),'scene_details':{}}
for scene in sorted({r['scene_id'] for r in rows}):
    group=[r for r in rows if r['scene_id']==scene]
    summary['scene_details'][scene]={'successes':sum(r['object_state_success'] for r in group),'repeats':len(group),'final_errors_m':[r['final_error_m'] for r in group],'identical_final_positions':all(r['cube_final']==group[0]['cube_final'] for r in group)}
(base/'results/feasibility/summary.json').write_text(json.dumps(summary,indent=2))
# Reconstruct the exact already-executed source, then verify against its saved hash.
s=(base/'run_stock_scene.py').read_text()
s=s.replace('(args.output / "runner_snapshot.py").write_bytes(Path(__file__).read_bytes())\n','')
a=s.index('                mode = scene.get('); b=s.index('            position = task.cubes',a)
s=s[:a]+'                task.step(1 / 60)\n'+s[b:]
s=s.replace('            "control_mode": scene.get("control_mode", "normal"),\n','')
s=s.replace('lift above 0.0758m; final 30 frames within 0.03m of goal, grasp separation above 0.08m, linear speed below 0.02m/s, orientation drift below 0.05rad; finish before horizon','lift above 0.0758m; cube within 0.03m of goal and grasp-frame separation above 0.08m for final 30 frames')
expected=json.loads((base/'results/feasibility/metadata.json').read_text())['script_sha256']
assert hashlib.sha256(s.encode()).hexdigest()==expected, 'Source reconstruction hash mismatch'
(base/'results/feasibility/runner_snapshot.py').write_bytes(s.encode())
print(json.dumps(summary,indent=2))
