"""Load experiment 103's single-call prompt and extraction rule from a pinned VeriBench checkout.

Experiment 103 (`veribench/experiments/103_single_call_baselines_all_models_vbv1_vbv2_valkyrie_validated_fsc_judge`)
is the only VeriBench table with every factor measured by the validated FSC judge for
single-call (no-agent) solvers, including one open-weight model (Qwen3.6-27B). Reusing its
exact user prompt (pack instruction + "\\n\\n---\\n\\n" + addendum), system prompt and
`extract_files` rule keeps small-model baselines comparable with that table.
"""

from __future__ import annotations

import hashlib
import importlib.util
import os
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from types import ModuleType

EXP103_DIR = "experiments/103_single_call_baselines_all_models_vbv1_vbv2_valkyrie_validated_fsc_judge"
SINGLE_CALL_REL = f"{EXP103_DIR}/scripts/valkyrie_single_call_agent/single_call.py"
ADDENDUM_REL = f"{EXP103_DIR}/scripts/valkyrie_single_call_agent/prompts/addendum_{{name}}.md"


def veribench_root(explicit: str | os.PathLike | None = None) -> Path:
    """Resolve the pinned VeriBench checkout: argument, then $VERIBENCH_ROOT, then external/veribench."""
    for cand in (explicit, os.environ.get("VERIBENCH_ROOT"), Path(__file__).resolve().parents[3] / "external" / "veribench"):
        if cand and (Path(cand) / SINGLE_CALL_REL).is_file():
            return Path(cand)
    raise FileNotFoundError(
        "VeriBench checkout not found; run scripts/setup_external.sh or set VERIBENCH_ROOT "
        f"to a checkout containing {SINGLE_CALL_REL}"
    )


@lru_cache(maxsize=4)
def load_single_call(root: str) -> ModuleType:
    """Import experiment 103's single_call.py as a module (it defines constants and functions only)."""
    path = Path(root) / SINGLE_CALL_REL
    spec = importlib.util.spec_from_file_location("vb103_single_call", path)
    if spec is None or spec.loader is None:
        raise ImportError(f"cannot import {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def sha256(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


@dataclass(frozen=True)
class Prompt:
    system: str
    user: str
    required_paths: tuple[str, ...]
    instruction_sha256: str
    addendum_sha256: str
    prompt_sha256: str
    system_prompt_sha256: str

    def messages(self) -> list[dict]:
        return [{"role": "system", "content": self.system}, {"role": "user", "content": self.user}]


def build_prompt(instruction: str, *, addendum: str = "vbv1", root: str | os.PathLike | None = None) -> Prompt:
    """Experiment 103's exact messages for one task instruction."""
    r = veribench_root(root)
    mod = load_single_call(str(r))
    add_text = (r / ADDENDUM_REL.format(name=addendum)).read_text(encoding="utf-8")
    user = instruction.rstrip() + "\n\n---\n\n" + add_text
    expected = mod.required_paths(instruction, addendum)
    if not expected:
        raise ValueError("the instruction declares no output path; experiment 103 would not spend a call on it")
    return Prompt(
        system=mod.SYSTEM_PROMPT,
        user=user,
        required_paths=tuple(expected),
        instruction_sha256=sha256(instruction),
        addendum_sha256=sha256(add_text),
        prompt_sha256=sha256(user),
        system_prompt_sha256=sha256(mod.SYSTEM_PROMPT),
    )


@dataclass(frozen=True)
class Extraction:
    lean: str | None
    method: str
    unmapped: tuple[str, ...]


def extract_lean(completion: str, required_paths: tuple[str, ...], *, addendum: str = "vbv1", root: str | os.PathLike | None = None) -> Extraction:
    """Apply experiment 103's `extract_files` + `resolve_paths` and return the single required file."""
    mod = load_single_call(str(veribench_root(root)))
    policy = mod.PATH_POLICIES[addendum]
    files, method = mod.extract_files(completion, list(required_paths))
    resolved, unmapped = mod.resolve_paths(files, list(required_paths), root=policy["root"], max_files=policy["max_files"])
    lean = resolved.get(required_paths[0]) if required_paths else None
    return Extraction(lean=lean if (lean and lean.strip()) else None, method=method, unmapped=tuple(sorted(unmapped)))


def clean_finish(finish_reason: str | None) -> bool:
    """Experiment 103 counts a cell as measured only for these finish reasons; vLLM reports 'stop' or 'length'."""
    return (finish_reason or "") in {"stop", "end_turn", "completed", "finished", "eos"}
