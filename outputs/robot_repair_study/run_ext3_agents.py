"""Collect the Extension 3 agent proposals (extension3_protocol.md §2). Refuses to overwrite.

Each proposal is one fresh, non-interactive CLI session started in a new EMPTY directory outside the
project, with the frozen prompt (ext3_prompts/<condition>.md) on stdin. Information-access tools are
disabled where the CLI allows it, and every transcript is saved. A proposal is re-requested once
(fresh session) if the CLI errors, times out, uses an information-access tool (file read/write,
shell command, MCP tool, web search) or returns no valid edit; after a second failure it is excluded.

Valid edit: a JSON object with "overrides" naming 1-6 of the six parameters, numeric values within
the runner's bounds after rounding to 3 decimals. Exact duplicates of an earlier proposal (in index
order) are recorded but not re-run; an edit equal to the stock values is a no-op and not run.

Usage:
  python run_ext3_agents.py --out proposals/ext3            # the frozen collection (once)
  python run_ext3_agents.py --smoke SCRATCH_DIR             # CLI check with a trivial prompt only
"""
import argparse
import hashlib
import json
import math
import os
import re
import subprocess
import tempfile
import time
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from pathlib import Path

STUDY = Path(__file__).resolve().parent
NPM = Path(os.environ['APPDATA']) / 'npm'
CLAUDE_EXE = NPM / 'node_modules' / '@anthropic-ai' / 'claude-code' / 'bin' / 'claude.exe'
NODE_DIR = Path(r'C:\Program Files\nodejs')
NODE = NODE_DIR / 'node.exe'
CODEX_JS = NPM / 'node_modules' / '@openai' / 'codex' / 'bin' / 'codex.js'
GEMINI_JS = NPM / 'node_modules' / '@google' / 'gemini-cli' / 'bundle' / 'gemini.js'
ENV = dict(os.environ, PATH=os.pathsep.join([str(NODE_DIR), str(NPM), os.environ.get('PATH', '')]))
SANDBOX_ROOT = Path(tempfile.gettempdir()) / 'ext3_agent_sandbox'
TIMEOUT_S = 900
SHORT = {'claude-opus': 'opus', 'claude-sonnet': 'sonnet', 'claude-haiku': 'haiku', 'gpt': 'gpt', 'gemini': 'gemini'}
CODEX_ALLOWED_ITEMS = {'agent_message', 'reasoning', 'todo_list'}
SMOKE_PROMPT = 'Reply with only this JSON object and nothing else: {"ok": true}\n'


def command(agent, workdir):
    cli, model = agent['cli'], agent['model']
    if cli == 'claude':
        return [str(CLAUDE_EXE), '-p', '--model', model, '--tools', '', '--safe-mode', '--strict-mcp-config',
                '--no-session-persistence', '--disable-slash-commands', '--output-format', 'json']
    if cli == 'codex':
        return [str(NODE), str(CODEX_JS), 'exec', '--json', '--ephemeral', '--skip-git-repo-check',
                '--ignore-user-config', '--ignore-rules', '-s', 'read-only', '-C', str(workdir), '-m', model,
                '-c', 'model_reasoning_effort="high"', '--disable', 'memories', '--disable', 'shell_tool',
                '--disable', 'unified_exec', '--disable', 'apps', '--disable', 'plugins', '--disable', 'browser_use',
                '--disable', 'computer_use', '--disable', 'image_generation', '-']
    if cli == 'gemini':
        cmd = [str(NODE), str(GEMINI_JS), '-p', 'Follow the instructions in the message above.', '-o', 'json',
               '--approval-mode', 'plan', '--skip-trust']
        return cmd + (['-m', model] if model else [])
    raise ValueError(cli)


