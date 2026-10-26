"""Build the frozen item files for experiment 18a v2: every environment in families_v2.json and v1's 6-part target set (CPU only).

Writes <out>/items/<set>.jsonl (one row per item: question, its sha256, the chat messages, the gold answer) and
<out>/items/manifest.json (configs, seeds, hashes). Usage:

    python build.py --out ~/e18a_v2/run --gsm8k-parquet ~/e18a/gsm8k_test.parquet
"""

from __future__ import annotations

import argparse
import hashlib
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import e18v2_common as C  # noqa: E402


def load_gsm8k(parquet: str | None, jsonl: str | None) -> tuple[list[dict], str]:
    """GSM8K test rows (question, answer) and the source file's sha256."""
    if jsonl:
        path = Path(jsonl)
        rows = list(C.read_jsonl(path))
    elif parquet:
        import pyarrow.parquet as pq

        path = Path(parquet)
        rows = pq.read_table(path).to_pylist()
    else:
        raise SystemExit("GSM8K needs --gsm8k-parquet (or --gsm8k-jsonl in tests)")
    return rows, hashlib.sha256(path.read_bytes()).hexdigest()


def build_set(spec: C.SetSpec, n_items: int, sys_prompt: str, gsm8k_rows: list[dict] | None) -> tuple[list[dict], dict]:
    rows: list[dict] = []
    meta: dict = {"set_id": spec.set_id, "set_index": spec.set_index, "kind": spec.kind, "source": spec.source,
                  "family": spec.family, "category": spec.category, "level": spec.level, "seed": spec.seed,
                  "sampling_seed": spec.sampling_seed, "n_items": n_items}
    if spec.source == "rg":
        ds = C.rg_dataset(spec, n_items)
        meta["rg_config"] = C.rg_config_dict(ds)
        for i in range(n_items):
            entry = ds[i]
            q = entry["question"]
            rows.append({"set_id": spec.set_id, "item_id": f"{spec.set_id}#{i}", "idx": i, "question": q,
                         "question_sha256": C.sha256_text(q), "gold": str(entry["answer"]),
                         "messages": C.messages_for(q, sys_prompt)})
    else:
        if gsm8k_rows is None:
            raise SystemExit("GSM8K rows missing")
        picks = C.gsm8k_select(len(gsm8k_rows), n_items)
        meta["gsm8k_indices"] = picks
        for i, j in enumerate(picks):
            q = gsm8k_rows[j]["question"]
            rows.append({"set_id": spec.set_id, "item_id": f"{spec.set_id}#{j}", "idx": j, "question": q,
                         "question_sha256": C.sha256_text(q), "gold": C.gsm8k_gold(gsm8k_rows[j]["answer"]),
                         "messages": C.messages_for(q, sys_prompt)})
    golds = [r["gold"] for r in rows]
    meta["unique_questions"] = len({r["question"] for r in rows})
    meta["top_answer_share"] = max(golds.count(g) for g in set(golds)) / len(golds) if golds else None
    meta["items_sha256"] = hashlib.sha256("".join(r["question_sha256"] for r in rows).encode()).hexdigest()
    return rows, meta


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--out", required=True, help="run directory; items go to <out>/items")
    ap.add_argument("--gsm8k-parquet", help="openai/gsm8k main test parquet at the pinned revision")
    ap.add_argument("--gsm8k-jsonl", help="tests only: GSM8K-like rows with question/answer")
    ap.add_argument("--n-items", type=int, default=C.N_ITEMS, help="items per set (frozen: 256; smaller only for tests/smoke)")
    ap.add_argument("--sets", default="all", help="comma-separated set ids (default all)")
    ap.add_argument("--probe", help="probe_v2.jsonl whose item hashes the build must reproduce (default: next to this file)")
    ap.add_argument("--allow-unpinned-gsm8k", action="store_true", help="tests only: skip the parquet sha256 check")
    args = ap.parse_args(argv)

    import importlib.metadata as md

    sys_prompt = C.system_prompt()

    rg_version = md.version("reasoning-gym")
    if rg_version != C.RG_VERSION:
        raise SystemExit(f"reasoning-gym {rg_version} installed; the protocol pins {C.RG_VERSION}")
    sets = C.select_sets(args.sets)
    gsm8k_rows, gsm8k_sha = (None, None)
    if any(s.source == "gsm8k" for s in sets):
        gsm8k_rows, gsm8k_sha = load_gsm8k(args.gsm8k_parquet, args.gsm8k_jsonl)
        if args.gsm8k_parquet and not args.allow_unpinned_gsm8k and gsm8k_sha != C.GSM8K_PARQUET_SHA256:
            raise SystemExit(f"GSM8K parquet sha256 {gsm8k_sha} != pinned {C.GSM8K_PARQUET_SHA256}")
    items_dir = Path(args.out) / "items"
    manifest = {"schema": "items_18a_v2/v1", "rg_version": rg_version, "n_items": args.n_items,
                "group_size": C.GROUP_SIZE, "system_prompt_sha256": C.sha256_text(sys_prompt),
                "gsm8k": {"repo": C.GSM8K_REPO, "revision": C.GSM8K_REVISION, "file_sha256": gsm8k_sha},
                "models": C.MODELS, "sets": []}
    probe_path = Path(args.probe or Path(__file__).resolve().parent / "probe_v2.jsonl")
    probe_sha = ({r["env_id"]: r.get("items_sha256") for r in C.read_jsonl(probe_path)}
                 if probe_path.exists() and args.n_items == C.N_ITEMS else {})
    for spec in sets:
        rows, meta = build_set(spec, args.n_items, sys_prompt, gsm8k_rows)
        want = probe_sha.get(spec.set_id)
        if want and want != meta["items_sha256"]:
            raise SystemExit(f"{spec.set_id}: items differ from the frozen probe ({meta['items_sha256'][:12]} != {want[:12]})")
        C.write_jsonl_atomic(items_dir / f"{spec.file_stem}.jsonl", rows)
        manifest["sets"].append(meta)
        print(f"built {spec.set_id}: {len(rows)} items, sha {meta['items_sha256'][:12]}", flush=True)
    C.write_json_atomic(items_dir / "manifest.json", manifest)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
