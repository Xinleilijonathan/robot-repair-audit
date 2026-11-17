"""Build the anonymized review artifact (zip) from the study folder.

Copies outputs/robot_repair_study plus the launch/queue scripts, replaces machine-specific
absolute paths with placeholders in text files, then FAILS if any identifying string remains.
Run-time logs are excluded (they duplicate rollout records and contain local paths).
Files whose bytes change through path substitution are listed in ANONYMIZATION.md, because
their recorded SHA-256 values refer to the original, pre-substitution bytes.
"""
import hashlib
import shutil
import sys
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
STUDY = ROOT / 'outputs' / 'robot_repair_study'
OUT_DIR = ROOT / 'artifact'
SCRIPTS = ['launch_isaac.ps1', 'launch_isaac_ps51.ps1', 'run_repair_batches.ps1', 'run_audit_batches.ps1',
           'launch_isaac_ps51_timeout.ps1', 'run_extension1.ps1', 'run_extension2.ps1', 'freeze_ext2.py']
PAPER_SCRIPTS = ['make_tables.py', 'make_population_table.py', 'make_combined_gate_table.py']
_root = str(ROOT).replace('/', '\\')
_env = 'C:\\Users\\Jonat\\Documents\\Codex\\isaac-sim-env'
_home = 'C:\\Users\\Jonat'
REPLACE = []
for _path, _tag in ((_root, '<STUDY_ROOT>'), (_env, '<ISAAC_ENV>'), (_home, '<USER_HOME>')):
    # backslash, escaped-backslash (JSON) and forward-slash spellings; most specific first
    REPLACE += [(_path, _tag), (_path.replace('\\', '\\\\'), _tag), (_path.replace('\\', '/'), _tag)]
FORBIDDEN = ['Jonat', 'northeastern', 'li.xinle', 'xinle']
TEXT = {'.py', '.md', '.json', '.txt', '.ps1', '.csv', '.toml', '.yaml', '.yml', '.cfg', '.ini'}


def main():
    stage = OUT_DIR / 'robot_repair_artifact'
    if stage.exists():
        shutil.rmtree(stage)
    shutil.copytree(STUDY, stage / 'robot_repair_study',
                    ignore=shutil.ignore_patterns('__pycache__', '*.log', '*.err'))
    (stage / 'scripts').mkdir()
    for name in SCRIPTS:
        shutil.copy2(ROOT / 'work' / name, stage / 'scripts' / name)
    for name in PAPER_SCRIPTS:
        shutil.copy2(ROOT / 'paper' / name, stage / 'scripts' / name)
    kit = ROOT / 'outputs' / 'regression_audit_kit'
    if kit.exists():
        shutil.copytree(kit, stage / 'regression_audit_kit', ignore=shutil.ignore_patterns('__pycache__'))
    changed = []
    for path in stage.rglob('*'):
        if path.is_file() and path.suffix.lower() in TEXT:
            raw = path.read_bytes()
            text = raw.decode('utf-8', errors='strict')
            new = text
            for old, rep in REPLACE:
                new = new.replace(old, rep)
            if new != text:
                path.write_text(new, encoding='utf-8')
                changed.append((path.relative_to(stage).as_posix(), hashlib.sha256(raw).hexdigest()))
    leaks = []
    for path in stage.rglob('*'):
        if path.is_file():
            data = path.read_bytes().decode('utf-8', errors='ignore').lower()
            leaks += [(path.relative_to(stage).as_posix(), w) for w in FORBIDDEN if w.lower() in data]
    if leaks:
        sys.exit(f'Identifying strings remain, refusing to package: {leaks[:10]}')
    notes = ['# Anonymization notes', '',
             'Machine-specific absolute paths were replaced with `<STUDY_ROOT>`, `<ISAAC_ENV>` and `<USER_HOME>`.',
             'Run logs were omitted (they duplicate the per-rollout JSON records).',
             'The following files changed by path substitution only; recorded hashes refer to the',
             'original bytes (original SHA-256 shown). All other files are byte-identical to the',
             'files hashed in the frozen records.', '']
    notes += [f'- `{p}` (original sha256 {h})' for p, h in changed] or ['- none']
    (stage / 'ANONYMIZATION.md').write_text('\n'.join(notes) + '\n', encoding='utf-8')
    zip_path = OUT_DIR / 'robot_repair_artifact.zip'
    with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as z:
        for path in sorted(stage.rglob('*')):
            if path.is_file():
                z.write(path, path.relative_to(stage.parent).as_posix())
    print(f'{zip_path} ({zip_path.stat().st_size / 1e6:.1f} MB); {len(changed)} files path-substituted')


if __name__ == '__main__':
    main()
