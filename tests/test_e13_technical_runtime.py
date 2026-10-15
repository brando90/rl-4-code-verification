"""Refuse changed technical generation inputs and preserve unsupported probabilities without a retry."""
from pathlib import Path
import importlib.util,json,os,subprocess,sys
import pytest

PHASE=Path(__file__).resolve().parents[1]/'experiments/13_irt_scsc_factor_guided_vs_direct_pass1_rl_sft_qwen3_vbv1_d013/expt_v2/phase2'
sys.path.insert(0,str(PHASE))
spec=importlib.util.spec_from_file_location('e13_technical_runtime',PHASE/'technical_runtime.py')
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)


def fixture(tmp_path):
    root=tmp_path/'generation';root.mkdir()
    cells=[{'cell_id':'authored/0','task_id':'authored','split':'train','seed':1,'prompt_token_ids':[3,4]}]
    row={**cells[0],'condition':'v2-S2','output_token_ids':[5,151645],
         'generation_logprobs':[-1.,None],'finish_reason':'stop'}
    files={'cells.json':cells,'00000.generation.json':row,'result.json':{'condition':'v2-S2',
        'status':'COMPLETE','declared':1,'completed':1,'generated_tokens':2}}
    for name,value in files.items():(root/name).write_text(json.dumps(value))
    config={'generation_root':str(root),'terminal_token_ids':[151643,151645],
            'bindings':[{'path':str(root/n),'sha256':m.digest(root/n)} for n in files]}
    return config,cells


def test_runtime_requires_durable_exact_generation_inputs(tmp_path):
    config,cells=fixture(tmp_path)
    assert m.generation_rows(config,cells)[0]['generation_logprobs'][-1] is None
    path=Path(config['generation_root'])/'00000.generation.json'
    row=json.loads(path.read_text());row['seed']=2;path.write_text(json.dumps(row))
    with pytest.raises(ValueError,match='binding'):m.generation_rows(config,cells)
    next(b for b in config['bindings'] if b['path']==str(path))['sha256']=m.digest(path)
    with pytest.raises(ValueError,match='identity'):m.generation_rows(config,cells)


def test_runtime_refuses_incomplete_denominators_and_duplicate_bindings(tmp_path):
    config,cells=fixture(tmp_path);path=Path(config['generation_root'])/'result.json'
    result=json.loads(path.read_text());result['completed']=0;path.write_text(json.dumps(result))
    next(b for b in config['bindings'] if b['path']==str(path))['sha256']=m.digest(path)
    with pytest.raises(ValueError,match='denominator'):m.generation_rows(config,cells)
    config['bindings']*=2
    with pytest.raises(ValueError,match='duplicate'):m.bound(config,path)


def test_installed_probability_receipts_keep_masks_and_nonfinite_tokens(tmp_path):
    python=Path(os.environ.get('E13_NEMO_PYTHON','/lfs/skampere1/0/brando9/rl4cv_e08/nemo_rl/.venv/bin/python'))
    if not python.exists():
        if os.environ.get('E13_REQUIRE_LEAN_INTEGRATION')=='1':pytest.fail('required installed NeMo unavailable')
        pytest.skip('installed NeMo unavailable')
    config,cells=fixture(tmp_path);config['stage_root']=str(tmp_path/'probabilities')
    plan=tmp_path/'fixture.json';plan.write_text(json.dumps({'config':config,'cells':cells}))
    code=r'''
import json,sys
from pathlib import Path
from contextlib import contextmanager
import torch
sys.path.insert(0,sys.argv[1])
import technical_runtime as runtime,trainer_core
assert not torch.cuda.is_available()
seen=[]
class Policy:
 def prepare_for_lp_inference(self):pass
 def get_logprobs(self,data):
  seen.append(data)
  return {'logprobs':torch.tensor([[0.,0.,-.2,float('nan')]])}
@contextmanager
def session(*a,**k):
 assert k['checkpoint'] is None and not k['init_optimizer']
 yield Policy(),None
trainer_core.policy_session=session
runtime.check_lease=lambda config:None
p=json.loads(Path(sys.argv[2]).read_text());config=p['config'];cells=p['cells']
r=runtime.probabilities(config,cells)
assert r['completed']==1 and not r['admission_statistics_computed'] and r['optimizer_updates']==0
row=json.loads((Path(config['stage_root'])/'00000.probability.json').read_text())
assert row['trainer_input_ids']==[3,4,5,151645] and row['trainer_token_mask']==[0,0,1,1]
assert row['trainer_logprobs'][-1] is None and len(seen)==1
try:runtime.probabilities(config,cells)
except FileExistsError:pass
else:raise AssertionError('completed probability stage repeated')
assert len(seen)==1
'''
    env=dict(os.environ,CUDA_VISIBLE_DEVICES='',OMP_NUM_THREADS='1',MKL_NUM_THREADS='1')
    result=subprocess.run([str(python),'-c',code,str(PHASE),str(plan)],env=env,capture_output=True,text=True,timeout=90)
    assert result.returncode==0,result.stdout+result.stderr
