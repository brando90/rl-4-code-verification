"""Actual Lean parity, timeout partial streams, and killed-owner log survival."""
import argparse
import dataclasses
import importlib.util
import json
import os
from pathlib import Path
import signal
import subprocess
import sys
import tempfile
import time

from durable_capture import DurableCapture, REAL_RUN, atomic, instrument_scorer, sha

HERE = Path(__file__).resolve().parent
RUN = Path('/lfs/skampere1/0/eth127/rl4cv_tiny_training')
SCORER = RUN/'repo/external/veribench_scorer/experiments/71_E2_valkyrie_harbor_vals_ai_eval_code/scripts/score_scsc.py'
LEAN = Path('/lfs/skampere1/0/brando9/.elan/toolchains/leanprover--lean4---v4.22.0/bin/lean')


def timeout_output(call):
    try:
        call()
    except subprocess.TimeoutExpired as error:
        return dict(timeout=error.timeout, stdout=error.stdout, stderr=error.stderr)
    raise AssertionError('Timeout control unexpectedly completed')


def main(root):
    root.mkdir(parents=True, exist_ok=True)
    spec = importlib.util.spec_from_file_location('logging_controls_frozen_cli', SCORER)
    cli = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = cli
    spec.loader.exec_module(cli)
    S = cli.S
    grading = str(RUN/'grading')
    good = root/'Good.lean'
    bad = root/'Bad.lean'
    good.write_text('theorem tiny_identity : (1 : Nat) = 1 := rfl\n')
    bad.write_text('def broken : Nat := definitelyUnknownControlName\n')
    before_good = dataclasses.asdict(S.compile_lean_file(str(good), grading))
    before_bad = dataclasses.asdict(S.compile_lean_file(str(bad), grading))
    before_kernel = S.kernel_axioms.check_file(str(good), grading).to_dict()
    assert before_good['success'] and not before_bad['success'] and before_kernel['probe_ok']
    capture = DurableCapture(root/'lean_evidence', LEAN, dict(control=True))
    instrument_scorer(S, capture)
    assert dataclasses.asdict(S.compile_lean_file(str(good), grading)) == before_good
    assert dataclasses.asdict(S.compile_lean_file(str(bad), grading)) == before_bad
    after_kernel = S.kernel_axioms.check_file(str(good), grading).to_dict()
    fields = ('probe_ok','probe_rc','allow_native_decide','n_stated','n_phantom','n_theorems',
        'n_honest','n_sorry_ax','n_native_decide','n_declared_axiom','n_unknown','ic_pp',
        'theorems','declared_axioms','extra_theorems','probe_errors','compile_rc','inspect_rc',
        'source_sha256','compiled_module_sha256','compiled_module')
    assert {k:before_kernel[k] for k in fields} == {k:after_kernel[k] for k in fields}
    evidence = [json.loads(path.read_text()) for path in (root/'lean_evidence').glob('call_*/execution.json')]
    assert {row['stage'] for row in evidence} == {'initial_compile','kernel_compile','kernel_inspect'}
    assert sorted(row['exit_code'] for row in evidence if row['stage'] == 'initial_compile') == [0,1]
    assert all(row['compiler']['sha256'] == sha(LEAN) and row['sources'] for row in evidence)
    # Original kernel helper deletes its temporary directory; the captured source
    # snapshots and both raw streams must remain independently readable.
    assert after_kernel['evidence_dir'] is None
    for row in evidence:
        if row['stage'].startswith('kernel'):
            assert any(not Path(source['path']).exists() for source in row['sources']) or row['stage'] == 'kernel_compile'
    for folder in (root/'lean_evidence').glob('call_*'):
        row = json.loads((folder/'execution.json').read_text())
        assert sha(folder/'stdout.log') == row['stdout_sha256']
        assert sha(folder/'stderr.log') == row['stderr_sha256']
        assert all(sha(folder/source['snapshot']) == source['sha256'] for source in row['sources'])
    python_capture = DurableCapture(root/'process_evidence', sys.executable, dict(control=True))
    parity_command = [sys.executable, '-c', 'import sys;sys.stdout.buffer.write(b"a\\r\\nb\\rc\\n");sys.stderr.buffer.write(b"err\\r\\n")']
    ordinary = REAL_RUN(parity_command, capture_output=True, text=True, check=False)
    logged = python_capture.run_logged(parity_command, capture_output=True, text=True, check=False)
    assert (ordinary.returncode,ordinary.stdout,ordinary.stderr) == (logged.returncode,logged.stdout,logged.stderr)
    timeout_command = [sys.executable, '-c', 'import sys,time;print("before-timeout",flush=True);print("error-before-timeout",file=sys.stderr,flush=True);time.sleep(10)']
    ordinary_timeout = timeout_output(lambda:REAL_RUN(timeout_command, capture_output=True, text=True, timeout=.25, check=False))
    logged_timeout = timeout_output(lambda:python_capture.run_logged(timeout_command, capture_output=True, text=True, timeout=.25, check=False))
    assert ordinary_timeout == logged_timeout
    timeout_records = [json.loads(path.read_text()) for path in (root/'process_evidence').glob('call_*/execution.json')]
    timeout_record = next(row for row in timeout_records if row['state'] == 'TIMEOUT')
    assert timeout_record['timed_out'] and timeout_record['stdout_bytes'] and timeout_record['stderr_bytes']
    kill_root = root/'killed_owner_evidence'
    child = subprocess.Popen([sys.executable, str(__file__), '--kill-fixture', str(kill_root)], start_new_session=True)
    deadline = time.monotonic()+15
    found = None
    while time.monotonic() < deadline:
        found = next((p for p in kill_root.glob('call_*/stdout.log') if p.stat().st_size), None)
        if found:
            break
        if child.poll() is not None:
            raise AssertionError('Killed-owner fixture exited before writing')
        time.sleep(.02)
    assert found is not None
    os.killpg(child.pid, signal.SIGKILL)
    child.wait(timeout=10)
    assert b'survives-owner-death' in found.read_bytes()
    assert b'stderr-survives' in (found.parent/'stderr.log').read_bytes()
    killed_record = json.loads((found.parent/'execution.json').read_text())
    assert killed_record['state'] == 'RUNNING' and killed_record['exit_code'] is None
    receipt = dict(status='PASS', actual_lean_positive_and_error_parity=True,
        actual_kernel_policy_and_theorem_report_parity=True, original_function_bytecode_unchanged=True,
        kernel_temp_directory_deleted_logs_and_source_snapshots_survive=True,
        text_newline_capture_interface_parity=True, timeout_partial_stream_interface_parity=True,
        killed_owner_partial_stream_survival=True, killed_owner_exit_not_fabricated=True,
        compiler_path=str(LEAN), compiler_sha256=sha(LEAN), controls_source_sha256=sha(__file__),
        capture_source_sha256=sha(HERE/'durable_capture.py'), model_calls=0, historical_verdicts_changed=False,
        observed_unix=time.time())
    atomic(root/'controls.json', receipt)
    print(json.dumps(receipt, indent=2))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path)
    parser.add_argument('--kill-fixture', type=Path)
    args = parser.parse_args()
    if args.kill_fixture:
        capture = DurableCapture(args.kill_fixture, sys.executable, dict(control=True))
        capture.run_logged([sys.executable,'-c','import sys,time;print("survives-owner-death",flush=True);print("stderr-survives",file=sys.stderr,flush=True);time.sleep(30)'],capture_output=True,text=True,timeout=60,check=False)
    else:
        assert args.root is not None
        main(args.root)
