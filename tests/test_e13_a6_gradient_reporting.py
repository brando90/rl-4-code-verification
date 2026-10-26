"""Keep actual zero gradients distinct from optimizer steps and unavailable updates."""
from pathlib import Path
import importlib.machinery,importlib.util
import pytest
import sys
P=Path(__file__).resolve().parents[1]/'experiments/13_irt_scsc_factor_guided_vs_direct_pass1_rl_sft_qwen3_vbv1_d013/expt_v2/phase2'
sys.path.insert(0,str(P))
import a6_gradient_reporting as m
def row(norm):return {'condition':'v2-S2','status':'MEASURED','optimizer_updates':1,'counts':{'usable_groups':32,'nonzero_advantage_slots':0 if norm==0 else 8},'metrics':{'grad_norm':[norm]},'before_parameters':'before','after_parameters':'different_after_decay'}
def test_weight_decay_is_not_nonzero_gradient():
 r=m.summarize([row(0),row(.3),{'condition':'v2-S2','status':'UNMEASURED','optimizer_updates':0,'counts':{'usable_groups':0,'nonzero_advantage_slots':0}}])
 assert r['optimizer_updates']==2 and r['nonzero_gradient_updates']==1 and r['zero_gradient_updates']==1 and r['gradient_unavailable_updates']==1
@pytest.mark.parametrize('norm',[float('nan'),float('inf'),-1,None])
def test_invalid_norm_not_reported_as_zero(norm):
 with pytest.raises(ValueError):m.summarize([row(norm)])
