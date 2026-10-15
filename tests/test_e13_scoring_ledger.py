"""Verify bounded identical scoring retries and crash recovery without repeating measured cells."""
from pathlib import Path
import sys,json
from contextlib import nullcontext
import pytest

PHASE=Path(__file__).resolve().parents[1]/'experiments/13_irt_scsc_factor_guided_vs_direct_pass1_rl_sft_qwen3_vbv1_d013/expt_v2/phase1'
sys.path.insert(0,str(PHASE))
import score_anchor_ledger as ledger


def fixture(tmp):
    generation=tmp/'generation';generation.mkdir()
    cell={'cell_id':'base/fixture/0','task_id':'fixture','sample':0,'split':'train','seed':11,
          'prompt_token_ids':[1,2],'required_paths':['solution.lean']}
    manifest={'batch':'base','terminal_token_ids':[9],'max_model_len':8194}
    raw={**cell,'output_token_ids':[3,9],'generation_logprobs':[-.3,-.2],'finish_reason':'stop',
         'stop_reason':9,'at_token_cap':False}
    path=generation/'00000.generation.json';path.write_text(json.dumps(raw))
    config={'root':str(tmp/'score'),'generation_root':str(generation)}
    return cell,config,manifest,{str(path):ledger.digest(path)}


def invoke(f,executor):return ledger.score_cell(f[0],0,f[1],f[2],f[3],'locked',nullcontext(),executor)


def test_complete_measurement_survives_resume_without_another_call(tmp_path):
    f=fixture(tmp_path);calls=[]
    def execute(job,root,attempt,slots):
        calls.append(attempt['number'])
        result={**job['identity'],'status':'measured','strict':1,'cleanup_verified':True}
        ledger.write_new(root/'result.json',result);return result
    a=invoke(f,execute);b=invoke(f,lambda *a:pytest.fail('measured cell replayed'))
    assert a==b and a['attempts']==1 and calls==[1]


def test_identical_transient_retry_is_bounded_at_two_and_keeps_same_source(tmp_path):
    f=fixture(tmp_path);calls=[]
    def execute(job,root,attempt,slots):
        calls.append((attempt['number'],attempt['generation_sha256'],job['generation']))
        result={**job['identity'],'status':'unresolved_measurement','error_type':'OSError','cleanup_verified':True}
        ledger.write_new(root/'result.json',result);return result
    result=invoke(f,execute);assert result['status']=='unresolved_measurement' and result['attempts']==2
    assert calls[0][1:]==calls[1][1:] and [r[0] for r in calls]==[1,2]
    invoke(f,lambda *a:pytest.fail('third attempt'))


@pytest.mark.parametrize('status,error',[('deterministic_resource_limit','MemoryError'),
    ('unresolved_measurement','ValueError'),('unresolved_cleanup','OSError')])
def test_deterministic_failure_or_failed_cleanup_never_retried(tmp_path,status,error):
    f=fixture(tmp_path);calls=[]
    def execute(job,root,attempt,slots):
        calls.append(attempt['number'])
        result={**job['identity'],'status':status,'error_type':error,'cleanup_verified':status!='unresolved_cleanup'}
        ledger.write_new(root/'result.json',result);return result
    result=invoke(f,execute);assert result['attempts']==1 and calls==[1]


def test_worker_receipt_recovers_after_controller_loss_without_rescoring(tmp_path,monkeypatch):
    f=fixture(tmp_path);root=Path(f[1]['root'])/'00000/attempt_1';ledger.mkdir(root)
    expected=ledger.identity(f[0],'base')
    ledger.write_new(root/'attempt.json',{'identity':expected,'number':1,'marker':'synthetic-no-process',
        'lock_sha256':'locked','generation_sha256':next(iter(f[3].values()))})
    ledger.write_new(root/'worker_result.json',{**expected,'status':'measured','strict':1})
    # Simulate controller loss between cleanup and final result persistence too.
    ledger.write_new(root/'cleanup.json',{'verified':True,'signals':[]})
    monkeypatch.setattr(ledger,'cleanup',lambda marker:{'verified':True,'signals':[]})
    result=invoke(f,lambda *a:pytest.fail('durable worker measurement replayed'))
    assert result['status']=='measured' and result['attempts']==1
    assert len(list(root.glob('cleanup_recovery_*.json')))==1


def test_missing_worker_receipt_has_only_one_remaining_attempt(tmp_path,monkeypatch):
    f=fixture(tmp_path);root=Path(f[1]['root'])/'00000/attempt_1';ledger.mkdir(root)
    expected=ledger.identity(f[0],'base')
    ledger.write_new(root/'attempt.json',{'identity':expected,'number':1,'marker':'synthetic-no-process',
        'lock_sha256':'locked','generation_sha256':next(iter(f[3].values()))})
    monkeypatch.setattr(ledger,'cleanup',lambda marker:{'verified':True,'signals':[]})
    calls=[]
    def execute(job,root,attempt,slots):
        calls.append(attempt['number'])
        result={**job['identity'],'status':'measured','strict':0,'cleanup_verified':True}
        ledger.write_new(root/'result.json',result);return result
    result=invoke(f,execute);assert result['status']=='measured' and result['attempts']==2 and calls==[2]


def test_changed_source_or_forged_identity_is_an_integrity_error(tmp_path):
    f=fixture(tmp_path);path=Path(next(iter(f[3])));path.write_text('{}')
    with pytest.raises(ValueError,match='changed generation'):invoke(f,lambda *a:pytest.fail('changed source scored'))
    with pytest.raises(ValueError,match='identity'):
        ledger.check_identity({'cell_id':'forged','status':'measured','strict':1},ledger.identity(f[0],'base'))
