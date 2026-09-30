"""Prospective forecast freezing: serialize a forecast canonically, hash it, and log it before outcomes exist.

The paper's evidence rests on chronology (Appendix B): each forecast was serialized with a
SHA-256 hash before the corresponding RL outcomes were observed. This module makes that step
mechanical so a forecast cannot be silently edited after the fact.
"""

from __future__ import annotations

import datetime as _dt
import hashlib
import json
import subprocess
from pathlib import Path
from typing import Any


def canonical_json(obj: Any) -> str:
    """Deterministic JSON text: sorted keys, no insignificant whitespace, UTF-8 characters kept."""
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False)


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _git_head(cwd: Path) -> str | None:
    try:
        out = subprocess.run(["git", "rev-parse", "HEAD"], cwd=cwd, capture_output=True, text=True, check=True)
        return out.stdout.strip()
    except (OSError, subprocess.CalledProcessError):
        return None


def freeze_forecast(forecast: dict, out_dir: str | Path, name: str, *, outcomes_observed: bool = False) -> dict:
    """Write `<name>.json` plus its hash and append a ledger line; refuse to overwrite a frozen forecast.

    `outcomes_observed` must be False: freezing after the outcomes exist defeats the purpose,
    so the caller has to assert, in code, that no outcome for this forecast has been read.
    """
    if outcomes_observed:
        raise ValueError("a prospective forecast must be frozen before its outcomes are observed")
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    path = out / f"{name}.json"
    if path.exists():
        raise FileExistsError(f"{path} already exists; frozen forecasts are append-only")
    text = canonical_json(forecast)
    digest = sha256_text(text)
    path.write_text(text + "\n", encoding="utf-8")
    (out / f"{name}.sha256").write_text(f"{digest}  {path.name}\n", encoding="utf-8")
    entry = {
        "name": name,
        "file": path.name,
        "sha256": digest,
        "frozen_at_utc": _dt.datetime.now(_dt.timezone.utc).isoformat(timespec="seconds"),
        "git_head": _git_head(out),
    }
    with (out / "forecast_ledger.jsonl").open("a", encoding="utf-8") as fh:
        fh.write(canonical_json(entry) + "\n")
    return entry


def verify_forecast(path: str | Path) -> bool:
    """Recompute the hash of a frozen forecast file and compare it to its recorded `.sha256` sidecar."""
    p = Path(path)
    recorded = p.with_suffix(".sha256").read_text(encoding="utf-8").split()[0]
    text = p.read_text(encoding="utf-8").rstrip("\n")
    return sha256_text(text) == recorded
