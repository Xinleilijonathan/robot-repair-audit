"""Record SHA-256 hashes of the Extension 2 materials (extension2_protocol.md §8). Refuses to overwrite."""
import hashlib
import json
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
S = ROOT / 'outputs' / 'robot_repair_study'
files = [S / 'extension2_protocol.md', S / 'make_ext2_materials.py', S / 'ext2_suites.json',
         S / 'ext2_validation_scenes.json', S / 'ext2_gates.py', S / 'analyze_ext2.py',
         ROOT / 'work' / 'run_extension2.ps1', ROOT / 'work' / 'launch_isaac_ps51_timeout.ps1',
         S / 'run_stock_scene.py', S / 'ext1_audit_scenes.json', S / 'ext1_validation_scenes.json',
         S / 'explore_margin.py', S / 'explore_history.py', S / 'explore_history_strict.py']
files += sorted((S / 'proposals' / 'ext2').glob('*.json'))
files += sorted((S / 'results' / 'exploratory').glob('*'))
out = S / 'extension2_frozen_hashes.json'
if out.exists():
    raise SystemExit(f'Refusing to overwrite {out}')
rec = {'frozen_local': datetime.now().astimezone().isoformat(),
       'note': 'Extension 2 materials hashed before any Extension 2 rollout.',
       'files': [{'path': str(p.relative_to(ROOT)), 'sha256': hashlib.sha256(p.read_bytes()).hexdigest()}
                 for p in files]}
out.write_text(json.dumps(rec, indent=1))
print(f"{len(rec['files'])} files frozen at {rec['frozen_local']}")
