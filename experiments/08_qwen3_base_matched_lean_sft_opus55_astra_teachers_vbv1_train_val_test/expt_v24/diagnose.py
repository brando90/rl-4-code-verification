"""Recover source-bound compiler diagnostics for three completed runs without changing their official scores."""
from concurrent.futures import ThreadPoolExecutor, as_completed
import collections
import csv
import hashlib
import json
import os
from pathlib import Path
import re
import signal
import subprocess
import time

RUN = Path('/lfs/skampere1/0/eth127/rl4cv_tiny_training')
OUT = RUN / 'failure_diagnostics_v24'
SEARCH = r'exact\?|apply\?|simp(?:_all|_rw|_arith|\?)?|simpa\??|omega\??|aesop\??|linarith!?|nlinarith!?|ring(?:_nf)?|norm_num!?|grind|tauto|solve_by_elim'
ERROR = re.compile(r'^.*?:(\d+):(\d+): error:\s*(.*)$', re.M)

def sha(data):
    return hashlib.sha256(data).hexdigest()

def write(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + '.tmp')
    tmp.write_text(json.dumps(value, indent=2) + '\n')
    tmp.replace(path)

def classify(text, rc):
    matches = list(ERROR.finditer(text))
    if not matches:
        return ('diagnostic_timeout' if rc == 124 else 'diagnostic_recompile_passed' if rc == 0 else 'other_no_formatted_error'), '', []
    first = text[matches[0].start():matches[1].start() if len(matches) > 1 else len(text)]
    t = first.lower()
    if re.search(r'unknown (?:identifier|constant|tactic|namespace)|environment does not contain|invalid field|invalid dotted identifier', t):
        category = 'unknown_name_tactic_or_member'
    elif 'type mismatch' in t or 'has type' in t and 'expected to have type' in t:
        category = 'type_mismatch'
    elif re.search(r'unexpected|expected token|unterminated|invalid syntax|invalid constructor|invalid notation', t):
        category = 'syntax_or_notation'
    elif re.search(r'(?:native_decide|decide).*?(?:evaluated|proved|determined).*?proposition', t, re.S) and re.search(r'false|not true', t):
        category = 'decision_procedure_false_proposition'
    elif re.search(r'synthesize|typeclass|failed to infer|cannot infer|don.t know how to infer', t):
        category = 'instance_or_type_inference'
    elif re.search(r'\b(?:native_decide|decide)\b', t) and re.search(r'failed|cannot|could not|error|not reduc|not support', t):
        category = 'failed_decision_procedure'
    elif re.search(r'\b(?:' + SEARCH + r')\b', t) and re.search(r'failed|could not|made no progress|unsolved', t):
        category = 'failed_proof_search'
    elif 'unsolved goals' in t:
        category = 'unsolved_goals'
    elif re.search(r'heartbeat|recursion|termination|maximum number', t):
        category = 'recursion_termination_or_resource'
    elif 'tactic' in t or 'no goals to be solved' in t:
        category = 'other_failed_proof_step'
    else:
        category = 'other_first_diagnostic'
    flags = []
    for m in matches:
        block = text[m.start():text.find('\n', m.end()) if text.find('\n', m.end()) >= 0 else len(text)]
        if re.search(r'\b(?:native_decide|decide)\b', block):
            flags.append('decision_procedure_reported_in_error')
        if re.search(r"tactic\s+['`‘’]?(?:" + SEARCH + r")(?!\w).*?(?:failed|could not|made no progress)|(?<!\w)(?:" + SEARCH + r")(?!\w)\s+(?:could not prove|made no progress)", block, re.I):
            flags.append('proof_search_reported_failed')
    return category, first[:6000], sorted(set(flags))

