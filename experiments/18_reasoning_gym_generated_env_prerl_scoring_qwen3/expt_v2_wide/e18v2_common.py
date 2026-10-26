"""Shared, frozen definitions for experiment 18a v2 (wide): environment and target sets, seeds, models, prompts and rewards (PROTOCOL_v2.md).

Sampling, prompts, rewards and the target set are v1's (expt_v1/e18a_common.py); what changes is the environment list,
read from the frozen families_v2.json written by probe_families.py, and the models (0.6B and 1.7B only)."""

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
SAMPLING_SEED_BASE = 2000  # v1 used 1000; v2 samples are independent of v1's
PASS_EPS = 1e-9

LEVELS = (0, 1, 2, 3)
# Item seed of rg/<family>/L<level>: V2_SEED_BASE + 10 * k + level, k = position of the family in sorted(CURRICULA) of
# reasoning-gym 0.1.25 (102 names), so a seed never depends on which families pass the probe.
V2_SEED_BASE = 20262000
FAMILIES_FILE = Path(__file__).resolve().parent / "families_v2.json"
# v1's 8 families (expt_v1 TRAIN_FAMILIES), for the "does the 8-family picture hold" comparison.
V1_FAMILIES = ("basic_arithmetic", "leg_counting", "simple_equations", "coin_flip", "letter_counting", "word_sorting",
               "family_relationships", "mini_sudoku")

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


def all_curricula() -> list[str]:
    """Every Reasoning Gym family with a curriculum, sorted (the seed index k)."""
    ensure_pycosat()
    from reasoning_gym.factory import CURRICULA

    return sorted(CURRICULA)


def family_category(family: str) -> str:
    """Reasoning Gym's own category: the package the dataset class lives in (reasoning_gym.<category>.<module>)."""
    ensure_pycosat()
    from reasoning_gym.factory import DATASETS

    return DATASETS[family][0].__module__.split(".")[1]


def env_seed(family_k: int, level: int) -> int:
    return V2_SEED_BASE + 10 * family_k + level


def load_families(path: str | os.PathLike | None = None) -> list[dict]:
    """The frozen environment list: [{"family", "k", "category", "levels": [...]}, ...] in family order."""
    data = json.loads(Path(path or FAMILIES_FILE).read_text(encoding="utf-8"))
    return data["families"]


def all_sets(families: list[dict] | None = None) -> list[SetSpec]:
    """Sets in the frozen order: environments (family in families_v2.json order, then level), then the 6 targets."""
    fams = load_families() if families is None else families
    out: list[SetSpec] = []
    for f in fams:
        for lvl in f["levels"]:
            out.append(SetSpec(f"rg/{f['family']}/L{lvl}", len(out), "env", "rg", f["family"], f["category"], lvl,
                               env_seed(f["k"], lvl)))
    for fam, seed in TARGET_RG:
        out.append(SetSpec(f"rg/{fam}", len(out), "target", "rg", fam, "held-out", None, seed))
    out.append(SetSpec(GSM8K_ID, len(out), "target", "gsm8k", "gsm8k", "held-out", None, GSM8K_SELECT_SEED))
    return out


def sets_by_id() -> dict[str, SetSpec]:
    return {s.set_id: s for s in all_sets()}


def ensure_pycosat() -> None:
    """reasoning_gym imports pycosat at import time, but only zebra_puzzles uses it (excluded in v2, see the probe).

    pycosat 0.6.6 has no wheels; where it cannot be built (no C compiler) a stub that raises on use is
    registered so every other family imports and scores normally.
    """
    try:
        import pycosat  # noqa: F401
    except ImportError:
        stub = types.ModuleType("pycosat")

        def _missing(*_a, **_k):
            raise RuntimeError("pycosat is not installed; experiment 18a v2 excludes SAT-based families")

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
