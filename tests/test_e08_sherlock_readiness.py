"""Check that incomplete, duplicate and saturated cohorts cannot be mistaken for RL readiness."""
import importlib.util
from pathlib import Path
import pytest

P=Path(__file__).resolve().parents[1]/"experiments/08_qwen3_base_matched_lean_sft_opus55_astra_teachers_vbv1_train_val_test/expt_v4/validation/readiness.py"
spec=importlib.util.spec_from_file_location("sherlock_readiness",P)
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
IDS=[f"task{i}" for i in range(135)]
def rows():
    return [dict(task_id=t,sample_idx=k,binary_success=int(i<7 and k==0),extracted=True,capped=False) for i,t in enumerate(IDS) for k in range(8)]
def test_exact_gate_and_histogram():
    r=m.summarize(rows(),IDS)
    assert r["readiness"]=="PASS" and r["mixed_tasks"]==7
    assert r["success_count_histogram"]=={str(k): (128 if k==0 else 7 if k==1 else 0) for k in range(9)}
def test_missing_is_unknown_not_zero():
    r=m.summarize(rows()[:-1],IDS)
    assert r["readiness"]=="INCOMPLETE" and r["known_cells"]==1079
    assert "success_rate" not in r
def test_duplicates_and_unknowns_fail_closed():
    with pytest.raises(AssertionError):m.summarize(rows()+rows()[:1],IDS)
    r=rows();r[0]["binary_success"]=float("nan")
    with pytest.raises(AssertionError):m.summarize(r,IDS)
def test_high_accuracy_is_not_a_mixed_group():
    r=rows()
    for cell in r:cell["binary_success"]=1
    s=m.summarize(r,IDS)
    assert s["success_rate"]==1 and s["mixed_tasks"]==0 and s["readiness"]=="FAIL"
def test_format_and_cap_boundaries():
    r=rows()
    for c in r[:108]:c["extracted"]=False;c["capped"]=True
    assert m.summarize(r,IDS)["readiness"]=="PASS"
    r[108]["capped"]=True
    assert m.summarize(r,IDS)["gates"]["truncation"] is False
    r[108]["extracted"]=False
    assert m.summarize(r,IDS)["gates"]["extraction"] is False
