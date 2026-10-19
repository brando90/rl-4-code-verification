"""Check admitted reward signal, serialized results, and full-cohort integrity."""
import csv
import importlib.util
import json
from pathlib import Path

import pytest

SOURCE = Path(__file__).resolve().parents[1] / "experiments/08_qwen3_base_matched_lean_sft_opus55_astra_teachers_vbv1_train_val_test/expt_v12/rl_signal_audit/signal_audit.py"
spec = importlib.util.spec_from_file_location("signal_audit", SOURCE)
audit = importlib.util.module_from_spec(spec)
spec.loader.exec_module(audit)


def cohort(tmp_path, capped=False):
    ids = tmp_path / "ids.txt"
    ids.write_text("\n".join(f"task{i}" for i in range(135)) + "\n")
    cells = tmp_path / "cells.csv"
    rows = [dict(task_id=f"task{i}", sample_idx=k,
                 binary_success=int(i == 0 and k == 0),
                 generated_tokens=10, capped=str(capped))
            for i in range(135) for k in range(8)]
    with cells.open("w") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    return cells, ids


def test_serialization_and_known_signal(tmp_path):
    cells, ids = cohort(tmp_path)
    result = audit.audit(cells, ids, tmp_path / "out")
    saved = json.loads((tmp_path / "out/summary.json").read_text())
    assert saved == result
    assert saved["nonzero_admitted_advantages"] == 8
    assert saved["measurement"]["rho"] == pytest.approx(2e6 / 10800)
    assert saved["measurement"]["H"] == pytest.approx(1 / 135)


def test_capped_answers_remain_in_baseline_but_supply_no_loss(tmp_path):
    cells, ids = cohort(tmp_path, capped=True)
    result = audit.audit(cells, ids, tmp_path / "out")
    assert result["nonzero_advantages"] == 8
    assert result["nonzero_admitted_advantages"] == 0
    assert result["measurement"]["rho_raw"] > 0
    assert result["measurement"]["rho"] == 0
    assert result["ci95"]["rho"] == result["ci95"]["H"] == [0, 0]
    assert result["verdict"] == "NO_ADMITTED_SIGNAL"


def test_duplicate_cell_rejected(tmp_path):
    cells, ids = cohort(tmp_path)
    lines = cells.read_text().splitlines()
    lines[-1] = lines[1]
    cells.write_text("\n".join(lines) + "\n")
    with pytest.raises(AssertionError):
        audit.audit(cells, ids, tmp_path / "out")
