"""A bounded stage keeps cleanup/failure evidence and never implies a scientific gate pass."""
import importlib.util,json,sys,time
from pathlib import Path
from types import SimpleNamespace
import pytest

PHASE=Path(__file__).resolve().parents[1]/'experiments/13_irt_scsc_factor_guided_vs_direct_pass1_rl_sft_qwen3_vbv1_d013/expt_v2/phase2'
sys.path.insert(0,str(PHASE));spec=importlib.util.spec_from_file_location('e13_technical_supervisor',PHASE/'technical_supervisor.py')
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)


def fixture(tmp_path,monkeypatch):
 lease=tmp_path/'lease.json';lease.write_text(json.dumps({'id':'authored-lease','started_unix':time.time(),'expires_unix':time.time()+600}))
 config=tmp_path/'config.json';config.write_text('{}');execution=tmp_path/'execution.json';execution.write_text('{}')
 plan={'supervisor_root':str(tmp_path/'stage'),'config':str(config),'execution':str(execution),'stage':'generate','maximum_seconds':600}
 plan_path=tmp_path/'plan.json';plan_path.write_text(json.dumps(plan))
 monkeypatch.setenv('E13_EXECUTION_ID','authored-lease')
 monkeypatch.setattr(m,'authorize',lambda p:(plan,{'lease_path':str(lease),'lease_id':'authored-lease','python':sys.executable}))
 monkeypatch.setattr(m,'check_lease',lambda c:None)
 calls=[];monkeypatch.setattr(m,'cleanup',lambda marker:(calls.append(marker) or {'verified':True,'signals':[]}))
 return plan_path,plan,calls


def test_zero_exit_is_not_an_admission_statistic_and_duplicate_stage_refused(tmp_path,monkeypatch):
 path,plan,calls=fixture(tmp_path,monkeypatch);launches=[]
 def run(*args,**kw):launches.append(kw);return SimpleNamespace(returncode=0)
 monkeypatch.setattr(m.subprocess,'run',run)
 result=m.run(path)
 assert result['status']=='RUNTIME_EXITED_ZERO' and not result['admission_statistics_computed']
 assert result['cleanup_verified'] and calls==['authored-lease']
 assert 0<launches[0]['timeout']<=510 and launches[0]['start_new_session']
 with pytest.raises(FileExistsError):m.run(path)
 assert len(launches)==1


def test_timeout_retains_failure_and_cleanup_receipts_without_retry(tmp_path,monkeypatch):
 path,plan,calls=fixture(tmp_path,monkeypatch)
 def run(*args,**kw):raise m.subprocess.TimeoutExpired('authored',kw['timeout'])
 monkeypatch.setattr(m.subprocess,'run',run)
 result=m.run(path)
 assert result['status']=='INCOMPLETE_INFRA' and result['error_type']=='TimeoutExpired'
 assert len(calls)==1 and json.loads((Path(plan['supervisor_root'])/'result.json').read_text())==result


def test_unresolved_cleanup_cannot_report_even_runtime_success(tmp_path,monkeypatch):
 path,plan,calls=fixture(tmp_path,monkeypatch)
 monkeypatch.setattr(m.subprocess,'run',lambda *a,**kw:SimpleNamespace(returncode=0))
 monkeypatch.setattr(m,'cleanup',lambda marker:{'verified':False,'signals':[]})
 assert m.run(path)['status']=='CLEANUP_REQUIRED'


def test_unpublished_or_wrong_gate_lock_refused_before_runtime(tmp_path,monkeypatch):
 path=tmp_path/'plan.json';path.write_text(json.dumps({'lock':'authored','repository':'authored','published_revision':'authored'}))
 monkeypatch.setattr(m,'verify_publication',lambda *a:{'condition':'v2-S2','gate':'ANCHOR_GENERATION_S2','status':'FROZEN'})
 with pytest.raises(ValueError,match='pilot lock required'):m.authorize(path)