def parse(cli, stdout):
    """Return (final_text, tool_calls, models_reported, error) from a CLI transcript."""
    if cli == 'claude':
        d = json.loads(stdout)
        return (d.get('result') or '', 0, sorted((d.get('modelUsage') or {}).keys()),
                d.get('subtype') if d.get('is_error') else None)
    if cli == 'codex':
        text, tools, err, models = '', 0, None, set()
        for line in stdout.splitlines():
            line = line.strip()
            if not line.startswith('{'):
                continue
            ev = json.loads(line)
            if ev.get('model'):
                models.add(ev['model'])
            item = ev.get('item') or {}
            if ev.get('type') == 'item.completed':
                if item.get('type') == 'agent_message':
                    text = item.get('text', '')
                elif item.get('type') not in CODEX_ALLOWED_ITEMS:
                    tools += 1
            if ev.get('type') in ('error', 'turn.failed'):
                err = json.dumps(ev)[:500]
        return text, tools, sorted(models), err
    if cli == 'gemini':
        start = stdout.find('{')
        d = json.loads(stdout[start:])
        stats = d.get('stats') or {}
        return (d.get('response') or '', int((stats.get('tools') or {}).get('totalCalls', 0)),
                sorted((stats.get('models') or {}).keys()), json.dumps(d['error'])[:500] if d.get('error') else None)
    raise ValueError(cli)


def extract(text):
    text = text.strip()
    candidates = [text]
    for i, ch in enumerate(text):
        if ch == '{':
            depth = 0
            for j in range(i, len(text)):
                depth += {'{': 1, '}': -1}.get(text[j], 0)
                if depth == 0:
                    candidates.append(text[i:j + 1])
                    break
    for c in candidates:
        try:
            d = json.loads(c)
        except (json.JSONDecodeError, ValueError):
            continue
        if isinstance(d, dict) and 'overrides' in d:
            return d
    return None


def validate(answer, bounds):
    if not answer or not isinstance(answer.get('overrides'), dict):
        return None, 'no overrides object'
    ov = answer['overrides']
    if not 1 <= len(ov) <= 6 or set(ov) - set(bounds):
        return None, f'bad parameter set {sorted(ov)}'
    out = {}
    for p in bounds:  # canonical order
        if p not in ov:
            continue
        v = ov[p]
        if isinstance(v, bool) or not isinstance(v, (int, float)) or not math.isfinite(v):
            return None, f'non-numeric {p}'
        r = round(float(v), 3)
        lo, hi = bounds[p]
        if not lo <= r <= hi:
            return None, f'{p}={v} outside [{lo}, {hi}]'
        out[p] = r
    return out, None


def run_once(agent, prompt, tag, transcripts):
    SANDBOX_ROOT.mkdir(parents=True, exist_ok=True)
    workdir = Path(tempfile.mkdtemp(prefix=f'{tag}_', dir=SANDBOX_ROOT))
    started = datetime.now(timezone.utc).isoformat()
    t0 = time.monotonic()
    try:
        proc = subprocess.run(command(agent, workdir), input=prompt.encode('utf-8'), cwd=workdir,
                              capture_output=True, timeout=TIMEOUT_S, env=ENV)
        stdout, stderr, code = proc.stdout.decode('utf-8', 'replace'), proc.stderr.decode('utf-8', 'replace'), proc.returncode
    except subprocess.TimeoutExpired as exc:
        stdout = (exc.stdout or b'').decode('utf-8', 'replace')
        stderr, code = 'TIMEOUT', None
    rec = {'started_utc': started, 'seconds': round(time.monotonic() - t0, 1), 'exit_code': code,
           'workdir': str(workdir), 'workdir_empty_after': not any(workdir.iterdir())}
    (transcripts / f'{tag}.stdout.txt').write_bytes(stdout.encode('utf-8'))
    (transcripts / f'{tag}.stderr.txt').write_bytes(stderr.encode('utf-8'))
    rec['transcript'] = f'transcripts/{tag}.stdout.txt'
    try:
        text, tools, models, err = parse(agent['cli'], stdout if stdout.strip() else stderr)
    except Exception as exc:  # unparseable transcript
        text, tools, models, err = '', 0, [], f'unparseable transcript: {exc!r}'[:300]
    rec.update({'final_text': text, 'information_tool_calls': tools, 'models_reported': models, 'cli_error': err})
    return rec


