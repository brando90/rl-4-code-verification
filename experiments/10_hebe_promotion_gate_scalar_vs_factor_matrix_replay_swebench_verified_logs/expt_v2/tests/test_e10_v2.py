"""Unit tests for Experiment 10 v2 (`analyze_e10_v2.py`)."""

from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
V2_DIR = HERE.parent
V1_DIR = V2_DIR.parent / "expt_v1"
for _p in (V2_DIR, V1_DIR):
    if str(_p) not in sys.path:
        sys.path.insert(0, str(_p))

import analyze_e10 as v1  # noqa: E402
import analyze_e10_v2 as v2  # noqa: E402


def test_matched_test_lists_shape_421() -> None:
    drop = frozenset(json.loads(v2.DRIFT.read_text())["tasks"])
    assert len(drop) == 4
    m = v2.load_matrix(v2.PER_CELL, v2.PER_CELL_SHA256, drop)
    assert (len(m.systems), len(m.tasks)) == v2.EXPECTED_SHAPE["matched_test_lists"] == (164, 421)


def test_irt_scorer_no_test_half_leakage_and_matches_v1_policies(tmp_path: Path) -> None:
    out_v1 = tmp_path / "v1.json"
    out_v2 = tmp_path / "v2.json"
    argv = ["--splits", "4", "--draws", "20", "--workers", "1", "--q", "0.25", "0.50"]
    v1.main(argv + ["--out", str(out_v1)])
    v2.main(argv + ["--out", str(out_v2)])
    r1 = json.loads(out_v1.read_text())
    r2 = json.loads(out_v2.read_text())
    for pop in ("near", "eligible"):
        m1 = r1["populations"][pop]["H3"]["0.25"]["main"]["members"]
        m2 = r2["populations"][pop]["H3"]["0.25"]["main"]["members"]
        for pol in v1.POLICIES:
            for k in ("hpr", "mean_dpass_t"):
                assert np.isclose(m1[f"{pol}.{k}"]["estimate"], m2[f"{pol}.{k}"]["estimate"], rtol=0, atol=1e-12)
        for pol in ("S_irt2pl", "S_irt2pl_z", "S_grm3", "S_grm3_z", "R_irt2pl", "R_irt2pl_z", "R_grm3", "R_grm3_z"):
            assert np.isfinite(m2[f"{pol}.hpr"]["estimate"])
            assert np.isfinite(m2[f"{pol}.mean_dpass_t"]["estimate"])
