"""Bind frozen VERINA interfaces to Lean candidate fragments and evaluate fixed external tests."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
from datetime import datetime, timezone

ALLOWED = {"propext", "Classical.choice", "Quot.sound"}


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def section(source: str, name: str) -> tuple[int, int, str]:
    start = list(re.finditer(rf"(?m)^[ \t]*-- !benchmark @start {re.escape(name)}(?:[ \t][^\n]*)?\n", source))
    end = list(re.finditer(rf"(?m)^[ \t]*-- !benchmark @end {re.escape(name)}[ \t]*$", source))
    if len(start) != 1 or len(end) != 1 or start[0].end() > end[0].start():
        raise ValueError(f"missing, repeated or reversed section: {name}")
    return start[0].end(), end[0].start(), source[start[0].end():end[0].start()]


def after_section(source: str, name: str) -> int:
    return re.search(rf"(?m)^[ \t]*-- !benchmark @end {re.escape(name)}[ \t]*$", source).end()


def before_section(source: str, name: str) -> int:
    return re.search(rf"(?m)^[ \t]*-- !benchmark @start {re.escape(name)}(?:[ \t][^\n]*)?\n", source).start()


def load_task(root: Path, row: dict) -> dict:
    directory = root / 'datasets' / 'verina' / row['task_id']
    for name, expected in row['file_sha256'].items():
        if sha((directory / name).read_bytes()) != expected:
            raise ValueError(f"frozen task bytes changed: {row['task_id']}/{name}")
    source = (directory / 'task.lean').read_text()
    for name in ('import', 'solution_aux', 'precond_aux', 'precond', 'code_aux', 'code', 'postcond_aux', 'postcond', 'proof_aux', 'proof'):
        section(source, name)
    sig = json.loads((directory / 'task.json').read_text())['signature']
    if sig != row['signature']:
        raise ValueError('signature differs from frozen metadata')
    # These are source-defined slots, not regular-expression renamings of arbitrary declarations.
    public = source[after_section(source, 'import'):before_section(source, 'solution_aux')]
    public += source[after_section(source, 'solution_aux'):before_section(source, 'code_aux')]
    declaration = source[after_section(source, 'code_aux'):before_section(source, 'code')]
    requirements = source[after_section(source, 'code'):before_section(source, 'proof_aux')]
    return dict(row=row, signature=sig, imports=section(source, 'import')[2], public=public,
                declaration=declaration, requirements=requirements, takes_precondition='h_precond' in declaration,
                candidate={k: section(source, k)[2] for k in ('solution_aux', 'code_aux', 'code')},
                tests=json.loads((directory / 'test.json').read_text()),
                interface_sha256=sha((public + declaration).encode()),
                requirements_sha256=sha((requirements + (directory / 'test.json').read_text()).encode()))


def candidate_source(task: dict, candidate: dict) -> str:
    if set(candidate) != {'solution_aux', 'code_aux', 'code'}:
        raise ValueError('candidate must provide exactly the three declared implementation slots')
    # Defense in depth for this offline adapter. This is NOT an OS isolation boundary;
    # a production rollout still needs a sandbox which cannot read evaluator storage.
    for fragment in candidate.values():
        # Source comments are not Lean commands. String literals remain scanned conservatively.
        fragment = re.sub(r'(?m)^[ \t]*--[^\n]*$', '', fragment)
        if re.search(r'\b(sorry|admit|axiom|native_decide|unsafe|run_tac|elab|macro|syntax|initialize|import|namespace|end|set_option|instance|attribute|notation|infix|infixl|infixr|prefix|postfix|scoped|open|export|local|noncomputable|opaque|deriving|_root_|letI)\b|#|@\[', fragment):
            raise ValueError('unsupported candidate command or forbidden trust')
    sig = task['signature']; name = sig['name']
    params = ' '.join(f"({p['param_name']} : {p['param_type']})" for p in sig['parameters'])
    args = ' '.join(f"({p['param_name']})" for p in sig['parameters'])
    expected = f"{params} (h_precond : {name}_precond {args})"
    proof_arg = ' h_precond' if task['takes_precondition'] else ''
    return ('import Lean\n' + task['imports'] + '\nnamespace AdapterCandidate\n' +
            task['public'] + '\n' + candidate['solution_aux'] + '\n' + candidate['code_aux'] + '\n' +
            task['declaration'] + candidate['code'] + '\n' +
            f'def adapterInterface {expected} : {sig["return_type"]} := {name} {args}{proof_arg}\n' +
            f'#check {name}\n#print axioms {name}\n#print axioms adapterInterface\n' +
            'end AdapterCandidate\n')


def lean_literal(value, lean_type: str) -> str:
    if lean_type == 'String':
        if not isinstance(value, str):
            raise ValueError('String test value is not a string')
        return json.dumps(value, ensure_ascii=False)
    if isinstance(value, bool):
        return 'true' if value else 'false'
    if isinstance(value, (str, int)):
        return str(value)
    raise ValueError(f'unsupported Lean literal: {type(value).__name__}')


def endpoint_source(task: dict) -> str:
    sig = task['signature']; name = sig['name']
    # Requirements remain in an evaluator-only module, absent from the candidate module.
    text = 'import Candidate\nopen AdapterCandidate\nnamespace AdapterEvaluator\n'
    text += task['requirements'] + '\n'
    text += 'set_option maxRecDepth 100000\nset_option maxHeartbeats 2000000\n'
    for i, test in enumerate(task['tests']):
        args = ' '.join('(' + lean_literal(test['input'][p['param_name']], p['param_type']) + ')' for p in sig['parameters'])
        text += f'theorem input_{i}_valid : _root_.AdapterCandidate.{name}_precond {args} := by decide\n'
        text += f'#print axioms input_{i}_valid\n'
        # A measured false is a behavioral failure, not unsupported or missing.
        proof_arg = f' input_{i}_valid' if task['takes_precondition'] else ''
        text += f'def observed_{i} : _root_.Bool := (_root_.AdapterCandidate.{name} {args}{proof_arg}) == ({lean_literal(test["expected"], sig["return_type"])} : {sig["return_type"]})\n'
        text += f'#eval IO.println ("AT3598_TEST_{i}=" ++ toString observed_{i})\n'
    return text + 'end AdapterEvaluator\n'


def run_lean(command: list[str], cwd: Path, env: dict, log: Path, timeout: int) -> dict:
    try:
        result = subprocess.run(command, cwd=cwd, env=env, capture_output=True, timeout=timeout)
        rc, stdout, stderr = result.returncode, result.stdout, result.stderr
    except subprocess.TimeoutExpired as exc:
        rc, stdout, stderr = None, exc.stdout or b'', exc.stderr or b''
    log.with_suffix('.stdout.txt').write_bytes(stdout)
    log.with_suffix('.stderr.txt').write_bytes(stderr)
    return dict(returncode=rc, stdout=stdout.decode(errors='replace'), stderr=stderr.decode(errors='replace'),
                stdout_sha256=sha(stdout), stderr_sha256=sha(stderr))


def axioms_allowed(stdout: str, expected: int) -> bool:
    reports = re.findall(r"(?:depends on axioms:\s*\[([^\]]*)\]|does not depend on any axioms)", stdout)
    if len(reports) != expected:
        return False
    return all(not ({name.strip() for name in text.split(',') if name.strip()} - ALLOWED) for text in reports)


def evaluate(task: dict, candidate: dict, lean: Path, lean_path: str, out: Path, timeout: int = 60) -> dict:
    out.mkdir(parents=True, exist_ok=False)
    candidate_text = candidate_source(task, candidate)
    endpoint_text = endpoint_source(task)
    (out / 'Candidate.lean').write_text(candidate_text)
    # Do not materialize evaluator inputs until candidate elaboration is finished.
    env = dict(os.environ, LEAN_PATH=str(out.resolve()) + ':' + lean_path)
    compiled = run_lean([str(lean), '-o', 'Candidate.olean', 'Candidate.lean'], out, env, out / 'candidate', timeout)
    row = dict(task_id=task['row']['task_id'], candidate_sha256=sha(candidate_text.encode()),
               source_sha256=task['row']['file_sha256']['task.lean'],
               interface_sha256=task['interface_sha256'], requirements_sha256=task['requirements_sha256'],
               candidate_compile_rc=compiled['returncode'], n_tests=len(task['tests']),
               endpoint_supported=False, endpoint_status='candidate_compile_or_trust_failure',
               candidate_axioms_allowed=axioms_allowed(compiled['stdout'], 2),
               logs=str(out.resolve()))
    if compiled['returncode'] != 0 or not row['candidate_axioms_allowed']:
        return row
    (out / 'Endpoint.lean').write_text(endpoint_text)
    result = run_lean([str(lean), 'Endpoint.lean'], out, env, out / 'endpoint', timeout)
    measurements = re.findall(r'^AT3598_TEST_(\d+)=(true|false)$', result['stdout'], re.M)
    complete = [int(i) for i, _ in measurements] == list(range(len(task['tests'])))
    witnesses = axioms_allowed(result['stdout'], len(task['tests']))
    supported = result['returncode'] == 0 and complete and witnesses and bool(task['tests'])
    row.update(endpoint_rc=result['returncode'], endpoint_supported=supported,
               endpoint_status='measured' if supported else 'endpoint_infrastructure_or_requirement_failure',
               nonvacuity_witnesses_allowed=witnesses,
               behavioral_tests=[dict(index=int(i), passed=v == 'true') for i, v in measurements],
               n_passed=sum(v == 'true' for _, v in measurements) if supported else None,
               endpoint_sha256=sha(endpoint_text.encode()))
    return row


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--manifest', type=Path, required=True); p.add_argument('--verina-root', type=Path, required=True)
    p.add_argument('--lean', type=Path, required=True); p.add_argument('--lean-path', required=True)
    p.add_argument('--out', type=Path, required=True); p.add_argument('--timeout', type=int, default=60)
    a = p.parse_args()
    manifest = json.loads(a.manifest.read_text())
    if manifest.get('manifest_kind') != 'VERINA_external24_screened_candidate_v1' or len(manifest['tasks']) != 24:
        raise ValueError('expected the frozen real 24-task panel')
    a.out.mkdir(parents=True, exist_ok=False)
    version = subprocess.check_output([str(a.lean), '--version'], text=True).strip()
    if 'version 4.22.0,' not in version:
        raise ValueError('requires pinned Lean 4.22.0')
    receipt = dict(date='11-25-2026', started_at=datetime.now(timezone.utc).isoformat(),
                   manifest_sha256=sha(a.manifest.read_bytes()), source_commit=manifest['source']['commit'],
                   adapter_sha256=sha(Path(__file__).read_bytes()), lean_version=version,
                   scope='real source implementation slots; fixed behavioral tests plus kernel-checked input witnesses; no reference proof acceptance, no DT',
                   rows=[])
    for r in manifest['tasks']:
        t = load_task(a.verina_root, r)
        receipt['rows'].append(evaluate(t, t['candidate'], a.lean, a.lean_path, a.out / r['task_id'], a.timeout))
        print(r['task_id'], receipt['rows'][-1]['endpoint_status'], flush=True)
        (a.out / 'receipt.json').write_text(json.dumps(receipt, indent=2) + '\n')
    receipt.update(finished_at=datetime.now(timezone.utc).isoformat(), n_declared=24,
                   n_supported=sum(r['endpoint_supported'] for r in receipt['rows']))
    (a.out / 'receipt.json').write_text(json.dumps(receipt, indent=2) + '\n')
    print(json.dumps({k:receipt[k] for k in ('n_declared','n_supported')}))
    return 0 if receipt['n_supported'] == 24 else 1


if __name__ == '__main__':
    raise SystemExit(main())
