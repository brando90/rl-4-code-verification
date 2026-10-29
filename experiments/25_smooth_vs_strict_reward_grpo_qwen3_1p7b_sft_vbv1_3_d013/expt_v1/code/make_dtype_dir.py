"""TLDR: Make a model directory that is the same checkpoint with config.json's dtype set to bfloat16 or float16 (symlinks for every other file), so vLLM and the trainer load the dtype under test.
Use before eval_local.sh or train_e25.py (train_e25.py calls make_dtype_dir() itself). Example: python3 make_dtype_dir.py <ckpt dir> <out dir> float16
"""
import json
import os
import sys
from pathlib import Path


def make_dtype_dir(src: str | Path, out: str | Path, dtype: str) -> Path:
    src, out = Path(src).resolve(), Path(out)
    out.mkdir(parents=True, exist_ok=True)
    for f in src.iterdir():
        if f.name == "config.json":
            continue
        link = out / f.name
        if not link.exists():
            os.symlink(f, link)
    cfg = json.loads((src / "config.json").read_text())
    cfg["torch_dtype"] = dtype
    cfg["dtype"] = dtype
    (out / "config.json").write_text(json.dumps(cfg, indent=2) + "\n")
    return out


if __name__ == "__main__":
    print(make_dtype_dir(sys.argv[1], sys.argv[2], sys.argv[3]))
