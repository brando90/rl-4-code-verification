#!/usr/bin/env python3
"""TLDR: Confirm that the frozen prompt bytes the teachers see (experiment 103's system prompt, the agent-spec v6 instruction template and addendum_vbv1.md) embed no VeriBench task text, reference Lean or Python program, because they become the SFT input (experiment 02A v3 PROTOCOL § 3; zero model calls)."""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[5]
sys.path.insert(0, str(REPO_ROOT / "src"))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from rl4cv.screens import jaccard, normalize, shingles  # noqa: E402
from screen_mbpp_tasks import protected_corpus  # noqa: E402

MIN_WINDOW_WORDS = 12   # a run of 12 normalized words shared with any VeriBench file is reported


def sha(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def shared_windows(text: str, protected: dict[str, str], n: int = MIN_WINDOW_WORDS) -> list[dict]:
    """Every n-word window of `text` that occurs verbatim (after normalization) in a protected file."""
    words = normalize(text).split()
    windows = {" ".join(words[i:i + n]) for i in range(max(0, len(words) - n + 1))}
    hits = []
    for pid, ptext in protected.items():
        pnorm = normalize(ptext)
        found = [w for w in windows if w in pnorm]
        if found:
            hits.append({"protected_file": pid, "n_windows": len(found), "example": sorted(found)[0][:200]})
    return hits


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--adapter-dir", type=Path, required=True)
    ap.add_argument("--veribench-root", type=Path, required=True)
    ap.add_argument("--out", type=Path, required=True)
    args = ap.parse_args(argv)
    os.environ.setdefault("VERIBENCH_ROOT", str(args.veribench_root))
    from rl4cv.veribench.exp103 import ADDENDUM_REL, load_single_call

    spec = importlib.util.spec_from_file_location("adapter_v6", args.adapter_dir / "adapter.py")
    adapter = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(adapter)
    mod = load_single_call(str(args.veribench_root))
    addendum = (args.veribench_root / ADDENDUM_REL.format(name="vbv1")).read_text(encoding="utf-8")
    template = adapter.generate_instruction("", "Stem")   # the template with an empty Python block
    texts = {"system_prompt": mod.SYSTEM_PROMPT, "instruction_template": template, "addendum_vbv1": addendum}
    protected = protected_corpus(args.veribench_root)
    prot_sh = {pid: shingles(t) for pid, t in protected.items()}
    report = {"written_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"), "veribench_root": str(args.veribench_root.resolve()),
              "n_protected_files": len(protected), "min_shared_window_words": MIN_WINDOW_WORDS, "texts": {}}
    verdict = "PASS"
    for name, text in texts.items():
        sh = shingles(text)
        best = max(((jaccard(sh, p), pid) for pid, p in prot_sh.items()), default=(0.0, None))
        windows = shared_windows(text, protected)
        # Code fences in the template are empty placeholders; any whole protected file inside the text is a leak.
        # A protected file shorter than one window (e.g. lean_src/sandbox.lean = `import Mathlib`) carries no task text;
        # it is listed as trivial rather than counted as an embedding.
        trivial = [pid for pid, pt in protected.items() if len(normalize(pt).split()) < MIN_WINDOW_WORDS]
        embedded = [pid for pid, pt in protected.items() if pid not in trivial and normalize(pt) in normalize(text)]
        row = {"sha256": sha(text), "bytes": len(text.encode("utf-8")), "max_word5_jaccard": best[0], "nearest_protected_file": best[1],
               "embedded_protected_files": embedded, "shared_12_word_windows": windows,
               "trivial_protected_files_ignored": {pid: normalize(protected[pid])[:80] for pid in trivial}}
        if embedded or windows:
            verdict = "FAIL"
        report["texts"][name] = row
    report["verdict"] = verdict
    report["meaning"] = ("PASS: none of the three prompt components contains a VeriBench py_src program or lean_src file, and no 12-word "
                         "normalized window is shared with any of them; the only task-specific bytes in a teacher prompt are the MBPP program.")
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, indent=1, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"verdict": verdict, **{k: {"max_word5_jaccard": round(v["max_word5_jaccard"], 4), "windows": len(v["shared_12_word_windows"]), "embedded": len(v["embedded_protected_files"])} for k, v in report["texts"].items()}}))
    return 0 if verdict == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
