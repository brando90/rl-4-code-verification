#!/usr/bin/env python3
"""TLDR: Smooth scorer entry for Exp 25 that makes smooth d independent of where the job dir lives: stage the job dir at a real path of one fixed length, run Exp 20's partial_credit_e20.py on it, and write the results as if run on the original job dir.
Why: the frozen scorer (pin 59059a20, bytes hash-checked) keeps only COMPILE_LOG_CAP = 4000 chars of the Lean log and every diagnostic line carries the absolute source path, so which errors survive (and so d) depends on the job-dir path length. declaration_adapter resolves symlinks, so a symlink does not work; a copy does. Default length 66 = Sherlock's Exp 20 phase-0 job dir (/scratch/users/brando9/rl4cv_sherlock/e20/phase0/jobs/e20_p0_c0_s3), which reproduces the saved Exp 20 values.
Use: same CLI as partial_credit_e20.py, in its place in train_e25.py; run from ROOT/code (needs partial_credit_e20.py beside it and E20_GRADING set). Env: E25_FIXEDPATH_BASE (default /tmp/e25_fixedpath), E25_FIXEDPATH_LEN (default 66).
Example: python3.12 partial_credit_fixedpath.py --job-dir <job-dir> --out <out>/partial_<name>.json --evidence-root <out>/compiler_diagnostics
"""
from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import uuid
from pathlib import Path

HERE = Path(__file__).resolve().parent
TARGET_LEN = int(os.environ.get("E25_FIXEDPATH_LEN", "66"))
BASE = Path(os.environ.get("E25_FIXEDPATH_BASE", "/tmp/e25_fixedpath"))


def staged_path() -> Path:
    token = uuid.uuid4().hex[:10]
    pad = TARGET_LEN - len(str(BASE)) - 1 - len(token)
    if pad < 0:
        raise SystemExit(f"E25_FIXEDPATH_BASE too long for E25_FIXEDPATH_LEN={TARGET_LEN}")
    return BASE / ("_" * pad + token)


def arg(argv: list[str], flag: str) -> str:
    return argv[argv.index(flag) + 1]


def main(argv: list[str]) -> int:
    job_dir = Path(arg(argv, "--job-dir")).resolve()
    out = Path(arg(argv, "--out"))
    staged = staged_path()
    BASE.mkdir(parents=True, exist_ok=True)
    shutil.copytree(job_dir, staged, symlinks=False)
    assert len(str(staged)) == TARGET_LEN
    args = list(argv)
    args[args.index("--job-dir") + 1] = str(staged)
    cmd = [sys.executable, str(HERE / "partial_credit_e20.py"), *args]
    try:
        rc = subprocess.call(cmd)
        if rc == 0 and out.is_file():
            data = json.loads(out.read_text())
            data["scored_job_dir"] = str(staged)
            data["job_dir"] = str(job_dir)
            data["fixed_job_dir_len"] = TARGET_LEN
            out.write_text(json.dumps(data, indent=1))
        return rc
    finally:
        shutil.rmtree(staged, ignore_errors=True)


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
