#!/usr/bin/env python3
"""TLDR: Convert experiment 08's SFT set S into the NeMo RL `openai_format` JSONL, render every example with NeMo RL's own message formatter (`get_formatted_message_log`, add_bos/add_eos/add_generation_prompt as the frozen config) under the four pinned Qwen3 Base tokenizers, verify that the prompt tokens equal the evaluation prompt (`apply_chat_template([system, user], add_generation_prompt=True, enable_thinking=True)`), that the loss span is `<think>\\n\\n</think>\\n\\n` + response verbatim + `<|im_end|>\\n` + EOS, and that all sizes give identical ids; then compute the batch-2 step schedule, the 12.5 / 25 / 50 / 75 / 100% assistant-token checkpoint steps with overshoot, and the odd-|S| fully-masked padding slot (PROTOCOL §§ 7–8, 12; runs with the NeMo RL interpreter; zero model calls)."""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[4]
EXP = Path(__file__).resolve().parents[1]
WORK = Path(os.environ.get("E08_WORK", "/lfs/skampere1/0/brando9/rl4cv_e08"))
NEMO = Path(os.environ.get("E08_NEMO_RL", str(WORK / "nemo_rl")))
sys.path.insert(0, str(NEMO))
sys.path.insert(0, str(Path(__file__).resolve().parent))
os.environ.setdefault("HF_HOME", str(WORK / "cache" / "huggingface"))
FRACTIONS = (0.125, 0.25, 0.5, 0.75, 1.0)
GLOBAL_BATCH = 2
MAX_TOTAL = 16384
THINK_PREFIX = "<think>\n\n</think>\n\n"
# A padding slot for odd |S| (PROTOCOL § 8): NeMo RL's SFT processor truncates an over-length example to a few tokens per message and sets
# loss_multiplier = 0 (sample_mask 0), so it contributes no loss and no valid tokens; it never repeats a training example.
PAD_USER = ("<pad> " * (MAX_TOTAL + 64)).strip()


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def stamp() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def nemo_render(tok, messages: list[dict], add_bos: bool, add_eos: bool, add_generation_prompt: bool) -> dict:
    from nemo_rl.data.interfaces import TaskDataSpec
    from nemo_rl.data.llm_message_utils import get_formatted_message_log

    spec = TaskDataSpec(task_name="rl4cv_e08")
    log = get_formatted_message_log([dict(m) for m in messages], tok, spec, add_bos_token=add_bos, add_eos_token=add_eos, add_generation_prompt=add_generation_prompt)
    ids = {m["role"]: [int(x) for x in m["token_ids"]] for m in log}
    chunks = {m["role"]: m["content"] for m in log}
    prompt_ids = ids["system"] + ids["user"]
    return {"prompt_ids": prompt_ids, "assistant_ids": ids["assistant"], "assistant_chunk": chunks["assistant"], "user_chunk_tail": chunks["user"][-40:]}


