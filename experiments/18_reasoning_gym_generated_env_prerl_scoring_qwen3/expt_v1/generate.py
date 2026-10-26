"""Sample 16 responses per item for experiment 18a sets with vLLM (or a deterministic fake model for CPU dry runs).

One output file per (model, set): <out>/raw/<model_tag>/<set>.jsonl, written atomically when the set is done, so a
rerun of the same command skips finished sets (resume after a wall-time kill). Usage:

    python generate.py --run ~/e18a/run --model-tag qwen3_0p6b --shard 0 --nshards 2
    python generate.py --run /tmp/r --model-tag qwen3_0p6b --backend fake --n 4      # CPU dry run
"""

from __future__ import annotations

import argparse
import hashlib
import json
import random
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import e18a_common as C  # noqa: E402


class FakeLLM:
    """Deterministic stand-in for vLLM: correct, wrong, untagged or capped answers with a level- and size-dependent rate."""

    name = "fake"
    version = "fake-1"

    def __init__(self, model_tag: str, max_tokens: int):
        self.size_b = C.MODELS[model_tag]["size_b"]
        self.tag = model_tag
        self.max_tokens = max_tokens

    def sample(self, items: list[dict], spec: C.SetSpec, n: int) -> list[list[dict]]:
        out = []
        level = spec.level if spec.level is not None else 1
        fam_shift = (sum(map(ord, spec.family)) % 7) / 20.0
        p_correct = min(0.97, max(0.03, 0.85 - 0.22 * level - fam_shift + 0.08 * self.size_b))
        for item in items:
            rng = random.Random(f"{self.tag}|{item['item_id']}|{spec.sampling_seed}")
            item_shift = rng.uniform(-0.25, 0.25)
            group = []
            for k in range(n):
                u = rng.random()
                tokens = rng.randint(20, 400)
                finish = "stop"
                if u < min(0.97, max(0.0, p_correct + item_shift)):
                    text = f"Thinking about it.\n<answer>{item['gold']}</answer>"
                elif u < 0.97:
                    text = "I think the answer is <answer>definitely-wrong-17</answer>" if k % 3 else "No tag here."
                else:
                    text, tokens, finish = "...", self.max_tokens, "length"
                group.append({"text": text, "generated_tokens": tokens, "finish_reason": finish})
            out.append(group)
        return out


class VLLMBackend:
    """vLLM LLM.chat with the frozen sampling settings and thinking off."""

    name = "vllm"

    def __init__(self, model_tag: str, model_path: str | None, max_tokens: int, max_model_len: int, gpu_mem: float):
        import vllm
        from vllm import LLM

        self.version = vllm.__version__
        m = C.MODELS[model_tag]
        rev = None if model_path else m["revision"]
        self.llm = LLM(model=model_path or m["id"], revision=rev, tokenizer_revision=rev, dtype="bfloat16",
                       max_model_len=max_model_len, gpu_memory_utilization=gpu_mem, enable_prefix_caching=True,
                       seed=0)
        self.max_tokens = max_tokens

    def sample(self, items: list[dict], spec: C.SetSpec, n: int) -> list[list[dict]]:
        from vllm import SamplingParams

        kw = dict(n=n, temperature=C.TEMPERATURE, top_p=C.TOP_P, max_tokens=self.max_tokens, seed=spec.sampling_seed)
        try:
            sp = SamplingParams(top_k=C.TOP_K, **kw)
        except ValueError:  # vLLM versions that spell "no top-k" as 0 instead of -1
            sp = SamplingParams(top_k=0, **kw)
        outs = self.llm.chat([it["messages"] for it in items], sp, use_tqdm=False,
                             chat_template_kwargs={"enable_thinking": False})
        groups = []
        for o in outs:
            groups.append([{"text": c.text, "generated_tokens": len(c.token_ids), "finish_reason": c.finish_reason}
                           for c in o.outputs])
        return groups


def raw_path(run: Path, model_tag: str, spec: C.SetSpec) -> Path:
    return run / "raw" / model_tag / f"{spec.file_stem}.jsonl"


