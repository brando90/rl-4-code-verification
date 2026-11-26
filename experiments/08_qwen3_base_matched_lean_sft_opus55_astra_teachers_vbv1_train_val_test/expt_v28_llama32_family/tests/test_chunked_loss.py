"""TLDR: chunked_lm_loss equals the HF labels loss (value and gradient) on a short Gemma-3 example, CPU, float32.
usage (Sherlock, from the package folder, after prepare): python3 tests/test_chunked_loss.py gemma1b"""
import json
import sys
from pathlib import Path

import torch
from transformers import AutoModelForCausalLM

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import train_v28 as t

arm = sys.argv[1] if len(sys.argv) > 1 else "gemma1b"
receipt = json.loads((t.ROOT / "prepare_receipt.json").read_text())
rows = torch.load(t.ROOT / "data/tokens_gemma3.pt", weights_only=True)
row = sorted(rows, key=lambda r: len(r["ids"]))[5]
ids = torch.tensor([row["ids"][:700]], dtype=torch.long)
prompt = min(row["prompt"], 300)
labels = ids.clone()
labels[:, :prompt] = -100
model = AutoModelForCausalLM.from_pretrained(receipt["models"][arm]["model_path"], local_files_only=True, torch_dtype=torch.float32,
                                             attn_implementation="eager")
model.train()
a = model(input_ids=ids, labels=labels).loss
a.backward()
ga = {n: p.grad.clone() for n, p in model.named_parameters() if p.grad is not None}
model.zero_grad(set_to_none=True)
b = t.chunked_lm_loss(model, ids, prompt, chunk=128)
b.backward()
worst = max(float((p.grad - ga[n]).abs().max() / (ga[n].abs().max() + 1e-12)) for n, p in model.named_parameters() if n in ga)
print(json.dumps({"hf_loss": float(a), "chunked_loss": float(b), "abs_diff": abs(float(a) - float(b)), "worst_rel_grad_diff": worst,
                  "params_with_grad": len(ga)}))
assert abs(float(a) - float(b)) < 1e-4 and worst < 1e-3
print("PASS")
