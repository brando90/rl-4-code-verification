"""Shared, frozen definitions for experiment 18a: environment and target sets, seeds, models, prompts and rewards (PROTOCOL.md)."""

from __future__ import annotations

import dataclasses
import hashlib
import json
import os
import random
import re
import sys
import types
from pathlib import Path
from typing import Iterable, Iterator

RG_VERSION = "0.1.25"
N_ITEMS = 256
GROUP_SIZE = 16
MAX_TOKENS = 4096
MAX_MODEL_LEN = 8192
TEMPERATURE = 1.0
TOP_P = 1.0
TOP_K = -1
SAMPLING_SEED_BASE = 1000
PASS_EPS = 1e-9

# (idx, family, category); levels 0-3 each; item seed 20261020 + 10*idx + level.
TRAIN_FAMILIES = [
    (0, "basic_arithmetic", "arithmetic"),
    (1, "leg_counting", "arithmetic (word problem)"),
    (2, "simple_equations", "algebra"),
    (3, "coin_flip", "probability"),
    (4, "letter_counting", "algorithmic (string)"),
    (5, "word_sorting", "algorithmic (string)"),
    (6, "family_relationships", "graphs / relational"),
    (7, "mini_sudoku", "games"),
]
LEVELS = (0, 1, 2, 3)
TRAIN_SEED_BASE = 20261020

# Held-out target components: five RG families at their default config, then GSM8K test.
TARGET_RG = [
    ("gsm_symbolic", 20261120),
    ("calendar_arithmetic", 20261121),
    ("time_intervals", 20261122),
    ("syllogism", 20261123),
    ("base_conversion", 20261124),
]
GSM8K_ID = "gsm8k/test256"
GSM8K_REPO = "openai/gsm8k"
GSM8K_REVISION = "740312add88f781978c0658806c59bc2815b9866"
GSM8K_PARQUET = "main/test-00000-of-00001.parquet"
GSM8K_PARQUET_SHA256 = "ee7b8da9e381df27b9e3f7758a159ab2bdaa4dbaa910546cbbc47e0cb44e4f59"
GSM8K_N_TEST = 1319
GSM8K_SELECT_SEED = 20261020

MODELS = {
    "qwen3_0p6b": {"id": "Qwen/Qwen3-0.6B", "revision": "c1899de289a04d12100db370d81485cdf75e47ca", "size_b": 0.6},
    "qwen3_1p7b": {"id": "Qwen/Qwen3-1.7B", "revision": "70d244cc86ccca08cf5af4e1e306ecf908b1ad5e", "size_b": 1.7},
    "qwen3_4b": {"id": "Qwen/Qwen3-4B", "revision": "1cfa9a7208912126459214e8b04321603b3df60c", "size_b": 4.0},
}


@dataclasses.dataclass(frozen=True)
class SetSpec:
    """One prompt set: a training environment or a target component."""

    set_id: str
    set_index: int
    kind: str  # "env" or "target"
    source: str  # "rg" or "gsm8k"
    family: str
    category: str
    level: int | None
    seed: int

    @property
    def file_stem(self) -> str:
        return self.set_id.replace("/", "__")

    @property
    def sampling_seed(self) -> int:
        return SAMPLING_SEED_BASE + self.set_index


def all_sets() -> list[SetSpec]:
    """The 38 sets in the frozen order: 32 environments (family, then level), then 6 target components."""
    out: list[SetSpec] = []
    for idx, fam, cat in TRAIN_FAMILIES:
        for lvl in LEVELS:
            out.append(SetSpec(f"rg/{fam}/L{lvl}", len(out), "env", "rg", fam, cat, lvl, TRAIN_SEED_BASE + 10 * idx + lvl))
    for fam, seed in TARGET_RG:
        out.append(SetSpec(f"rg/{fam}", len(out), "target", "rg", fam, "held-out", None, seed))
    out.append(SetSpec(GSM8K_ID, len(out), "target", "gsm8k", "gsm8k", "held-out", None, GSM8K_SELECT_SEED))
    return out


def sets_by_id() -> dict[str, SetSpec]:
    return {s.set_id: s for s in all_sets()}


def ensure_pycosat() -> None:
    """reasoning_gym imports pycosat at import time, but only zebra_puzzles uses it (not in this experiment).

    pycosat 0.6.6 has no wheels; where it cannot be built (no C compiler) a stub that raises on use is
    registered so the 11 families used here import and score normally.
    """
    try:
        import pycosat  # noqa: F401
    except ImportError:
        stub = types.ModuleType("pycosat")

        def _missing(*_a, **_k):
            raise RuntimeError("pycosat is not installed; experiment 18a never uses SAT-based families")

        stub.solve = _missing
        stub.itersolve = _missing
        sys.modules["pycosat"] = stub


