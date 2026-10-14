"""Preserve capped successes, frozen extraction, missing denominators and train-only anchor scoring."""
import json
import os
from pathlib import Path
import sys
from types import SimpleNamespace

import pytest

ROOT = Path(__file__).resolve().parents[1]
PHASE = ROOT/'experiments/13_irt_scsc_factor_guided_vs_direct_pass1_rl_sft_qwen3_vbv1_d013/expt_v2/phase1'
sys.path.insert(0,str(PHASE))
import score_anchor as S


def test_missing_scores_keep_full_denominator_without_zero_imputation():
    rows = [{'cell_id':'a','status':'measured','strict':1,'at_token_cap':True},
            {'cell_id':'b','status':'measured','strict':0,'at_token_cap':False},
            {'cell_id':'c','status':'missing_generation'},
            {'cell_id':'d','status':'deterministic_resource_limit'}]
    result = S.summarize(rows,4)
    assert result['status']=='INCOMPLETE' and result['measured']==2
    assert result['strict_full_denominator_bounds']==[.25,.75]
    assert result['capped_measured']==1
    with pytest.raises(ValueError,match='denominator'):S.summarize(rows[:-1],4)
    with pytest.raises(ValueError,match='denominator'):S.summarize(rows[:3]+[rows[0]],4)


def test_test_split_refused_before_extraction(tmp_path,monkeypatch):
    import rl4cv.veribench.exp103 as E
    monkeypatch.setattr(E,'extract_lean',lambda *a,**k:pytest.fail('sealed extraction'))
    with pytest.raises(ValueError,match='train-only'):
        S.score_one({'split':'test','batch':'base'},tmp_path,{})


def test_source_and_cap_reach_independent_oracle_unchanged(tmp_path,monkeypatch):
    import rl4cv.veribench.exp103 as E
    source='def x : Nat := 1\n';seen=[]
    monkeypatch.setattr(E,'extract_lean',lambda *a,**k:SimpleNamespace(lean=source,method='fixture',unmapped=()))
    def inspect(path,**kw):
        seen.append((path.read_text(),kw))
        evidence=kw['evidence']/'oracle';evidence.mkdir(parents=True)
        (evidence/'oracle.json').write_text(json.dumps({'compile':True,'vacuity':{'unparseable':[]},
            'scored_response':{'n_theorems_stated':1,'n_theorems_proved':1}}))
        return {'strict':1,'strict_status':'scored','e':1,'n_examples':1,
                'p':{'numerator':1,'denominator':1},'raw_vacuity_hits':0}
    monkeypatch.setattr(S,'inspect_source',inspect)
    row={'split':'train','batch':'full1','completion':'raw completion','required_paths':['solution.lean'],'at_token_cap':True}
    result=S.score_one(row,tmp_path,{'veribench':'fixture','lake':'fixture','scorer':'fixture'})
    assert result['strict']==1 and result['at_token_cap'] and result['q1'] and result['honest']
    assert seen[0][0]==source and seen[0][1]['truncated'] is True
    assert seen[0][1]['expected_sha256']==S.digest(tmp_path/'solution.lean')
    with pytest.raises(FileExistsError):S.score_one(row,tmp_path,{'veribench':'fixture'})


def test_real_frozen_extraction_and_lean_keep_capped_success(tmp_path):
    keys=('VERIBENCH_ROOT','E13_LAKE_DIR','E13_SCORER_ROOT')
    if not all(os.environ.get(k) and Path(os.environ[k]).exists() for k in keys):
        if os.environ.get('E13_REQUIRE_LEAN_INTEGRATION')=='1':pytest.fail('required Lean routes missing')
        pytest.skip('pinned Lean routes unavailable')
    fixture=ROOT/'experiments/13_irt_scsc_factor_guided_vs_direct_pass1_rl_sft_qwen3_vbv1_d013/expt_v2/R0_attempt_2/fixtures/valid.lean'
    if not fixture.exists():
        fixture=Path('/lfs/skampere1/0/brando9/agent-recovery-10-09-2026/workers/rl4cv13_review/phase0_controls/fixtures/valid.lean')
    row={'split':'train','batch':'base','completion':'```lean\n'+fixture.read_text()+'\n```',
         'required_paths':['solution.lean'],'at_token_cap':True}
    result=S.score_one(row,tmp_path,{'veribench':os.environ['VERIBENCH_ROOT'],
                                    'lake':os.environ['E13_LAKE_DIR'],'scorer':os.environ['E13_SCORER_ROOT']})
    assert result['status']=='measured' and result['strict']==1 and result['at_token_cap']
    assert result['q1'] and result['compile'] and result['honest']
