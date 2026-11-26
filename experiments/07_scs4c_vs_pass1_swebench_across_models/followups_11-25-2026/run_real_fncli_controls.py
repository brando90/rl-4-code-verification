"""Run real gold-repeat/base D_gold controls for the pinned OpenLibrary FnToCLI task on fixed generated CLI inputs."""

from __future__ import annotations

import argparse
import contextlib
import hashlib
import importlib.util
import io
import json
from pathlib import Path
import platform
import random
import subprocess
import sys
import time
import urllib.request

from d_gold_controls import check_task
from prepare_phase_b import SHA256

TASK_SUBSTRING = "6afdb09df692223c3a31df65cfa92f15e5614c01"
MODULE = "scripts/solr_builder/solr_builder/fn_to_cli.py"


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write_new(path: Path, data) -> None:
    with path.open("x") as stream:
        stream.write(json.dumps(data, indent=2, allow_nan=False) + "\n")


def generated_inputs(seed=20261125) -> list[dict]:
    """Generate boundary cases and seeded fuzz inputs without observing base or gold outputs."""
    cases = []
    for value in (-1000000, -1, 0, 1, 2, 1000000):
        for operation in ("scalar", "async_scalar"):
            cases.append({"operation": operation, "argv": [str(value)], "source": "boundary"})
    for values in ([], ["0"], ["-1", "0", "1"], ["1000000", "-1000000"]):
        cases.append({"operation": "list_int", "argv": values, "source": "boundary"})
    for values in ([], ["."], ["a/b", "c.txt"], ["/tmp/example", "../relative"]):
        cases.append({"operation": "list_path", "argv": values, "source": "boundary"})
    rng = random.Random(seed)
    for _ in range(236):
        operation = rng.choice(("scalar", "async_scalar", "list_int", "list_path"))
        if operation in ("scalar", "async_scalar"):
            args = [str(rng.randrange(-10**6, 10**6))]
        elif operation == "list_int":
            args = [str(rng.randrange(-1000, 1000)) for _ in range(rng.randrange(0, 9))]
        else:
            args = [f"dir{rng.randrange(12)}/file{rng.randrange(100)}.txt" for _ in range(rng.randrange(0, 9))]
        cases.append({"operation": operation, "argv": args, "source": "seeded_fuzz"})
    return [{"input_id": f"fncli-{i:04d}", **c} for i, c in enumerate(cases)]


def observe(module, case: dict) -> dict:
    """Invoke the real class with typed callback/argv inputs; callbacks neither read nor modify files."""
    def scalar(number: int):
        return number * 2

    async def async_scalar(number: int):
        return number * 2

    def list_int(numbers: list[int]):
        return sum(numbers)

    def list_path(paths: list[Path]):
        return [str(p) for p in paths]

    callbacks = {"scalar": scalar, "async_scalar": async_scalar, "list_int": list_int, "list_path": list_path}
    original_argv = sys.argv
    stdout, stderr = io.StringIO(), io.StringIO()
    try:
        sys.argv = ["fncli-dgold", *case["argv"]]
        with contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr):
            # Use the old shared no-argument API, so the witness is behavioral, not a changed signature.
            result = module.FnToCLI(callbacks[case["operation"]]).run()
        json.dumps(result, allow_nan=False)
        return {"kind": "value", "value": result, "stdout": stdout.getvalue(), "stderr": stderr.getvalue()}
    except (Exception, SystemExit) as exc:
        return {"kind": "exception", "type": f"{type(exc).__module__}.{type(exc).__qualname__}",
                "message": str(exc), "stdout": stdout.getvalue(), "stderr": stderr.getvalue()}
    finally:
        sys.argv = original_argv


