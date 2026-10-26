"""Future scorer entry point: unchanged frozen verifier plus durable diagnostics."""
import argparse
import importlib.util
import json
from pathlib import Path
import sys
import time

from durable_capture import DurableCapture, atomic, instrument_scorer, sha

HERE = Path(__file__).resolve().parent
FROZEN_HELPERS = HERE.parent.parent/'expt_v20'
sys.path.insert(0, str(FROZEN_HELPERS))
import parallel_score_cache


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--scorer', type=Path, required=True)
    parser.add_argument('--evidence-root', type=Path, required=True)
    parser.add_argument('--lean-executable', type=Path, required=True)
    args, forwarded = parser.parse_known_args()
    if forwarded[:1] == ['--']:
        forwarded = forwarded[1:]
    spec = importlib.util.spec_from_file_location('future_logged_frozen_cli', args.scorer)
    cli = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = cli
    spec.loader.exec_module(cli)
    parallel_score_cache.assert_frozen_scorer(cli.S)
    job = Path(forwarded[forwarded.index('--job-dir')+1]).resolve()
    tasks = cli.S.discover_agent_tasks(str(job))
    source_identity = {task:dict(path=str(Path(path).resolve()), sha256=sha(path)) for task, path in tasks.items()}
    capture = DurableCapture(args.evidence_root, args.lean_executable, dict(
        evaluated_sources=source_identity, job_dir=str(job),
        scorer_sha256=sha(cli.S.__file__), kernel_sha256=sha(cli.S.kernel_axioms.__file__),
        cli_sha256=sha(args.scorer)))
    changes = instrument_scorer(cli.S, capture)
    receipt = dict(state='READY', observed_unix=time.time(),
        entry_source_sha256=sha(__file__), capture_source_sha256=sha(HERE/'durable_capture.py'),
        scorer_path=str(args.scorer.resolve()), scorer_sha256=sha(cli.S.__file__),
        kernel_sha256=sha(changes['original_kernel'].__file__), cli_sha256=sha(args.scorer),
        argv=forwarded, evaluated_sources=source_identity, compiler=capture.compiler,
        compile_bytecode_unchanged=True, kernel_probe_bytecode_unchanged=True,
        kernel_check_bytecode_unchanged=True,
        amendment='stdout/stderr transport changes from PIPE to persistent regular files; identical command arguments, timeout, exit code and frozen proof policy.')
    atomic(capture.root/'launcher.json', receipt)
    original_argv = sys.argv
    try:
        sys.argv = [str(args.scorer), *forwarded]
        status = cli.main()
        receipt.update(state='COMPLETE', exit_code=status, ended_unix=time.time())
        atomic(capture.root/'launcher.json', receipt)
        return status
    except BaseException as exc:
        receipt.update(state='RAISED', error=type(exc).__name__+': '+str(exc), ended_unix=time.time())
        atomic(capture.root/'launcher.json', receipt)
        raise
    finally:
        sys.argv = original_argv


if __name__ == '__main__':
    raise SystemExit(main())
