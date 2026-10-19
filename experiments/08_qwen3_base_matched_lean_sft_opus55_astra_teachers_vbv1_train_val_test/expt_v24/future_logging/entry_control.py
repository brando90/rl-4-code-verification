"""Run the future coordinator's exact mandatory scorer command on a tiny fixture."""
import json
import os
from pathlib import Path
import shutil
import subprocess
import time

import parallel_scoring_logged as future
from durable_capture import atomic, sha


def main():
    root = future.RUN/'future_logging_v24_controls/entry'
    root.mkdir(parents=True, exist_ok=False)
    # Copy metadata into an explicitly labelled control, never overwrite an
    # original agent file or record this fixture as a benchmark measurement.
    partition = json.loads((future.RUN/'corpus_training_v23/scoring_parallel_v1/partition.json').read_text())
    original = partition['cells'][0]
    job = root/'job'
    job.mkdir()
    shutil.copytree(Path(original['job'])/original['td'], job/original['td'])
    lean = next((job/original['td']).glob('verifier/solution.lean'))
    lean.write_text('theorem logging_control : True := True.intro\nexample : True := True.intro\n')
    cell = dict(key='logging_control_not_a_model_measurement', job=str(job))
    destination = root/'result'
    destination.mkdir()
    command = future.scorer_command(cell, destination,
        future.REPO/'external/veribench_scorer/veribench_dataset/lean_src/veribench', future.RUN/'grading')
    env = dict(os.environ, CUDA_VISIBLE_DEVICES='', PATH=str(future.RUN/'bin')+':'+os.environ['PATH'])
    with (root/'scorer.log').open('x') as stream:
        completed = subprocess.run(command, cwd=future.REPO, env=env,
            stdout=stream, stderr=subprocess.STDOUT, check=False, timeout=90)
    assert completed.returncode == 0
    evidence = destination/'compiler_diagnostics'
    launcher = json.loads((evidence/'launcher.json').read_text())
    assert launcher['state'] == 'COMPLETE' and launcher['exit_code'] == 0
    calls = [json.loads(p.read_text()) for p in evidence.glob('call_*/execution.json')]
    assert {row['stage'] for row in calls} == {'initial_compile','kernel_compile','kernel_inspect'}
    assert all(row['state'] == 'COMPLETE' and row['exit_code'] == 0 for row in calls)
    assert all(any(source['sha256'] == sha(lean) for source in row['context']['evaluated_sources'].values()) for row in calls)
    atomic(root/'control.json', dict(status='PASS', scope='Logging fixture only, not a model or benchmark measurement',
        exact_future_coordinator_default_command_used=True, command=command,
        coordinator_source_sha256=sha(future.__file__), launcher_source_sha256=sha(future.HERE/'logged_scorer.py'),
        capture_source_sha256=sha(future.HERE/'durable_capture.py'),
        all_three_actual_compiler_stages_logged=True, exit_code=completed.returncode,
        model_calls=0, historical_files_changed=False, observed_unix=time.time()))
    print((root/'control.json').read_text())


if __name__ == '__main__':
    main()
