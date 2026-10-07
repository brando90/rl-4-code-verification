#!/usr/bin/env python3
"""TLDR: Build the Harbor-style task pack the collect-only Valkyrie service serves (one dir per declared task plus the preflight task: instruction.md, tests/test.sh, task.toml) from the hash-recorded agent-spec v6 adapter bytes, and record every prompt hash (experiment 02A v3 PROTOCOL § 3; zero model calls)."""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import os
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[5]
sys.path.insert(0, str(REPO_ROOT / "src"))

ADAPTER_COMMIT = "85fd329c6946dcd14742aef9ea430c3491a1a366"   # VeriBench; adapter unchanged through 546b19fde (last touch before v7 at 631bcacb0)
ADAPTER_FILES_SHA256 = {
    "adapter.py": "a129b20a820113526a7c4db32094b2450afab6e42b94099649f4a85d7cb2a24f",
    "completion_contract.py": "7acf52e5e61a564e3d96b01e60ed014766bf6f73fc1ca6927c57f121cf7dd33e",
    "template/test.sh": "c83131ba6b54b638d9c24364cb2a27816321e8397891a95829da9ace60ffc41c",
    "template/task.toml": "e75c7ad00e6eee92fcfaeef408e5fc323cddf4b303b2cb5f8b0bf9c838e314e2",
}
CANARY = "e02a_v3_placeholder_canary"      # test.sh is never executed here; the service reads only its SOLUTION_FILE line
PREFLIGHT_PREFIX = "mbpp__preflight_"
# Mirrors experiment 103's service (veribench_valkyrie_service.py); the real round-trip runs its own loader.
AGENT_SPEC_RE = re.compile(r"^<!-- VeriBench agent-spec v([2-9]|[1-9][0-9]+)([ :].*)? -->\r?$")
SOLUTION_FILE_RE = re.compile(r'^SOLUTION_FILE="/home/user/lean_project/Veribench/([A-Za-z0-9_]+)\.lean"$', re.M)


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def load_adapter(adapter_dir: Path):
    for rel, want in ADAPTER_FILES_SHA256.items():
        got = sha((adapter_dir / rel).read_bytes())
        if got != want:
            raise RuntimeError(f"adapter byte mismatch for {rel}: {got} != {want}")
    os.environ.setdefault("VERIBENCH_ROOT", str(REPO_ROOT / "external" / "veribench"))
    spec = importlib.util.spec_from_file_location("adapter_v6", adapter_dir / "adapter.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    if "agent-spec v6" not in mod.AGENT_SPEC_VERSION:
        raise RuntimeError(f"unexpected adapter stamp {mod.AGENT_SPEC_VERSION!r}")
    return mod


def write_task(pack: Path, task_id: str, lean_stem: str, py_text: str, adapter, task_toml: str) -> dict:
    from rl4cv.veribench.exp103 import build_prompt

    instruction = adapter.generate_instruction(py_text, lean_stem)
    test_sh = adapter.generate_test_sh(lean_stem, CANARY)
    if not AGENT_SPEC_RE.match(instruction.splitlines()[0]):
        raise RuntimeError(f"{task_id}: instruction is not stamped agent-spec v<N>")
    m = SOLUTION_FILE_RE.search(test_sh)
    if not m or m.group(1) != lean_stem:
        raise RuntimeError(f"{task_id}: test.sh SOLUTION_FILE line missing or wrong stem")
    if re.search(r"thm \.\.\. := sorry", instruction):
        raise RuntimeError(f"{task_id}: sorry-mandating instruction")
    prompt = build_prompt(instruction, root=REPO_ROOT / "external" / "veribench")
    expected_path = f"/home/user/lean_project/Veribench/{lean_stem}.lean"
    if prompt.required_paths != (expected_path,):
        raise RuntimeError(f"{task_id}: required paths {prompt.required_paths} != ({expected_path},)")
    d = pack / task_id
    (d / "tests").mkdir(parents=True)
    (d / "instruction.md").write_text(instruction, encoding="utf-8")
    (d / "tests" / "test.sh").write_text(test_sh, encoding="utf-8")
    (d / "task.toml").write_text(task_toml, encoding="utf-8")
    return {"task_id": task_id, "lean_stem": lean_stem, "required_path": expected_path,
            "py_sha256": sha(py_text.encode("utf-8")), "instruction_sha256": sha(instruction.encode("utf-8")),
            "instruction_bytes": len(instruction.encode("utf-8")), "test_sh_sha256": sha(test_sh.encode("utf-8")),
            "prompt_sha256": prompt.prompt_sha256, "prompt_bytes": len(prompt.user.encode("utf-8"))}


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--declared-manifest", type=Path, required=True)
    ap.add_argument("--py-dir", type=Path, required=True, help="rewritten files: <py-dir>/mbpp/<lean_stem>.py")
    ap.add_argument("--adapter-dir", type=Path, required=True)
    ap.add_argument("--out", type=Path, required=True, help="pack directory (must not exist)")
    ap.add_argument("--pack-manifest", type=Path, required=True)
    ap.add_argument("--task-ids-out", type=Path, required=True, help="declared task ids, one per line (for --task-ids-file)")
    ap.add_argument("--preflight-source", default="mbpp__task_1", help="declared task whose Python the preflight task re-serves")
    args = ap.parse_args(argv)
    if args.out.exists() or args.pack_manifest.exists():
        raise FileExistsError("pack or pack manifest exists; packs are write-once")
    from rl4cv.veribench.exp103 import build_prompt, veribench_root

    adapter = load_adapter(args.adapter_dir)
    task_toml = (args.adapter_dir / "template" / "task.toml").read_text(encoding="utf-8")
    declared = json.loads(args.declared_manifest.read_text())
    args.out.mkdir(parents=True)
    rows = []
    by_id = {t["task_id"]: t for t in declared["tasks"]}
    for t in declared["tasks"]:
        py_path = args.py_dir / "mbpp" / f"{t['lean_stem']}.py"
        py_text = py_path.read_text(encoding="utf-8")
        if sha(py_text.encode("utf-8")) != t["py_sha256"]:
            raise RuntimeError(f"{t['task_id']}: Python file hash differs from the declared manifest")
        rows.append(write_task(args.out, t["task_id"], t["lean_stem"], py_text, adapter, task_toml))
    src = by_id[args.preflight_source]
    pre_id = PREFLIGHT_PREFIX + src["lean_stem"]
    pre_stem = "preflight_" + src["lean_stem"]
    py_text = (args.py_dir / "mbpp" / f"{src['lean_stem']}.py").read_text(encoding="utf-8")
    preflight = write_task(args.out, pre_id, pre_stem, py_text, adapter, task_toml)
    preflight["source_task_id"] = src["task_id"]
    ids = [r["task_id"] for r in rows]
    ids_text = "".join(i + "\n" for i in ids)
    if sha(ids_text.encode("utf-8")) != declared["task_ids_sha256"]:
        raise RuntimeError("pack task ids do not reproduce the declared manifest's task_ids_sha256")
    args.task_ids_out.write_text(ids_text, encoding="utf-8")
    probe = build_prompt(adapter.generate_instruction("<PYTHON>\n", "Stem"), root=veribench_root())
    manifest = {
        "manifest_kind": "pack_manifest_e02a_v3",
        "written_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "pack_dir": str(args.out.resolve()),
        "declared_manifest_sha256": sha(args.declared_manifest.read_bytes()),
        "task_ids_sha256": declared["task_ids_sha256"],
        "adapter": {"veribench_commit": ADAPTER_COMMIT, "agent_spec": adapter.AGENT_SPEC_VERSION,
                    "files_sha256": ADAPTER_FILES_SHA256, "test_sh_canary": CANARY,
                    "note": "generate_instruction(py_content, lean_stem) and generate_test_sh(lean_stem, canary) from vb_harbor/adapter at the commit above; "
                            "regenerating experiment 103 pack tasks from their py_src with these bytes is byte-identical"},
        "prompt": {"system_prompt_sha256": probe.system_prompt_sha256, "addendum": "vbv1", "addendum_sha256": probe.addendum_sha256,
                   "user_message": "instruction.rstrip() + '\\n\\n---\\n\\n' + addendum_vbv1.md (rl4cv.veribench.exp103.build_prompt)",
                   "instruction_template_probe_sha256": probe.instruction_sha256},
        "n_declared": len(rows), "preflight": preflight, "tasks": rows,
    }
    args.pack_manifest.parent.mkdir(parents=True, exist_ok=True)
    args.pack_manifest.write_text(json.dumps(manifest, indent=1, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"n_declared": len(rows), "preflight": pre_id, "pack": str(args.out), "system_prompt_sha256": probe.system_prompt_sha256[:16],
                      "addendum_sha256": probe.addendum_sha256[:16], "mean_prompt_bytes": round(sum(r["prompt_bytes"] for r in rows) / len(rows))}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
