"""Verify retained evaluation source, numerical, population and checkpoint identity before model construction."""
from pathlib import Path
import hashlib,importlib.util,json,sys
import pytest
PHASE=Path(__file__).resolve().parents[1]/'experiments/13_irt_scsc_factor_guided_vs_direct_pass1_rl_sft_qwen3_vbv1_d013/expt_v2/phase2'
sys.path.insert(0,str(PHASE));spec=importlib.util.spec_from_file_location('e13_evaluation_runtime',PHASE/'evaluation_runtime.py')
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
from evaluation_contract import identities


def fixture(tmp_path,monkeypatch):
    def put(name,value):
        p=tmp_path/name;p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(value));return str(p)
    ids=[f'authored_{i:03d}' for i in range(135)];allow=tmp_path/'ids.txt';allow.write_text('\n'.join(ids)+'\n')
    cells=identities(ids,'validation',arm='A',run_seed=13011,boundary=1)
    for cell in cells:cell.update(prompt_text='authored',chat_text_sha256=hashlib.sha256(b'authored').hexdigest(),prompt_token_ids=[1,2],required_paths=['solution.lean'])
    manifest=put('manifest.json',{'condition':'v2-S2','purpose':'validation','arm':'A','run_seed':13011,'boundary':1,'cells':cells})
    policy=put('policy.json',{'precision':'float16','generation':{'vllm_cfg':{'precision':'float16'}}})
    put('model/weights.safetensors',{'authored':True});put('tokenizer/tokenizer.json',{'authored':True})
    paths=list(tmp_path.rglob('*'))+[PHASE/name for name in ('evaluation_runtime.py','evaluation_generation.py','evaluation_contract.py','technical_runtime.py','training_checkpoint.py')]+[PHASE.parent/'phase1'/name for name in ('runtime.py','device_binding.py')]
    config={'condition':'v2-S2','stage':'evaluation_generate','purpose':'validation','arm':'A','run_seed':13011,'boundary':1,
        'manifest':manifest,'allowlist':str(allow),'policy_config':policy,'numerical_dtype':'float16','batch_size':32,
        'max_model_len':32768,'runtime_versions':{},'model':str(tmp_path/'model'),'tokenizer':str(tmp_path/'tokenizer'),
        'indexes':[0,1],'bindings':[{'path':str(p),'sha256':m.bound.__globals__['digest'](p)} for p in paths if p.is_file()]}
    monkeypatch.setattr(m,'check_lease',lambda _:None)
    return config


def test_complete_population_and_checkpoint_identity_precede_generation(tmp_path,monkeypatch):
    config=fixture(tmp_path,monkeypatch);assert len(m.verify(config,'evaluation_generate')['cells'])==1080
    config['boundary']=2
    with pytest.raises(ValueError,match='another selected checkpoint'):m.verify(config,'evaluation_generate')


def test_changed_weights_cannot_pass_runtime_admission(tmp_path,monkeypatch):
    config=fixture(tmp_path,monkeypatch);(tmp_path/'model/weights.safetensors').write_bytes(b'changed')
    with pytest.raises(ValueError,match='changed runtime binding'):m.verify(config,'evaluation_generate')


def test_duplicate_segment_and_changed_engine_context_are_refused(tmp_path,monkeypatch):
    config=fixture(tmp_path,monkeypatch);config['indexes']=[0,0]
    with pytest.raises(ValueError,match='invalid retained'):m.verify(config,'evaluation_generate')
    config['indexes']=[0];config['max_model_len']=15945
    with pytest.raises(ValueError,match='engine contract'):m.verify(config,'evaluation_generate')


def test_health_preflight_restores_shared_engine_builder_on_failure(monkeypatch):
    import runtime,evaluation_generation
    original=runtime.build_engine
    monkeypatch.setattr(m,'verify',lambda *_:{})
    def fail(_):
        assert runtime.build_engine is not original
        raise RuntimeError('authored engine failure')
    monkeypatch.setattr(runtime,'preflight',fail)
    with pytest.raises(RuntimeError,match='authored engine failure'):m.run({},'evaluation_preflight')
    assert runtime.build_engine is original
