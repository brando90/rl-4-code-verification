"""Policy prompt embeddings for the experiment 18a v2 alignment score: per-set centroids of mean-pooled hidden states.

For one model, every item prompt (chat template, thinking off, generation prompt added) goes through Hugging Face
transformers in bf16; the embedding is the mean over prompt tokens of the last hidden layer (and, exploratory, the
middle layer), L2-normalised. Writes <run>/emb/<model_tag>/centroids.npz (set_ids, last, mid, n). Usage:

    python embed.py --run ~/e18a_v2/run --model-tag qwen3_1p7b
    python embed.py --run /tmp/r --model-tag qwen3_1p7b --backend fake     # CPU dry run
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
import e18v2_common as C  # noqa: E402


def _normalize(x: np.ndarray) -> np.ndarray:
    n = np.linalg.norm(x, axis=-1, keepdims=True)
    return x / np.where(n > 0, n, 1.0)


class FakeEmbedder:
    """Hashed character-trigram bag of words: deterministic, CPU, enough to exercise the alignment code."""

    dim = 64

    def embed(self, prompts: list[list[dict]]) -> tuple[np.ndarray, np.ndarray]:
        out = np.zeros((len(prompts), self.dim))
        for i, msgs in enumerate(prompts):
            text = msgs[-1]["content"].lower()
            for j in range(len(text) - 2):
                h = int(hashlib.md5(text[j : j + 3].encode()).hexdigest()[:8], 16)
                out[i, h % self.dim] += 1.0
        last = _normalize(out)
        return last, _normalize(np.sqrt(out))


class HFEmbedder:
    """transformers forward pass, mean pooling over the prompt's tokens."""

    def __init__(self, model_tag: str, model_path: str | None, batch_size: int):
        import torch
        from transformers import AutoModelForCausalLM, AutoTokenizer

        m = C.MODELS[model_tag]
        src = model_path or m["id"]
        rev = None if model_path else m["revision"]
        self.torch = torch
        self.tok = AutoTokenizer.from_pretrained(src, revision=rev)
        self.tok.padding_side = "right"
        self.model = AutoModelForCausalLM.from_pretrained(src, revision=rev, dtype=torch.bfloat16).to("cuda").eval()
        self.mid_layer = self.model.config.num_hidden_layers // 2
        self.batch_size = batch_size

    def embed(self, prompts: list[list[dict]]) -> tuple[np.ndarray, np.ndarray]:
        torch = self.torch
        texts = [self.tok.apply_chat_template(p, tokenize=False, add_generation_prompt=True, enable_thinking=False)
                 for p in prompts]
        lasts, mids = [], []
        for b in range(0, len(texts), self.batch_size):
            enc = self.tok(texts[b : b + self.batch_size], return_tensors="pt", padding=True,
                           add_special_tokens=False).to("cuda")
            with torch.no_grad():
                out = self.model(**enc, output_hidden_states=True)
            mask = enc["attention_mask"].unsqueeze(-1).float()
            for store, layer in ((lasts, -1), (mids, self.mid_layer)):
                h = out.hidden_states[layer].float()
                pooled = (h * mask).sum(1) / mask.sum(1)
                store.append(pooled.cpu().numpy())
        return _normalize(np.concatenate(lasts)), _normalize(np.concatenate(mids))


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--run", required=True)
    ap.add_argument("--model-tag", required=True, choices=sorted(C.MODELS))
    ap.add_argument("--model-path")
    ap.add_argument("--backend", choices=["hf", "fake"], default="hf")
    ap.add_argument("--batch-size", type=int, default=16)
    ap.add_argument("--limit-items", type=int, default=0, help="smoke only")
    ap.add_argument("--out-subdir", default="", help="smoke only: write emb_<subdir>")
    args = ap.parse_args(argv)
    run = Path(args.run)
    manifest = json.loads((run / "items" / "manifest.json").read_text())
    emb = FakeEmbedder() if args.backend == "fake" else HFEmbedder(args.model_tag, args.model_path, args.batch_size)
    set_ids, lasts, mids, ns = [], [], [], []
    for meta in manifest["sets"]:
        spec = C.sets_by_id()[meta["set_id"]]
        items = list(C.read_jsonl(run / "items" / f"{spec.file_stem}.jsonl"))
        if args.limit_items:
            items = items[: args.limit_items]
        last, mid = emb.embed([it["messages"] for it in items])
        set_ids.append(spec.set_id)
        lasts.append(last.mean(0))
        mids.append(mid.mean(0))
        ns.append(len(items))
        print(f"embedded {spec.set_id}: {len(items)} prompts", flush=True)
    out = run / (f"emb_{args.out_subdir}" if args.out_subdir else "emb") / args.model_tag / "centroids.npz"
    out.parent.mkdir(parents=True, exist_ok=True)
    np.savez(out, set_ids=np.array(set_ids), last=np.stack(lasts), mid=np.stack(mids), n=np.array(ns),
             backend=np.array(args.backend))
    print(f"wrote {out}", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