def system_prompt() -> str:
    ensure_pycosat()
    from reasoning_gym.utils import SYSTEM_PROMPTS

    return SYSTEM_PROMPTS["default"]


def rg_dataset(spec: SetSpec, size: int):
    """Build the Reasoning Gym dataset for a set exactly as frozen (UPPER_BOUND curriculum level or default config)."""
    ensure_pycosat()
    from reasoning_gym.coaching.base_curriculum import DefaultCurriculumContext, RangeAttributeMode
    from reasoning_gym.factory import DATASETS, create_curriculum, create_dataset

    if spec.source != "rg":
        raise ValueError(f"{spec.set_id} is not a Reasoning Gym set")
    if spec.level is None:
        return create_dataset(spec.family, seed=spec.seed, size=size)
    cur = create_curriculum(spec.family)
    cur.set_global_level(spec.level)
    cfg = cur.generate_configuration(
        {"seed": spec.seed, "size": size}, context=DefaultCurriculumContext(mode=RangeAttributeMode.UPPER_BOUND)
    )
    return DATASETS[spec.family][0](cfg)


def rg_config_dict(ds) -> dict:
    return json.loads(json.dumps(dataclasses.asdict(ds.config), default=str))


def gsm8k_select(n_rows: int, n_items: int) -> list[int]:
    return sorted(random.Random(GSM8K_SELECT_SEED).sample(range(n_rows), n_items))


def gsm8k_gold(answer_field: str) -> str:
    """The number after '####' in a GSM8K answer, commas removed."""
    return answer_field.split("####")[-1].strip().replace(",", "")


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def extract_answer(text: str | None) -> str | None:
    ensure_pycosat()
    from reasoning_gym.utils import extract_answer as rg_extract

    if text is None:
        return None
    return rg_extract(text)


_NUM = re.compile(r"-?\d+(?:\.\d+)?")


def gsm8k_score(extracted: str | None, gold: str) -> float:
    """Exact numeric match: last number in the extracted answer (commas, $ and spaces removed) equals the gold number."""
    if extracted is None:
        return 0.0
    cleaned = extracted.replace(",", "").replace("$", "").replace(" ", "")
    nums = _NUM.findall(cleaned)
    if not nums:
        return 0.0
    try:
        return 1.0 if abs(float(nums[-1]) - float(gold)) < 1e-6 else 0.0
    except ValueError:
        return 0.0


def is_pass(score: float) -> bool:
    return score >= 1.0 - PASS_EPS


def messages_for(question: str, sys_prompt: str) -> list[dict]:
    return [{"role": "system", "content": sys_prompt}, {"role": "user", "content": question}]


def read_jsonl(path: str | os.PathLike) -> Iterator[dict]:
    with open(path, encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if line:
                yield json.loads(line)


def write_jsonl_atomic(path: str | os.PathLike, rows: Iterable[dict]) -> int:
    """Write rows to path via a temporary file and rename, so a partial file never looks complete."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    n = 0
    with open(tmp, "w", encoding="utf-8") as fh:
        for row in rows:
            fh.write(json.dumps(row, ensure_ascii=False) + "\n")
            n += 1
    os.replace(tmp, path)
    return n


def write_json_atomic(path: str | os.PathLike, obj) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(obj, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    os.replace(tmp, path)


def repo_src() -> Path:
    """The repository's src/ (for rl4cv.experience), found relative to this file."""
    return Path(__file__).resolve().parents[3] / "src"


def select_sets(spec: str | None) -> list[SetSpec]:
    """Comma-separated set ids, or None/'all' for every set."""
    sets = all_sets()
    if not spec or spec == "all":
        return sets
    wanted = [s.strip() for s in spec.split(",") if s.strip()]
    by_id = sets_by_id()
    missing = [w for w in wanted if w not in by_id]
    if missing:
        raise SystemExit(f"unknown set ids: {missing}")
    return [by_id[w] for w in wanted]


def shard_sets(sets: list[SetSpec], shard: int, nshards: int) -> list[SetSpec]:
    """Round-robin shard so every shard mixes short and long sets."""
    if not 0 <= shard < nshards:
        raise ValueError("shard must lie in [0, nshards)")
    return [s for i, s in enumerate(sets) if i % nshards == shard]