def eval_prefix(tok, system: str, user: str) -> tuple[str, list[int]]:
    text = tok.apply_chat_template([{"role": "system", "content": system}, {"role": "user", "content": user}], tokenize=False, add_generation_prompt=True, enable_thinking=True)
    return text, tok(text, add_special_tokens=False)["input_ids"]


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--sft", type=Path, default=WORK / "sft" / "s_v1.jsonl")
    ap.add_argument("--out-jsonl", type=Path, default=WORK / "sft" / "s_v1_nemo.jsonl")
    ap.add_argument("--examples-out", type=Path, default=EXP / "results" / "sft_examples_nemo.jsonl")
    ap.add_argument("--schedule-out", type=Path, default=EXP / "results" / "sft_schedule.json")
    ap.add_argument("--sizes", nargs="+", default=["1.7B", "4B", "8B", "14B"])
    ap.add_argument("--add-bos", type=int, default=1)
    ap.add_argument("--add-eos", type=int, default=1)
    ap.add_argument("--add-generation-prompt", type=int, default=1)
    ap.add_argument("--limit", type=int, default=None, help="use only the first N examples (dry run)")
    a = ap.parse_args(argv)
    import warnings

    warnings.filterwarnings("ignore")
    from template_check import MODELS, load_tokenizers

    toks = load_tokenizers(a.sizes)
    rows = [json.loads(l) for l in a.sft.read_text(encoding="utf-8").splitlines() if l.strip()]
    if a.limit:
        rows = rows[: a.limit]
    examples, bad = [], []
    ref_size = a.sizes[0]
    for r in rows:
        m = {x["role"]: x["content"] for x in r["messages"]}
        per = {}
        for size, t in toks.items():
            tok = t["tokenizer"]
            nr = nemo_render(tok, r["messages"], bool(a.add_bos), bool(a.add_eos), bool(a.add_generation_prompt))
            ptext, pids = eval_prefix(tok, m["system"], m["user"])
            expected_chunk = THINK_PREFIX + m["assistant"] + "<|im_end|>\n" + (tok.eos_token if a.add_eos else "")
            per[size] = {"prompt_ok": nr["prompt_ids"] == pids, "assistant_chunk_ok": nr["assistant_chunk"] == expected_chunk, "n_prompt": len(nr["prompt_ids"]),
                         "n_assistant": len(nr["assistant_ids"]), "n_total": len(nr["prompt_ids"]) + len(nr["assistant_ids"]),
                         "prompt_ids_sha256": sha(json.dumps(nr["prompt_ids"]).encode()), "assistant_ids_sha256": sha(json.dumps(nr["assistant_ids"]).encode()),
                         "assistant_chunk_sha256": sha(nr["assistant_chunk"].encode("utf-8")), "eval_prefix_sha256": sha(ptext.encode("utf-8"))}
        same = all(per[s][k] == per[ref_size][k] for s in per for k in ("prompt_ids_sha256", "assistant_ids_sha256", "n_prompt", "n_assistant"))
        ok = all(v["prompt_ok"] and v["assistant_chunk_ok"] for v in per.values()) and same and per[ref_size]["n_total"] <= MAX_TOTAL
        e = {"index": r["index"], "task_id": r["task_id"], "teacher": r["teacher"], "r": r["r"], "order_key": r["order_key"], "ok": ok, "identical_across_sizes": same,
             "n_prompt_tokens": per[ref_size]["n_prompt"], "n_assistant_tokens_loss": per[ref_size]["n_assistant"], "n_total_tokens": per[ref_size]["n_total"],
             "prompt_ids_sha256": per[ref_size]["prompt_ids_sha256"], "assistant_ids_sha256": per[ref_size]["assistant_ids_sha256"], "per_size": per}
        examples.append(e)
        if not ok:
            bad.append({k: e[k] for k in ("index", "task_id", "teacher", "r", "n_total_tokens")} | {"per_size": {s: {k: v[k] for k in ("prompt_ok", "assistant_chunk_ok")} for s, v in per.items()}})
    n = len(rows)
    padded = n % GLOBAL_BATCH == 1
    a.out_jsonl.parent.mkdir(parents=True, exist_ok=True)
    with a.out_jsonl.open("w", encoding="utf-8") as fh:
        for r in rows:
            fh.write(json.dumps({"messages": r["messages"], "task_id": r["task_id"], "teacher": r["teacher"], "r": r["r"], "index": r["index"], "is_padding": False}, ensure_ascii=False) + "\n")
        if padded:
            fh.write(json.dumps({"messages": [{"role": "system", "content": "padding slot"}, {"role": "user", "content": PAD_USER}, {"role": "assistant", "content": "padding slot"}],
                                 "task_id": None, "teacher": None, "r": None, "index": n, "is_padding": True}, ensure_ascii=False) + "\n")
    # NeMo RL's loader needs a validation file; it is never evaluated (val_period 0, val_at_start false): the first two train examples.
    val_dummy = a.out_jsonl.with_name("s_v1_val_dummy.jsonl")
    with val_dummy.open("w", encoding="utf-8") as fh:
        for r in rows[:2]:
            fh.write(json.dumps({"messages": r["messages"], "task_id": r["task_id"], "teacher": r["teacher"], "r": r["r"], "index": r["index"], "is_padding": False}, ensure_ascii=False) + "\n")
    # Batch-2 step schedule over the fixed order: step j (1-indexed) consumes examples 2j-1 and 2j.
    steps = math.ceil(n / GLOBAL_BATCH)
    cum, cum_steps = 0, []
    for j in range(steps):
        batch = examples[j * GLOBAL_BATCH:(j + 1) * GLOBAL_BATCH]
        cum += sum(e["n_assistant_tokens_loss"] for e in batch)
        cum_steps.append(cum)
    total = cum
    ckpts = {}
    for f in FRACTIONS:
        target = f * total
        j = next(i for i, c in enumerate(cum_steps) if c >= target - 1e-9) + 1
        ckpts[str(f)] = {"step": j, "cumulative_assistant_tokens": cum_steps[j - 1], "target_tokens": round(target, 1), "overshoot_tokens": round(cum_steps[j - 1] - target, 1),
                         "actual_fraction": round(cum_steps[j - 1] / total, 6) if total else None}
    distinct_steps = sorted({v["step"] for v in ckpts.values()})
    W = math.ceil(0.03 * steps)
    schedule = {"written_utc": stamp(), "sft_path": str(a.sft), "sft_sha256": sha(a.sft.read_bytes()), "nemo_jsonl": str(a.out_jsonl), "nemo_jsonl_sha256": sha(a.out_jsonl.read_bytes()),
                "nemo_rl_root": str(NEMO), "sizes": a.sizes, "tokenizers": {s: {k: v for k, v in t.items() if k != "tokenizer"} for s, t in toks.items()},
                "render_flags": {"add_bos": bool(a.add_bos), "add_eos": bool(a.add_eos), "add_generation_prompt": bool(a.add_generation_prompt), "chat_template": "default", "chat_template_kwargs": None},
                "loss_span": "'<think>\\n\\n</think>\\n\\n' + response verbatim + '<|im_end|>\\n' + '<|endoftext|>' (NeMo RL appends the tokenizer EOS to the last message; Qwen3 has no BOS)",
                "n_examples": n, "n_ok": n - len(bad), "n_bad": len(bad), "bad": bad[:50], "global_batch": GLOBAL_BATCH, "steps": steps, "padding_slot_appended": padded,
                "warmup_steps_W": W, "cosine_T_max": steps - W, "scheduler": {"LinearLR": {"start_factor": 1.0 / W if W else None, "end_factor": 1.0, "total_iters": W},
                                                                             "CosineAnnealingLR": {"T_max": steps - W, "eta_min": 0.0}, "milestones": [W]},
                "assistant_tokens_total": total, "prompt_tokens_total": sum(e["n_prompt_tokens"] for e in examples), "cumulative_assistant_tokens_per_step": cum_steps,
                "checkpoints": ckpts, "distinct_checkpoint_steps": distinct_steps, "max_total_tokens": MAX_TOTAL,
                "verdict": "PASS" if not bad and n > 0 else ("NOT READY: S is empty" if n == 0 else "FAIL")}
    a.examples_out.parent.mkdir(parents=True, exist_ok=True)
    with a.examples_out.open("w", encoding="utf-8") as fh:
        for e in examples:
            fh.write(json.dumps({k: v for k, v in e.items() if k != "per_size"}, sort_keys=True) + "\n")
    a.schedule_out.write_text(json.dumps(schedule, indent=1, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({k: schedule[k] for k in ("verdict", "n_examples", "n_bad", "steps", "padding_slot_appended", "warmup_steps_W", "assistant_tokens_total", "checkpoints")}, indent=1))
    return 0 if schedule["verdict"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