def worker(module_path: Path, inputs: Path, out: Path) -> None:
    spec = importlib.util.spec_from_file_location("real_fn_to_cli", module_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    cases = json.loads(inputs.read_text())["inputs"]
    write_new(out, {c["input_id"]: observe(module, c) for c in cases})


def prepare(dataset: Path, work: Path) -> dict:
    if sha(dataset) != SHA256:
        raise ValueError("benchmark dataset differs from the pinned public release")
    row = next(r for r in map(json.loads, dataset.read_text().splitlines()) if TASK_SUBSTRING in r["instance_id"])
    work.mkdir(parents=True, exist_ok=False)
    inputs = work / "inputs_11-25-2026.json"
    write_new(inputs, {"date": "11-25-2026", "seed": 20261125,
                       "written_before_first_control_execution_unix": time.time(), "inputs": generated_inputs()})
    url = f"https://raw.githubusercontent.com/{row['repo']}/{row['base_commit']}/{MODULE}"
    source = urllib.request.urlopen(url, timeout=30).read()
    paths = {}
    for name in ("base", "gold"):
        path = work / name / MODULE
        path.parent.mkdir(parents=True)
        path.write_bytes(source)
        paths[name] = path
    patch = work / "gold.patch"
    patch.write_text(row["patch"])
    changed = [line[6:] for line in row["patch"].splitlines() if line.startswith("+++ b/")]
    if changed != [MODULE]:
        raise ValueError("unexpected gold patch paths")
    completed = subprocess.run(["patch", "--batch", "--fuzz=0", "-p1", "-i", str(patch.resolve())],
                               cwd=work / "gold", capture_output=True, text=True, timeout=30)
    write_new(work / "patch_application_11-25-2026.json",
              {"exit_code": completed.returncode, "stdout": completed.stdout, "stderr": completed.stderr})
    completed.check_returncode()
    record = {"date": "11-25-2026", "task_id": row["instance_id"], "repo": row["repo"],
              "base_commit": row["base_commit"], "source_url": url, "base_source_sha256": sha(paths["base"]),
              "gold_source_sha256": sha(paths["gold"]), "gold_patch_sha256": sha(patch),
              "input_sha256": sha(inputs), "inputs": len(generated_inputs()), "python": platform.python_version(),
              "scope": "Full real stdlib FnToCLI module; property/fuzz controls only; no whole-repository gate or solver generation"}
    write_new(work / "prepared_11-25-2026.json", record)
    return record


def run(dataset: Path, work: Path, out: Path):
    record = prepare(dataset, work)
    inputs = work / "inputs_11-25-2026.json"
    runs, execution = {}, {}
    for name in ("gold", "gold_repeat", "base"):
        module = work / ("base" if name == "base" else "gold") / MODULE
        receipt = work / (name + "_observations.json")
        command = [sys.executable, str(Path(__file__).resolve()), "--worker", "--module", str(module.resolve()),
                   "--inputs", str(inputs.resolve()), "--out", str(receipt.resolve())]
        started = time.time()
        completed = subprocess.run(command, capture_output=True, text=True, timeout=60)
        execution[name] = {"command": command, "exit_code": completed.returncode, "stdout": completed.stdout,
                           "stderr": completed.stderr, "elapsed_seconds": time.time() - started}
        completed.check_returncode()
        runs[name] = json.loads(receipt.read_text())
    result = check_task([r["input_id"] for r in json.loads(inputs.read_text())["inputs"]], runs)
    record.update(controls=result, execution=execution,
                  observations={name: {"sha256": sha(work / (name + "_observations.json")),
                                       "values": sum(v["kind"] == "value" for v in observations.values()),
                                       "exceptions": sum(v["kind"] == "exception" for v in observations.values())}
                                for name, observations in runs.items()},
                  cpu_only=True, gpu_jobs=[], model_calls=0,
                  whole_repository_install_import_gate="unmeasured", phase_b_admitted=False)
    write_new(out, record)
    print(json.dumps(record, indent=2))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--worker", action="store_true")
    parser.add_argument("--module", type=Path)
    parser.add_argument("--inputs", type=Path)
    parser.add_argument("--dataset", type=Path)
    parser.add_argument("--work", type=Path)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    if args.worker:
        worker(args.module, args.inputs, args.out)
    else:
        run(args.dataset, args.work, args.out)