def is_complete(path: Path, n_items: int, n: int) -> bool:
    if not path.exists():
        return False
    with open(path, encoding="utf-8") as fh:
        return sum(1 for line in fh if line.strip()) == n_items * n


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--run", required=True, help="run directory holding items/ (from build.py)")
    ap.add_argument("--model-tag", required=True, choices=sorted(C.MODELS))
    ap.add_argument("--model-path", help="local snapshot directory (default: HF id at the pinned revision)")
    ap.add_argument("--sets", default="all")
    ap.add_argument("--shard", type=int, default=0)
    ap.add_argument("--nshards", type=int, default=1)
    ap.add_argument("--n", type=int, default=C.GROUP_SIZE, help="samples per item (frozen: 16)")
    ap.add_argument("--limit-items", type=int, default=0, help="smoke only: first k items of each set")
    ap.add_argument("--max-tokens", type=int, default=C.MAX_TOKENS)
    ap.add_argument("--max-model-len", type=int, default=C.MAX_MODEL_LEN)
    ap.add_argument("--gpu-mem", type=float, default=0.85)
    ap.add_argument("--backend", choices=["vllm", "fake"], default="vllm")
    ap.add_argument("--out-subdir", default="", help="smoke only: write under raw_<subdir> instead of raw")
    args = ap.parse_args(argv)

    run = Path(args.run)
    manifest = json.loads((run / "items" / "manifest.json").read_text())
    built = {m["set_id"] for m in manifest["sets"]}
    sets = [s for s in C.shard_sets(C.select_sets(args.sets), args.shard, args.nshards) if s.set_id in built]
    out_root = run / (f"raw_{args.out_subdir}" if args.out_subdir else "raw")
    todo = []
    for spec in sets:
        items = list(C.read_jsonl(run / "items" / f"{spec.file_stem}.jsonl"))
        if args.limit_items:
            items = items[: args.limit_items]
        path = out_root / args.model_tag / f"{spec.file_stem}.jsonl"
        if is_complete(path, len(items), args.n):
            print(f"skip {spec.set_id}: complete", flush=True)
            continue
        todo.append((spec, items, path))
    if not todo:
        print("nothing to do", flush=True)
        return 0
    backend = (FakeLLM(args.model_tag, args.max_tokens) if args.backend == "fake" else
               VLLMBackend(args.model_tag, args.model_path, args.max_tokens, args.max_model_len, args.gpu_mem))
    m = C.MODELS[args.model_tag]
    for spec, items, path in todo:
        t0 = time.time()
        groups = backend.sample(items, spec, args.n)
        rows = []
        for item, group in zip(items, groups):
            if len(group) != args.n:
                raise RuntimeError(f"{item['item_id']}: got {len(group)} samples, expected {args.n}")
            for k, resp in enumerate(group):
                rows.append({"set_id": spec.set_id, "item_id": item["item_id"], "sample": k,
                             "question_sha256": item["question_sha256"], "text": resp["text"],
                             "generated_tokens": int(resp["generated_tokens"]), "finish_reason": resp["finish_reason"],
                             "model": m["id"], "model_revision": m["revision"], "model_tag": args.model_tag,
                             "backend": backend.name, "backend_version": backend.version,
                             "sampling_seed": spec.sampling_seed, "max_tokens": args.max_tokens})
        C.write_jsonl_atomic(path, rows)
        toks = sum(r["generated_tokens"] for r in rows)
        dt = time.time() - t0
        timing = {"set_id": spec.set_id, "model_tag": args.model_tag, "seconds": round(dt, 2), "responses": len(rows),
                  "generated_tokens": toks, "tokens_per_s": round(toks / dt, 1) if dt > 0 else None,
                  "sha256": hashlib.sha256(path.read_bytes()).hexdigest()}
        with open(out_root / args.model_tag / "timing.jsonl", "a", encoding="utf-8") as fh:
            fh.write(json.dumps(timing) + "\n")
        print(f"done {spec.set_id}: {len(rows)} responses, {toks} tokens, {dt:.0f}s", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
