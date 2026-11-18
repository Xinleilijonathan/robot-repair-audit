"""Record SHA-256 hashes for Extension 3 (extension3_protocol.md §7). Refuses to overwrite.

  python freeze_ext3.py               -> extension3_frozen_hashes.json (before any agent call)
  python freeze_ext3.py --proposals   -> ext3_proposal_hashes.json (after collection, before any rollout)
"""
import hashlib
import json
import sys
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
S = ROOT / 'outputs' / 'robot_repair_study'
CONTROLLER = Path(r'C:\Users\Jonat\Documents\Codex\isaac-sim-env\Lib\site-packages\isaacsim\exts'
                  r'\isaacsim.robot_motion.examples\isaacsim\robot_motion\examples\manipulation'
                  r'\controllers\pick_place.py')


def rel(p):
    try:
        return str(p.relative_to(ROOT))
    except ValueError:
        return '<ISAAC_ENV>/' + p.as_posix().split('isaac-sim-env/', 1)[-1]


if '--proposals' in sys.argv:
    out = S / 'ext3_proposal_hashes.json'
    files = sorted(p for p in (S / 'proposals' / 'ext3').rglob('*') if p.is_file())
    note = 'Extension 3 agent proposals and transcripts, hashed after collection and before any Extension 3 rollout.'
else:
    out = S / 'extension3_frozen_hashes.json'
    files = [S / 'extension3_protocol.md', S / 'make_ext3_materials.py', S / 'ext3_suites.json',
             S / 'ext3_prompts' / 'blind.md', S / 'ext3_prompts' / 'memory.md', S / 'ext3_agents.json',
             S / 'run_ext3_agents.py', S / 'analyze_ext3.py', S / 'analyze_ext2.py',
             ROOT / 'work' / 'run_extension3.ps1', ROOT / 'work' / 'launch_isaac_ps51_timeout.ps1',
             S / 'run_stock_scene.py', S / 'ext1_audit_scenes.json', CONTROLLER]
    note = 'Extension 3 materials hashed before any agent was asked for a proposal and before any Extension 3 rollout.'
if out.exists():
    raise SystemExit(f'Refusing to overwrite {out}')
rec = {'frozen_local': datetime.now().astimezone().isoformat(), 'note': note,
       'files': [{'path': rel(p), 'sha256': hashlib.sha256(p.read_bytes()).hexdigest()} for p in files]}
out.write_text(json.dumps(rec, indent=1))
print(f"{len(rec['files'])} files hashed at {rec['frozen_local']} -> {out.name}")
