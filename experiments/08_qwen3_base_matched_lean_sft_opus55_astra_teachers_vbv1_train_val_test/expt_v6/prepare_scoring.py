"""Verify frozen scorer bytes and exercise positive, compilation-error and sorry controls with cached Lean imports."""
from __future__ import annotations

import csv
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[2]
RUN = Path(os.environ["TINY_RUN_ROOT"])
sys.path.insert(0, str(REPO / "src"))
sys.path.insert(0, str(HERE.parent / "expt_v1/scripts"))


def main():
    from rl4cv.veribench.jobs import materialize_jobs
    from score_teacher_files import FROZEN_SHA256

    scorer = REPO / "external/veribench_scorer"
    frozen = {}
    for relative, expected in FROZEN_SHA256.items():
        actual = hashlib.sha256((scorer / relative).read_bytes()).hexdigest()
        assert actual == expected, relative
        frozen[relative] = actual
    grade = Path("/lfs/skampere1/0/brando9/rl4cv_e08/grading/lean_src")
    lean_bin = Path("/lfs/skampere1/0/brando9/.elan/toolchains/leanprover--lean4---v4.22.0/bin/lean")
    assert "v4.22.0" in (grade / "lean-toolchain").read_text()
    local_grade = RUN / "grading"
    local_grade.mkdir(exist_ok=True)
    for name in ("lakefile.toml", "lakefile.lean", "lake-manifest.json", "lean-toolchain"):
        if (grade / name).is_file():
            shutil.copy2(grade / name, local_grade / name)
    imports = [p / ".lake/build/lib/lean" for p in (grade / ".lake/packages").iterdir() if p.is_dir()]
    imports += [grade / ".lake/build/lib/lean"]
    lean_path = ":".join(str(p) for p in imports if p.is_dir())
    # The verifier is unchanged. Resolve `lake env lean` to the same pinned binary and
    # cached import directories without letting Lake mutate another owner's packages.
    binary = RUN / "bin/lake"
    binary.parent.mkdir(exist_ok=True)
    binary.write_text("#!/usr/bin/python3\n"
        "import os,sys\n"
        "if sys.argv[1:3] != ['env','lean']: raise SystemExit('unsupported lake invocation')\n"
        f"env=os.environ.copy();env['LEAN_PATH']={lean_path!r}\n"
        f"os.execve({str(lean_bin)!r},[{str(lean_bin)!r},'-j','1']+sys.argv[3:],env)\n")
    binary.chmod(0o755)
    control = RUN / "scorer_controls"
    control.mkdir(exist_ok=True)
    train_id = (HERE.parent / "expt_v1/results/split/vbv1_train_task_ids.txt").read_text().splitlines()[0]
    positive = (RUN / "curriculum/examples/tiny_natural_arithmetic_01/Solution.lean").read_text()
    assert "\nexample :" in positive
    negative = "import Mathlib\nexample : 1 = 2 := by rfl\n"
    dishonest = positive.replace("\nend Tiny\n", "\ntheorem spec_bad : False := by sorry\nend Tiny\n")
    raw = [{"task_id": train_id, "sample_idx": k, "model": "deterministic-control", "lean": text,
        "finish_reason": "stop", "measured": True, "extraction": "control", "generated_tokens": 0}
        for k, text in enumerate((positive, negative, dishonest))]
    jobs = materialize_jobs(raw, control / "jobs", "control")
    pack = control / "pack" / train_id
    pack.mkdir(parents=True, exist_ok=True)
    shutil.copy2(REPO / "external/veribench/vb_harbor/adapter/template/task.toml", pack / "task.toml")
    env = os.environ.copy()
    env.update(CUDA_VISIBLE_DEVICES="", PATH=str(binary.parent) + ":" + env["PATH"])
    results = []
    for sample, job in jobs.items():
        out = control / "scores" / str(sample)
        command = [sys.executable, str(scorer / "experiments/71_E2_valkyrie_harbor_vals_ai_eval_code/scripts/score_scsc.py"),
            "--job-dir", str(job), "--pack", str(pack.parent), "--name", f"control_{sample}",
            "--gold-dir", str(scorer / "veribench_dataset/lean_src/veribench"),
            "--lake-dir", str(local_grade), "--skip-tc", "--out-dir", str(out)]
        with (control / f"sample_{sample}.log").open("w") as log:
            result = subprocess.run(command, env=env, stdout=log, stderr=subprocess.STDOUT, timeout=300)
        assert result.returncode == 0, f"control {sample} failed; see log"
        path = next(out.glob("*_per_task.csv"))
        records = list(csv.DictReader(path.open()))
        assert len(records) == 1
        results.append(records[0])
    def number(row, key):
        return float(row.get(key) or 0)
    assert number(results[0], "IC_ap") == 1 and number(results[0], "IC_pp") == 1
    assert number(results[1], "IC_ap") == 0
    assert number(results[2], "kernel_n_sorry_ax") >= 1 and number(results[2], "IC_pp") < 1
    receipt = {"status": "PASS", "frozen_bytes": frozen, "controls": results,
        "lean_binary": str(lean_bin), "lean_binary_sha256": hashlib.sha256(lean_bin.read_bytes()).hexdigest(),
        "lake_adapter_sha256": hashlib.sha256(binary.read_bytes()).hexdigest(),
        "lean_path": lean_path, "compiler_threads": 1,
        "operational_change": "same Lean 4.22.0 and cached Mathlib imports; no Lake package refresh"}
    (RUN / "scoring_preflight.json").write_text(json.dumps(receipt, indent=2) + "\n")
    print(json.dumps({"status": "PASS", "controls": 3, "frozen_scorer_bytes_verified": True}), flush=True)


if __name__ == "__main__":
    main()
