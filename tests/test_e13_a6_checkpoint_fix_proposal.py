"""Reproduce the zero-response A6 checkpoint-format defect and test its admitted one-line repair."""
from pathlib import Path
import difflib,json,sys,types
import pytest
P=Path(__file__).resolve().parents[1]/'experiments/13_irt_scsc_factor_guided_vs_direct_pass1_rl_sft_qwen3_vbv1_d013/expt_v2/phase2'
sys.path.insert(0,str(P))
import a6_runtime as original
from test_e13_a6_diagnostic import manifest


def historical():
    new=(P/'a6_runtime.py').read_text()
    old=new.replace("any(p.suffix in ('.bin','.safetensors')for p in files)","any(p.suffix=='.safetensors'for p in files)")
    assert new!=old
    relative=str((P/'a6_runtime.py').relative_to(P.parents[3]))
    patch=''.join(difflib.unified_diff(old.splitlines(keepends=True),new.splitlines(keepends=True),fromfile='a/'+relative,tofile='b/'+relative))
    assert patch==(P/'A6_checkpoint_format_fix.patch').read_text()
    module=types.ModuleType('authored_a6_original');module.__file__=str(P/'a6_runtime.py');exec(compile(old,module.__file__,'exec'),module.__dict__)
    module.check_lease=lambda config:None
    return module


def configuration(tmp_path,suffix):
    model=tmp_path/'model';model.mkdir()
    if suffix:(model/('authored_weights'+suffix)).write_bytes(b'authored fixture, not real weights')
    m,ids=manifest();manifest_path=tmp_path/'manifest.json';manifest_path.write_text(json.dumps(m));allow=tmp_path/'train_ids';allow.write_text('\n'.join(ids))
    policy=tmp_path/'policy.json';policy.write_text(json.dumps({'precision':'float16','generation':{'vllm_cfg':{'precision':'float16'}}}))
    lease=tmp_path/'lease.json';lease.write_text(json.dumps({'phase':'v2-S2-A6-diagnostic','id':'authored'}))
    files=[P/'a6_runtime.py',P/'a6_generation.py',P/'a6_contract.py',P/'evaluation_contract.py',P.parent/'phase1/runtime.py',P.parent/'phase1/device_binding.py',manifest_path,allow,policy,*model.iterdir()]
    return {'manifest':str(manifest_path),'allowlist':str(allow),'policy_config':str(policy),'model':str(model),'tokenizer':str(model),
        'runtime_versions':{},'numerical_dtype':'float16','max_model_len':32768,'batch_size':32,'lease_path':str(lease),'lease_id':'authored',
        'bindings':[{'path':str(p),'sha256':original.digest(p)}for p in files]}


def test_pytorch_binary_reproduces_original_failure_and_passes_proposed_preflight(tmp_path,monkeypatch):
    config=configuration(tmp_path,'.bin');monkeypatch.setattr(original,'check_lease',lambda config:None)
    with pytest.raises(ValueError,match='frozen weights absent'):historical().verify(config)
    assert len(original.verify(config)['cells'])==512


def test_safetensors_still_passes_and_missing_weights_still_fail(tmp_path,monkeypatch):
    first=tmp_path/'present';first.mkdir();config=configuration(first,'.safetensors');monkeypatch.setattr(original,'check_lease',lambda config:None)
    assert historical().verify(config)==original.verify(config)
    absent=tmp_path/'absent';absent.mkdir();config=configuration(absent,None)
    with pytest.raises(ValueError,match='frozen weights absent'):original.verify(config)


def test_changed_weights_still_rejected(tmp_path):
    config=configuration(tmp_path,'.bin');(Path(config['model'])/'authored_weights.bin').write_bytes(b'changed bytes')
    with pytest.raises(ValueError,match='changed diagnostic runtime binding'):original.verify(config)
