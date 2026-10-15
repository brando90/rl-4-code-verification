"""Check immutable scoring identity, bounded recovery and the actual frozen oracle on authored Lean."""
import importlib.machinery
import importlib.util
import json
import os
from pathlib import Path
import sys
import pytest

ROOT=Path(__file__).resolve().parents[1]
PHASE=ROOT/'experiments/13_irt_scsc_factor_guided_vs_direct_pass1_rl_sft_qwen3_vbv1_d013/expt_v2/phase2'
sys.path.insert(0,str(PHASE))
spec=importlib.util.spec_from_file_location('e13_score_evaluation',PHASE/'score_evaluation.py')
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)


def fixture(tmp_path):
    cell={'cell_id':'A/13011/4/test/authored/0','task_id':'authored','split':'test','sample_idx':0,
          'arm':'A','run_seed':13011,'boundary':4,'prompt_token_ids':[12,13],'required_paths':['solution.lean']}
    ids=tmp_path/'test.txt';ids.write_text('authored\n')
    source=tmp_path/'generation.json';source.write_text(json.dumps(cell))
    config={'allowlist':str(ids),'split':'test','purpose':'test','root':str(tmp_path/'scores')}
    bindings={cell['cell_id']:{'path':str(source),'sha256':m.digest(source)}}
    return cell,config,bindings


def executor(calls,failures):
    def run(job,root,attempt,slots):
        calls.append(job)
        row={**job['identity'],'cleanup_verified':True}
        if len(calls)<=failures:row.update(status='unresolved_measurement',error_type='OSError')
        else:row.update(status='measured',strict=1)
        m.write_new(root/'result.json',row);return row
    return run


def test_one_identical_retry_then_completed_receipt_is_never_rescored(tmp_path):
    cell,config,bindings=fixture(tmp_path);calls=[]
    result=m.score_cell(cell,0,config,bindings,'locked',None,executor=executor(calls,1))
    assert result['strict']==1 and result['attempts']==2 and len(calls)==2
    assert calls[0]['generation']==calls[1]['generation'] and calls[0]['generation_sha256']==calls[1]['generation_sha256']
    assert m.score_cell(cell,0,config,bindings,'locked',None,executor=lambda *a:pytest.fail('rescore'))==result
    with pytest.raises(ValueError,match='binding changed'):m.score_cell(cell,0,config,bindings,'different',None)


def test_exhausted_cell_stays_missing_and_generation_missing_cannot_be_replaced(tmp_path):
    cell,config,bindings=fixture(tmp_path);calls=[]
    result=m.score_cell(cell,0,config,bindings,'locked',None,executor=executor(calls,2))
    assert result['strict'] is None and result['attempts']==2 and len(calls)==2
    config['root']=str(tmp_path/'missing')
    result=m.score_cell(cell,0,config,{cell['cell_id']:None},'locked',None)
    assert result['strict'] is None and result['attempts']==0
    with pytest.raises(ValueError,match='binding changed'):m.score_cell(cell,0,config,bindings,'locked',None)


def test_wrong_split_refused_before_source_extraction(tmp_path,monkeypatch):
    cell,config,bindings=fixture(tmp_path);cell['split']='validation'
    import rl4cv.veribench.exp103 as extraction
    monkeypatch.setattr(extraction,'extract_lean',lambda *a,**k:pytest.fail('wrong split read'))
    with pytest.raises(ValueError,match='outside'):m.score_one(cell,tmp_path,config)


def test_real_frozen_oracle_retains_capped_evaluation_success(tmp_path):
    required=('VERIBENCH_ROOT','E13_LAKE_DIR','E13_SCORER_ROOT')
    if not all(os.environ.get(k) and Path(os.environ[k]).exists() for k in required):
        if os.environ.get('E13_REQUIRE_LEAN_INTEGRATION')=='1':pytest.fail('required Lean routes missing')
        pytest.skip('pinned Lean routes unavailable')
    cell,config,bindings=fixture(tmp_path)
    authored=PHASE.parent/'R0_attempt_2/fixtures/valid.lean'
    cell.update(completion='```lean\n'+authored.read_text()+'\n```',at_token_cap=True)
    config.update(veribench=os.environ['VERIBENCH_ROOT'],lake=os.environ['E13_LAKE_DIR'],scorer=os.environ['E13_SCORER_ROOT'])
    result=m.score_one(cell,tmp_path,config)
    assert result['strict']==1 and result['compile'] is True and result['at_token_cap']