def collect_agent(agent, prompts, conditions, samples, bounds, transcripts):
    out = []
    for cond in conditions:
        for s in range(1, samples + 1):
            pid = f"{SHORT[agent['agent']]}_{cond[0]}{s}"
            attempts, overrides, reason, answer = [], None, None, None
            for k in (1, 2):
                rec = run_once(agent, prompts[cond], f'{pid}_a{k}', transcripts)
                answer = extract(rec['final_text'])
                overrides, reason = validate(answer, bounds)
                if rec['cli_error'] or rec['exit_code'] not in (0,):
                    overrides, reason = None, f"cli error: {rec['cli_error'] or rec['exit_code']}"
                if rec['information_tool_calls'] or not rec['workdir_empty_after']:
                    overrides, reason = None, f"tool use: {rec['information_tool_calls']} calls"
                rec['valid'] = overrides is not None
                rec['invalid_reason'] = reason
                attempts.append(rec)
                if overrides is not None:
                    break
            out.append({'id': pid, 'agent': agent['agent'], 'vendor': agent['vendor'], 'cli': agent['cli'],
                        'model_requested': agent['model'], 'condition': cond, 'sample': s,
                        'prompt_sha256': hashlib.sha256(prompts[cond].encode('utf-8')).hexdigest(),
                        'overrides': overrides, 'excluded': overrides is None, 'exclusion_reason': reason,
                        'rationale': (answer or {}).get('rationale'), 'expected_risk': (answer or {}).get('expected_risk'),
                        'attempts': attempts})
            print(pid, 'OK' if overrides else f'EXCLUDED ({reason})', overrides, flush=True)
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--out', type=Path)
    ap.add_argument('--smoke', type=Path)
    args = ap.parse_args()
    cfg = json.loads((STUDY / 'ext3_agents.json').read_text())
    if args.smoke:
        args.smoke.mkdir(parents=True, exist_ok=True)
        for agent in cfg['agents']:
            rec = run_once(agent, SMOKE_PROMPT, f"smoke_{SHORT[agent['agent']]}_{int(time.time())}", args.smoke)
            print(agent['agent'], {k: rec[k] for k in ('exit_code', 'seconds', 'information_tool_calls',
                                                       'models_reported', 'cli_error', 'workdir_empty_after')},
                  repr(rec['final_text'][:80]), flush=True)
        return
    out = args.out
    if out.exists():
        raise SystemExit(f'Refusing to overwrite {out}')
    prompts = {c: (STUDY / 'ext3_prompts' / f'{c}.md').read_bytes().decode('utf-8') for c in cfg['conditions']}
    transcripts = out / 'transcripts'
    transcripts.mkdir(parents=True)
    started = datetime.now(timezone.utc).isoformat()
    with ThreadPoolExecutor(max_workers=len(cfg['agents'])) as pool:
        futures = [pool.submit(collect_agent, a, prompts, cfg['conditions'], cfg['samples_per_condition'],
                               cfg['bounds'], transcripts) for a in cfg['agents']]
        props = [p for f in futures for p in f.result()]
    seen = {}
    for p in props:  # index order: agents as listed, then condition, then sample
        p['noop'] = p['duplicate_of'] = None
        p['run'] = False
        if p['excluded']:
            continue
        key = json.dumps(p['overrides'], sort_keys=True)
        if all(cfg['stock_values'][k] == v for k, v in p['overrides'].items()):
            p['noop'] = True
        elif key in seen:
            p['duplicate_of'] = seen[key]
        else:
            seen[key] = p['id']
            p['run'] = True
            (out / f"{p['id']}.json").write_text(json.dumps(p['overrides']))
    index = {'collected_utc': [started, datetime.now(timezone.utc).isoformat()],
             'sandbox_root': str(SANDBOX_ROOT), 'timeout_s': TIMEOUT_S, 'candidates': props}
    (out / 'index.json').write_text(json.dumps(index, indent=1))
    print(f"{sum(p['run'] for p in props)} distinct edits to run; "
          f"{sum(p['excluded'] for p in props)} excluded; {sum(bool(p['duplicate_of']) for p in props)} duplicates; "
          f"{sum(bool(p['noop']) for p in props)} no-ops")


if __name__ == '__main__':
    main()