def collect_case(v, row):
    label = 'v12_current' if v == 12 else f'v{v}_base'
    root = RUN / f'corpus_training_v{v}'
    tid, sample = row['task_id'], int(row['sample_idx'])
    output = OUT / f'v{v}' / 'cells' / f's{sample}' / tid
    source = root / 'validation' / label / 'jobs' / f'{label}_s{sample}' / tid / 'verifier/solution.lean'
    digest = sha(source.read_bytes())
    receipt = output / 'diagnostic.json'
    if receipt.exists():
        saved = json.loads(receipt.read_text())
        assert saved['source_sha256'] == digest
        assert sha((output/'stdout.log').read_bytes()) == saved['stdout_sha256']
        assert sha((output/'stderr.log').read_bytes()) == saved['stderr_sha256']
        return saved
    start = time.time()
    reused = False
    if v == 12:
        old = root / 'analysis/failure_diagnostics_current/cells' / f's{sample}' / tid
        meta = json.loads((old/'diagnostic.json').read_text())
        assert meta['source_sha256'] == digest
        stdout = (old/'compile.log').read_bytes()
        stderr = b''
        rc = meta['returncode']
        reused = True
        command = ['REUSE_EXISTING_V12_COMBINED_LOG']
    else:
        command = [str(RUN/'bin/lake'), 'env', 'lean', str(source)]
        env = dict(os.environ, CUDA_VISIBLE_DEVICES='', PATH=str(RUN/'bin')+':'+os.environ['PATH'])
        process = subprocess.Popen(command, cwd=RUN/'grading', env=env, stdout=subprocess.PIPE, stderr=subprocess.PIPE, start_new_session=True)
        try:
            stdout, stderr = process.communicate(timeout=20)
            rc = process.returncode
        except subprocess.TimeoutExpired:
            try: os.killpg(process.pid, signal.SIGTERM)
            except ProcessLookupError: pass
            try:
                stdout, stderr = process.communicate(timeout=2)
            except subprocess.TimeoutExpired:
                os.killpg(process.pid, signal.SIGKILL)
                stdout, stderr = process.communicate()
            rc = 124
    text = stdout.decode(errors='replace') + '\n' + stderr.decode(errors='replace')
    category, first, flags = classify(text, rc)
    first_match = ERROR.search(text)
    source_line = ''
    if first_match:
        lines = source.read_text().splitlines()
        lineno = int(first_match.group(1))
        source_line = lines[lineno-1] if 0 < lineno <= len(lines) else ''
        if re.search(r'\bnative_decide\b', source_line): flags.append('native_decide_at_first_error_location')
        if re.search(r'(?<![\w])decide(?![\w])', source_line): flags.append('decide_at_first_error_location')
        if re.search(r'\bDecidable(?:Pred|Eq)?\b', first): flags.append('decidable_instance_in_first_error')
    output.mkdir(parents=True, exist_ok=True)
    (output/'stdout.log').write_bytes(stdout)
    (output/'stderr.log').write_bytes(stderr)
    result = dict(run=v, task_id=tid, sample_idx=sample, source_sha256=digest, source_path=str(source),
                  returncode=rc, diagnostic_timeout=rc==124, diagnostic_seconds=20, reused_existing_log=reused,
                  first_category=category, first_error=first, first_error_source_line=source_line, error_flags=flags, stdout_sha256=sha(stdout), stderr_sha256=sha(stderr),
                  command=command, elapsed_seconds=time.time()-start, official_verdict_changed=False)
    write(receipt, result)
    return result

def truth(value):
    return str(value).lower() in ['true','1','1.0']

def main():
    OUT.mkdir(exist_ok=True)
    pin = json.loads((RUN/'scoring_preflight.json').read_text())
    assert sha((RUN/'bin/lake').read_bytes()) == pin['lake_adapter_sha256']
    manifest = dict(state='RUNNING', workers=96, diagnostic_seconds=20, toolchain=pin, source_sha256=sha(Path(__file__).read_bytes()), official_scores_changed=False, teacher_calls=0)
    write(OUT/'protocol.json', manifest)
    allrows, pending = [], []
    for v in [12,20,23]:
        label = 'v12_current' if v==12 else f'v{v}_base'
        root = RUN/f'corpus_training_v{v}'
        rows = list(csv.DictReader((root/'analysis'/f'{label}_cells.csv').open()))
        assert len(rows) == 1080 and len({(r['task_id'],r['sample_idx']) for r in rows}) == 1080
        for row in rows:
            base = dict(run=v,task_id=row['task_id'],sample_idx=int(row['sample_idx']))
            if truth(row['compiles']):
                allrows.append(dict(base, first_category='success'))
            elif not truth(row['extracted']):
                allrows.append(dict(base, first_category='no_extracted_lean',capped=truth(row.get('capped','False'))))
            else:
                pending.append((v,row))
    write(OUT/'progress.json',dict(state='RUNNING',completed=0,declared=len(pending),observed_unix=time.time()))
    with ThreadPoolExecutor(max_workers=96) as pool:
        jobs = [pool.submit(collect_case,v,r) for v,r in pending]
        for i,f in enumerate(as_completed(jobs),1):
            allrows.append(f.result())
            if i%25==0:
                write(OUT/'progress.json',dict(state='RUNNING',completed=i,declared=len(pending),observed_unix=time.time()))
    summaries = {}
    for v in [12,20,23]:
        rs=[r for r in allrows if r['run']==v]
        assert len(rs)==1080
        summaries[str(v)] = dict(declared=1080, first_diagnostic_categories=dict(collections.Counter(r['first_category'] for r in rs)),
                                overlapping_error_flags=dict(collections.Counter(f for r in rs for f in r.get('error_flags',[]))),
                                diagnostics_reused=sum(r.get('reused_existing_log',False) for r in rs))
    keys=['run','task_id','sample_idx','first_category','returncode','diagnostic_timeout','source_sha256','error_flags','first_error','first_error_source_line']
    with (OUT/'all_cells.csv').open('w') as f:
        w=csv.DictWriter(f,fieldnames=keys,extrasaction='ignore',lineterminator='\n');w.writeheader();w.writerows(sorted(allrows,key=lambda r:(r['run'],r['task_id'],r['sample_idx'])))
    write(OUT/'summary.json',dict(state='COMPLETE',runs=summaries,first_diagnostic_not_proven_root_cause=True,diagnostic_timeout_not_official_score_timeout=True,official_scores_changed=False))
    write(OUT/'progress.json',dict(state='COMPLETE',completed=len(pending),declared=len(pending),observed_unix=time.time()))

if __name__=='__main__':
    main()
