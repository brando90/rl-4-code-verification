"""Generate single-call VeriBench answers from a local open-weight policy with vLLM and record per-sample receipts.

Each output row is one (task, sample) cell: the prompt hashes, the raw completion, the finish
reason, generated-token count, whether the response hit the cap (admission under overlong
filtering) and the extracted Lean file. Rows are written as JSONL, one line per cell, flushed as
they complete so an interrupted run keeps every finished cell.

Usage (on a GPU host, inside an environment with vLLM installed):

    python -m rl4cv.veribench.generate --pack PACK --task-ids ids.txt --model Qwen/Qwen3.5-2B \\
        --revision <commit> --samples 1 --max-tokens 65536 --temperature 1.0 --top-p 0.95 --top-k 20 \\
        --out results/gen_qwen3.5-2b_g1.jsonl

The sampling defaults are experiment 103's served defaults for Qwen3.6 (temperature 1.0,
top-p 0.95, top-k 20, 65,536 output tokens); the RL probe contract uses the paper's decoding
instead (temperature 0.6, top-p 0.95, top-k 20, 12,288-token cap). Record whichever is used.
"""

from __future__ import annotations

import argparse
import datetime as _dt
import json
import sys
from pathlib import Path

from rl4cv.veribench.exp103 import build_prompt, clean_finish, extract_lean, veribench_root
from rl4cv.veribench.pack import load_pack, read_task_ids


def _now() -> str:
    return _dt.datetime.now(_dt.timezone.utc).isoformat(timespec="seconds")


def done_cells(out_path: Path) -> set[tuple[str, int]]:
    if not out_path.is_file():
        return set()
    done = set()
    for line in out_path.read_text(encoding="utf-8").splitlines():
        if line.strip():
            row = json.loads(line)
            done.add((row["task_id"], int(row["sample_idx"])))
    return done


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--pack", required=True, type=Path)
    ap.add_argument("--task-ids", type=Path, help="one task id per line; defaults to every task in the pack")
    ap.add_argument("--model", required=True, help="Hugging Face id or local path of the policy")
    ap.add_argument("--revision", default=None, help="pinned Hugging Face commit; required for public models")
    ap.add_argument("--label", default=None, help="condition label written into every row")
    ap.add_argument("--samples", type=int, default=1, help="samples per task (1 for evaluation, 8 for probes)")
    ap.add_argument("--max-tokens", type=int, default=65536)
    ap.add_argument("--max-model-len", type=int, default=None)
    ap.add_argument("--temperature", type=float, default=1.0)
    ap.add_argument("--top-p", type=float, default=0.95)
    ap.add_argument("--top-k", type=int, default=20)
    ap.add_argument("--seed", type=int, default=91)
    ap.add_argument("--thinking", choices=["on", "off", "model-default"], default="on")
    ap.add_argument("--tensor-parallel-size", type=int, default=1)
    ap.add_argument("--gpu-memory-utilization", type=float, default=0.88)
    ap.add_argument("--addendum", default="vbv1")
    ap.add_argument("--veribench-root", default=None)
    ap.add_argument("--batch", type=int, default=64, help="prompts submitted to vLLM per batch (rows flush per batch)")
    ap.add_argument("--out", required=True, type=Path)
    args = ap.parse_args(argv)

    if args.revision is None and not Path(args.model).exists():
        ap.error("--revision is required for hub models so the exact weights are recorded")

    root = veribench_root(args.veribench_root)
    ids = read_task_ids(args.task_ids) if args.task_ids else None
    tasks = load_pack(args.pack, ids)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    done = done_cells(args.out)
    todo = [(t, k) for t in tasks for k in range(args.samples) if (t.task_id, k) not in done]
    print(f"{len(tasks)} tasks x {args.samples} samples; {len(done)} cells already done; {len(todo)} to run", file=sys.stderr)
    if not todo:
        return 0

    from vllm import LLM, SamplingParams  # imported late so the module imports without a GPU stack

    llm = LLM(
        model=args.model,
        revision=args.revision,
        tensor_parallel_size=args.tensor_parallel_size,
        gpu_memory_utilization=args.gpu_memory_utilization,
        max_model_len=args.max_model_len,
        seed=args.seed,
        trust_remote_code=False,
    )
    tok = llm.get_tokenizer()
    chat_kwargs = {} if args.thinking == "model-default" else {"enable_thinking": args.thinking == "on"}

    prompts = {t.task_id: build_prompt(t.instruction, addendum=args.addendum, root=root) for t in tasks}
    with args.out.open("a", encoding="utf-8") as fh:
        for start in range(0, len(todo), args.batch):
            chunk = todo[start : start + args.batch]
            texts, params = [], []
            for task, k in chunk:
                p = prompts[task.task_id]
                texts.append(tok.apply_chat_template(p.messages(), tokenize=False, add_generation_prompt=True, **chat_kwargs))
                params.append(
                    SamplingParams(
                        n=1,
                        temperature=args.temperature,
                        top_p=args.top_p,
                        top_k=args.top_k,
                        max_tokens=args.max_tokens,
                        seed=args.seed * 100003 + k,
                    )
                )
            outputs = llm.generate(texts, params)
            for (task, k), text, out in zip(chunk, texts, outputs):
                comp = out.outputs[0]
                p = prompts[task.task_id]
                ext = extract_lean(comp.text, p.required_paths, addendum=args.addendum, root=root)
                row = {
                    "task_id": task.task_id,
                    "sample_idx": k,
                    "label": args.label,
                    "model": args.model,
                    "revision": args.revision,
                    "sampling": {
                        "temperature": args.temperature,
                        "top_p": args.top_p,
                        "top_k": args.top_k,
                        "max_tokens": args.max_tokens,
                        "seed": args.seed * 100003 + k,
                        "thinking": args.thinking,
                    },
                    "instruction_sha256": p.instruction_sha256,
                    "addendum_sha256": p.addendum_sha256,
                    "prompt_sha256": p.prompt_sha256,
                    "system_prompt_sha256": p.system_prompt_sha256,
                    "prompt_tokens": len(out.prompt_token_ids or []),
                    "generated_tokens": len(comp.token_ids),
                    "finish_reason": comp.finish_reason,
                    "measured": clean_finish(comp.finish_reason),
                    "truncated": comp.finish_reason == "length",
                    "admitted": comp.finish_reason != "length",
                    "extraction": ext.method,
                    "lean": ext.lean,
                    "completion": comp.text,
                    "finished_utc": _now(),
                }
                fh.write(json.dumps(row, ensure_ascii=False) + "\n")
            fh.flush()
            print(f"cells {min(start + args.batch, len(todo))}/{len(todo)}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
