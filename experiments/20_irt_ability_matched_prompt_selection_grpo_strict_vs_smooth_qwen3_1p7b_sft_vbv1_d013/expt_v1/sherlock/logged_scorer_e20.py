"""TLDR: Experiment 20's scoring entry on Sherlock under repo decision D-109: run VeriBench's frozen scorer (pin 59059a2, score_scsc.py --skip-tc) unchanged, but with experiment 08 expt_v24's durable compiler capture, so every Lean compile and kernel call keeps its stdout/stderr, source snapshot, compiler identity, timeout/partial output and exit status under --evidence-root; the frozen scorer bytes are checked against their pinned SHA-256 before anything runs (a port of expt_v24/future_logging/logged_scorer.py whose only change is this inline byte check instead of expt_v20's parallel_score_cache helper)."""
import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import sys
import time

sys.path.insert(0, str(Path(__file__).resolve().parent))
from durable_capture import DurableCapture, atomic, instrument_scorer, sha  # noqa: E402

# rl4cv external/deps.lock.json veribench_scorer 59059a2 (same hashes as experiment 08's setup_grading.sbatch byte check).
FROZEN = {
    "run_real_eval.py": "6e82b3d1cd6d3686aaec3d45f273cd902b03b962c0c2eca48f2c2b4f25f41fa9",
    "kernel_axioms.py": "5dbbdcae75ba8b22911fcb43ab1fcde45a1475cf92742a39a29ebe41116de287",
    "score_scsc.py": "b3713c48e0fdb24adec93b77be8785d20e48897ee8d1fd8ce31fdf37101e81d6",
}


def assert_frozen(paths: dict) -> dict:
    seen = {name: hashlib.sha256(Path(p).read_bytes()).hexdigest() for name, p in paths.items()}
    bad = {n: (seen[n], FROZEN[n]) for n in FROZEN if seen.get(n) != FROZEN[n]}
    if bad:
        raise RuntimeError(f"frozen scorer bytes differ from pin 59059a2: {bad}")
    return seen


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--scorer', type=Path, required=True, help='score_scsc.py of the pinned scorer')
    parser.add_argument('--evidence-root', type=Path, required=True)
    parser.add_argument('--lean-executable', type=Path, required=True)
    args, forwarded = parser.parse_known_args()
    if forwarded[:1] == ['--']:
        forwarded = forwarded[1:]
    spec = importlib.util.spec_from_file_location('e20_logged_frozen_cli', args.scorer)
    cli = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = cli
    spec.loader.exec_module(cli)
    hashes = assert_frozen({"run_real_eval.py": cli.S.__file__, "kernel_axioms.py": cli.S.kernel_axioms.__file__,
                            "score_scsc.py": args.scorer})
    job = Path(forwarded[forwarded.index('--job-dir') + 1]).resolve()
    tasks = cli.S.discover_agent_tasks(str(job))
    source_identity = {task: dict(path=str(Path(path).resolve()), sha256=sha(path)) for task, path in tasks.items()}
    capture = DurableCapture(args.evidence_root, args.lean_executable, dict(
        evaluated_sources=source_identity, job_dir=str(job), scorer_sha256=hashes["run_real_eval.py"],
        kernel_sha256=hashes["kernel_axioms.py"], cli_sha256=hashes["score_scsc.py"], experiment="20", decision="D-109"))
    changes = instrument_scorer(cli.S, capture)
    receipt = dict(state='READY', observed_unix=time.time(), entry_source_sha256=sha(__file__),
                   capture_source_sha256=sha(Path(__file__).resolve().parent / 'durable_capture.py'),
                   scorer_path=str(args.scorer.resolve()), frozen_sha256=hashes, argv=forwarded,
                   evaluated_sources=source_identity, compiler=capture.compiler, **{k: v for k, v in changes.items() if k.endswith('unchanged')},
                   amendment='stdout/stderr transport changes from PIPE to persistent regular files; identical command arguments, timeout, exit code and frozen proof policy.')
    atomic(capture.root / 'launcher.json', receipt)
    original_argv = sys.argv
    try:
        sys.argv = [str(args.scorer), *forwarded]
        status = cli.main()
        receipt.update(state='COMPLETE', exit_code=status, ended_unix=time.time())
        atomic(capture.root / 'launcher.json', receipt)
        return status
    except BaseException as exc:
        receipt.update(state='RAISED', error=type(exc).__name__ + ': ' + str(exc), ended_unix=time.time())
        atomic(capture.root / 'launcher.json', receipt)
        raise
    finally:
        sys.argv = original_argv


if __name__ == '__main__':
    raise SystemExit(main())
