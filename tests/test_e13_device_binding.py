"""Reproduce vLLM's UUID parsing defect and test the numeric mapping on every launch purpose."""
import ast
import json
import os
from pathlib import Path
import socket
import sys
import time
from types import SimpleNamespace

import pytest

ROOT = Path(__file__).resolve().parents[1] / 'experiments/13_irt_scsc_factor_guided_vs_direct_pass1_rl_sft_qwen3_vbv1_d013/expt_v2/phase1'
sys.path.insert(0,str(ROOT))
import device_binding as binding
import lp1


def lease():
    return {'status':'ACTIVE','owner':'e13v2','host':socket.gethostname().split('.')[0],
            'expires_unix':time.time()+100,'uuid':'GPU-synthetic','index':2,'id':'fixture'}


@pytest.mark.parametrize('purpose',binding.PURPOSES)
def test_vllm_uuid_regression_and_all_launch_purposes(monkeypatch,purpose):
    # Execute the exact installed pinned method, isolated from importing CUDA.
    source=Path('/lfs/skampere1/0/brando9/rl4cv_e08/nemo_rl/.venv/lib/python3.12/site-packages/vllm/platforms/interface.py')
    if source.exists():
        tree=ast.parse(source.read_text())
        cls=next(n for n in tree.body if isinstance(n,ast.ClassDef) and n.name=='Platform')
        method=next(n for n in cls.body if isinstance(n,ast.FunctionDef) and n.name=='device_id_to_physical_device_id')
        module=ast.Module(body=[ast.ClassDef(name='PinnedPlatform',bases=[],keywords=[],
            body=[ast.Assign(targets=[ast.Name(id='device_control_env_var',ctx=ast.Store())],
                             value=ast.Constant(value='CUDA_VISIBLE_DEVICES')),method],decorator_list=[])],type_ignores=[])
        ns={'os':os};exec(compile(ast.fix_missing_locations(module),str(source),'exec'),ns)
        physical=ns['PinnedPlatform'].device_id_to_physical_device_id
    else:
        # Same pinned method's conversion on non-cluster test hosts.
        physical=lambda logical:int(os.environ['CUDA_VISIBLE_DEVICES'].split(',')[logical])
    monkeypatch.setenv('CUDA_VISIBLE_DEVICES','GPU-synthetic')
    with pytest.raises(ValueError,match='invalid literal'):physical(0)
    environment=binding.launch_environment(lease(),purpose,{},'GPU-other, 0\nGPU-synthetic, 2\n')
    monkeypatch.setenv('CUDA_VISIBLE_DEVICES',environment['CUDA_VISIBLE_DEVICES'])
    assert physical(0)==2 and environment['E13_EXECUTION_ID']=='fixture'
    assert environment['CUDA_DEVICE_ORDER']=='PCI_BUS_ID'


@pytest.mark.parametrize('query',['GPU-other, 2\n','GPU-synthetic, 1\n',
                                  'GPU-synthetic, 2\nGPU-synthetic, 2\n','GPU-synthetic, bad\n'])
def test_mapping_drift_or_ambiguity_refuses_launch(query):
    with pytest.raises(RuntimeError):binding.numeric_index(lease(),query)


def test_runtime_refuses_uuid_even_when_lease_is_valid(monkeypatch):
    monkeypatch.setattr(binding,'numeric_index',lambda _: '2')
    monkeypatch.setenv('CUDA_VISIBLE_DEVICES','GPU-synthetic');monkeypatch.setenv('E13_EXECUTION_ID','fixture')
    with pytest.raises(RuntimeError,match='numeric index'):binding.check_visible_device(lease())


def test_preflight_failure_is_durable_but_does_not_count_probe(tmp_path,monkeypatch):
    l=tmp_path/'lease.json';l.write_text(json.dumps(lease()))
    config={'lease_path':str(l),'attempt_root':str(tmp_path/'run'),'maximum_seconds':100,
            'python':'synthetic','attempt_number':2}
    path=tmp_path/'config.json';path.write_text(json.dumps(config))
    monkeypatch.setenv('E13_EXECUTION_ID','fixture')
    monkeypatch.setattr(lp1,'check_bindings',lambda _:None);monkeypatch.setattr(lp1,'check_lease',lambda _:None)
    stages=[]
    def failed(argv,**kwargs):
        stages.append(argv[-1]);return SimpleNamespace(returncode=1)
    monkeypatch.setattr(lp1.subprocess,'run',failed)
    monkeypatch.setattr(lp1,'cleanup',lambda _: {'verified':True,'signals':[]})
    with pytest.raises(RuntimeError,match='preflight failed'):lp1.run(path)
    assert stages==['preflight'] and not (tmp_path/'run/attempt.json').exists()
    result=json.loads((tmp_path/'run/result.json').read_text())
    assert not result['attempt_counted'] and not result['admission_statistics_computed']
    assert result['cleanup_verified']
    with pytest.raises(FileExistsError):lp1.run(path)


def test_a4_statistic_finality_and_three_attempt_bound():
    from a4_admission import admit_attempt
    empty={'status':'INCOMPLETE','admission_statistics_computed':False}
    admit_attempt(2,[empty]); admit_attempt(3,[empty,empty])
    for number,prior in [(4,[empty]*3),(2,[]),(2,[{**empty,'unsupported_tokens':0}]),
                         (2,[{**empty,'admission_statistics_computed':True}]),(2,[{'status':'FAIL'}])]:
        with pytest.raises(ValueError):admit_attempt(number,prior)


def test_a4_preserves_science_and_all_previous_noncode_hashes():
    from copy import deepcopy
    from a4_admission import unchanged_science
    runtime={'attempt_root':'old','generation_root':'old/generation','ray_temp':'old/ray',
             'model':'fixed-model','manifest':'fixed-probe','batch_size':32,'runtime_versions':{'vllm':'0.10.0'},
             'bindings':[{'path':'/code/runtime.py','sha256':'old-code'},
                         {'path':'/science/probe.json','sha256':'fixed-probe'}]}
    old={'maximum_seconds':1800,'cumulative_limit_hours':.6,
         'routes':[{'lp1_script':'/code/lp1.py','config_path':'old-config','lease_path':'old-lease','runtime':runtime}]}
    new=deepcopy(old);r=new['routes'][0]['runtime'];r.update(attempt_number=2,attempt_root='new',generation_root='new/gen',ray_temp='new/ray')
    r['bindings'][0]['sha256']='new-code';r['bindings'].append({'path':'/code/device_binding.py','sha256':'mapper'})
    unchanged_science(old,new)
    for field,value in [('model','different'),('manifest','different'),('batch_size',8)]:
        bad=deepcopy(new);bad['routes'][0]['runtime'][field]=value
        with pytest.raises(ValueError):unchanged_science(old,bad)
    bad=deepcopy(new);bad['routes'][0]['runtime']['bindings'][1]['sha256']='changed'
    with pytest.raises(ValueError,match='scientific binding'):unchanged_science(old,bad)
    bad=deepcopy(new);bad['cumulative_limit_hours']=1
    with pytest.raises(ValueError,match='resource cap'):unchanged_science(old,bad)
