#!/usr/bin/env python3
"""TLDR: Verify the pinned Qwen3 Base tokenizers' actual chat template for experiment 08's SFT rendering (PROTOCOL § 7): the evaluation prompt `apply_chat_template([system, user], add_generation_prompt=True, enable_thinking=True)` must be an exact byte and token-id prefix of the full render with the assistant message, the remainder (the only loss span) must equal the template's inserted empty think block + the response verbatim + `<|im_end|>\\n`, and all four sizes must give identical token ids; `control` runs it on one fixed train task before lock 1, `examples` on every SFT example before lock 2 (zero model calls; runs in the vLLM/transformers interpreter)."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(REPO_ROOT / "src"))
EXP = Path(__file__).resolve().parents[1]
WORK = Path(os.environ.get("E08_WORK", "/lfs/skampere1/0/brando9/rl4cv_e08"))
os.environ.setdefault("HF_HOME", str(WORK / "cache" / "huggingface"))
MODELS = {
    "1.7B": ("Qwen/Qwen3-1.7B-Base", "ea980cb0a6c2ae4b936e82123acc929f1cec04c1"),
    "4B": ("Qwen/Qwen3-4B-Base", "906bfd4b4dc7f14ee4320094d8b41684abff8539"),
    "8B": ("Qwen/Qwen3-8B-Base", "49e3418fbbbca6ecbdf9608b4d22e5a407081db4"),
    "14B": ("Qwen/Qwen3-14B-Base", "0b0bd3732e2c374d483664439ea334928b65f304"),
}
EXPECTED_THINK_PREFIX = "<think>\n\n</think>\n\n"
END = "<|im_end|>\n"
MAX_TOTAL = 16384
CONTROL_ASSISTANT = ("FILE: /home/user/lean_project/Veribench/Control.lean\n```lean\nimport Mathlib\n\nnamespace Control\n\n"
                     "def f (n : Nat) : Nat := n + 1\n\nexample : f 1 = 2 := by decide\n\ntheorem f_pos (n : Nat) : 0 < f n := by\n  simp [f]\n\nend Control\n```\n")


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def stamp() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def load_tokenizers(sizes: list[str]) -> dict:
    from transformers import AutoTokenizer

    out = {}
    for size in sizes:
        mid, rev = MODELS[size]
        tok = AutoTokenizer.from_pretrained(mid, revision=rev, local_files_only=True)
        snap = Path(tok.name_or_path) if Path(tok.name_or_path).is_dir() else None
        files = {}
        if snap is None:
            from huggingface_hub import snapshot_download

            snap = Path(snapshot_download(mid, revision=rev, allow_patterns=["tokenizer*", "vocab.json", "merges.txt"], local_files_only=True))
        for name in ("tokenizer.json", "tokenizer_config.json", "vocab.json", "merges.txt"):
            p = snap / name
            if p.is_file():
                files[name] = sha(p.read_bytes())
        out[size] = {"tokenizer": tok, "model_id": mid, "revision": rev, "files_sha256": files, "chat_template_sha256": sha((tok.chat_template or "").encode("utf-8")),
                     "bos_token": tok.bos_token, "eos_token": tok.eos_token, "pad_token": tok.pad_token, "im_end_id": tok.convert_tokens_to_ids("<|im_end|>")}
    return out


def render(tok, system: str, user: str, assistant: str | None) -> dict:
    msgs = [{"role": "system", "content": system}, {"role": "user", "content": user}]
    prefix = tok.apply_chat_template(msgs, tokenize=False, add_generation_prompt=True, enable_thinking=True)
    prefix_ids = tok(prefix, add_special_tokens=False)["input_ids"]
    out = {"prefix_text_sha256": sha(prefix.encode("utf-8")), "prefix_bytes": len(prefix.encode("utf-8")), "n_prompt_tokens": len(prefix_ids),
           "prefix_ids_sha256": sha(json.dumps(prefix_ids).encode())}
    if assistant is None:
        return out
    full = tok.apply_chat_template(msgs + [{"role": "assistant", "content": assistant}], tokenize=False, add_generation_prompt=False, enable_thinking=True)
    full_ids = tok(full, add_special_tokens=False)["input_ids"]
    span = full[len(prefix):] if full.startswith(prefix) else None
    expected_span = EXPECTED_THINK_PREFIX + assistant + END
    out.update(byte_prefix_ok=full.startswith(prefix), token_prefix_ok=full_ids[:len(prefix_ids)] == prefix_ids, n_total_tokens=len(full_ids),
               n_assistant_tokens=len(full_ids) - len(prefix_ids), span_matches_expected=(span == expected_span),
               span_sha256=sha(span.encode("utf-8")) if span is not None else None, full_ids_sha256=sha(json.dumps(full_ids).encode()),
               assistant_ids_sha256=sha(json.dumps(full_ids[len(prefix_ids):]).encode()), within_cap=len(full_ids) <= MAX_TOTAL,
               template_inserted_prefix=(span[:len(EXPECTED_THINK_PREFIX)] if span else None), ends_with_im_end_newline=(bool(span) and span.endswith(END)),
               response_has_think_close=("</think>" in assistant), response_leading_newline=assistant.startswith("\n"))
    return out


def cross_size(per_size: dict, keys: tuple[str, ...]) -> dict:
    return {k: len({v[k] for v in per_size.values()}) == 1 for k in keys}


def cmd_control(a) -> int:
    from rl4cv.veribench.exp103 import build_prompt

    ids = [l.strip() for l in (EXP / "results" / "split" / "vbv1_train_task_ids.txt").read_text().splitlines() if l.strip()]
    tid = ids[0]
    instruction = (a.pack / tid / "instruction.md").read_text(encoding="utf-8")
    p = build_prompt(instruction, root=REPO_ROOT / "external" / "veribench")
    toks = load_tokenizers(a.sizes)
    per_size = {s: render(t["tokenizer"], p.system, p.user, CONTROL_ASSISTANT) for s, t in toks.items()}
    # A response that starts with a newline or contains </think> would be altered by the template: confirm the check catches it.
    altered = {s: {"leading_newline": render(t["tokenizer"], p.system, p.user, "\n" + CONTROL_ASSISTANT)["span_matches_expected"],
                   "think_close": render(t["tokenizer"], p.system, p.user, "x </think> y")["span_matches_expected"]} for s, t in toks.items()}
    same = cross_size(per_size, ("prefix_ids_sha256", "full_ids_sha256", "assistant_ids_sha256", "n_prompt_tokens", "n_assistant_tokens"))
    tok_same = {k: len({t[k] if not isinstance(t[k], dict) else json.dumps(t[k], sort_keys=True) for t in toks.values()}) == 1
                for k in ("chat_template_sha256", "files_sha256", "eos_token", "im_end_id")}
    ok = all(v["byte_prefix_ok"] and v["token_prefix_ok"] and v["span_matches_expected"] and v["ends_with_im_end_newline"] for v in per_size.values()) \
        and all(same.values()) and all(not x["leading_newline"] and not x["think_close"] for x in altered.values())
    out = {"written_utc": stamp(), "control_task_id": tid, "sizes": a.sizes, "tokenizers": {s: {k: v for k, v in t.items() if k != "tokenizer"} for s, t in toks.items()},
           "prompt": {"system_prompt_sha256": p.system_prompt_sha256, "addendum_sha256": p.addendum_sha256, "prompt_sha256": p.prompt_sha256},
           "control_assistant_sha256": sha(CONTROL_ASSISTANT.encode("utf-8")), "per_size": per_size, "identical_across_sizes": same, "tokenizer_identity_across_sizes": tok_same,
           "template_alters_response_when": {"leading_newline_or_think_close": "detected (span_matches_expected false)", "evidence": altered},
           "assistant_span_definition": "full render minus the evaluation prompt: '<think>\\n\\n</think>\\n\\n' + response verbatim + '<|im_end|>\\n' (the trailing newline is template residue and is kept in the loss span)",
           "note_bos": "Qwen3 tokenizers have no BOS token; add_special_tokens=False and vLLM's text-prompt tokenization give the same ids",
           "verdict": "PASS" if ok else "FAIL"}
    a.out.parent.mkdir(parents=True, exist_ok=True)
    a.out.write_text(json.dumps(out, indent=1, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"verdict": out["verdict"], "sizes": a.sizes, "identical_across_sizes": same, "tokenizer_identity": tok_same,
                      "n_prompt_tokens": {s: v["n_prompt_tokens"] for s, v in per_size.items()}, "n_assistant_tokens": {s: v["n_assistant_tokens"] for s, v in per_size.items()},
                      "template_inserted_prefix": repr(next(iter(per_size.values()))["template_inserted_prefix"])}))
    return 0 if ok else 1


def cmd_examples(a) -> int:
    toks = load_tokenizers(a.sizes)
    rows = [json.loads(l) for l in a.sft.read_text(encoding="utf-8").splitlines() if l.strip()]
    per_example, bad = [], []
    with a.out_jsonl.open("w", encoding="utf-8") as fh:
        for i, r in enumerate(rows):
            m = {x["role"]: x["content"] for x in r["messages"]}
            per_size = {s: render(t["tokenizer"], m["system"], m["user"], m["assistant"]) for s, t in toks.items()}
            same = cross_size(per_size, ("prefix_ids_sha256", "full_ids_sha256", "n_prompt_tokens", "n_assistant_tokens"))
            ref = per_size[a.sizes[0]]
            ok = all(v["byte_prefix_ok"] and v["token_prefix_ok"] and v["span_matches_expected"] for v in per_size.values()) and all(same.values())
            entry = {"index": i, "task_id": r.get("task_id"), "teacher": r.get("teacher"), "r": r.get("r"), "ok": ok, "identical_across_sizes": same,
                     "n_prompt_tokens": ref["n_prompt_tokens"], "n_assistant_tokens": ref["n_assistant_tokens"], "n_total_tokens": ref["n_total_tokens"],
                     "within_cap": ref["within_cap"], "prefix_ids_sha256": ref["prefix_ids_sha256"], "assistant_ids_sha256": ref["assistant_ids_sha256"],
                     "response_has_think_close": ref["response_has_think_close"], "response_leading_newline": ref["response_leading_newline"]}
            if not ok:
                bad.append(entry)
            per_example.append(entry)
            fh.write(json.dumps(entry, sort_keys=True) + "\n")
    summary = {"written_utc": stamp(), "sft": str(a.sft), "sft_sha256": sha(a.sft.read_bytes()), "sizes": a.sizes, "n_examples": len(rows), "n_ok": len(rows) - len(bad),
               "n_bad": len(bad), "bad": bad[:50], "n_over_cap": sum(1 for e in per_example if not e["within_cap"]),
               "assistant_tokens_total": sum(e["n_assistant_tokens"] for e in per_example), "prompt_tokens_total": sum(e["n_prompt_tokens"] for e in per_example),
               "tokenizers": {s: {k: v for k, v in t.items() if k != "tokenizer"} for s, t in toks.items()}, "verdict": "PASS" if not bad else "FAIL"}
    a.out.write_text(json.dumps(summary, indent=1, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({k: summary[k] for k in ("verdict", "n_examples", "n_ok", "n_bad", "n_over_cap", "assistant_tokens_total")}))
    return 0 if not bad else 1


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--sizes", nargs="+", default=list(MODELS), choices=list(MODELS))
    sub = ap.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("control")
    p.add_argument("--pack", type=Path, default=WORK / "pack_train539")
    p.add_argument("--out", type=Path, default=EXP / "results" / "template_check.json")
    p = sub.add_parser("examples")
    p.add_argument("--sft", type=Path, required=True)
    p.add_argument("--out", type=Path, required=True)
    p.add_argument("--out-jsonl", type=Path, required=True)
    a = ap.parse_args(argv)
    return {"control": cmd_control, "examples": cmd_examples}[a.cmd](a)


if __name__ == "__main__":
    raise SystemExit(main())
