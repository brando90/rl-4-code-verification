"""Exercise exact evaluation rendering, population isolation and durable neighboring outputs without a device."""
import hashlib
import importlib.machinery
import importlib.util
import json
from pathlib import Path
import sys
from types import SimpleNamespace
import pytest

PHASE=Path(__file__).resolve().parents[1]/'experiments/13_irt_scsc_factor_guided_vs_direct_pass1_rl_sft_qwen3_vbv1_d013/expt_v2/phase2'
sys.path.insert(0,str(PHASE))
spec=importlib.util.spec_from_file_location('e13_evaluation_generation',PHASE/'evaluation_generation.py')
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)


def fixture(tmp_path,monkeypatch,bad_index=None):
    text='authored non-benchmark prompt'
    cells=[{'cell_id':f'cost/{i}/0','task_id':f'authored_{i}','split':'train','sample_idx':0,'seed':9100273,
            'prompt_text':text,'chat_text_sha256':hashlib.sha256(text.encode()).hexdigest(),
            'prompt_token_ids':[12,13],'required_paths':['/authored.lean']} for i in range(8)]
    manifest={'condition':'v2-S2','purpose':'T4_train_cost','cells':cells}
    ids=tmp_path/'train';ids.write_text('\n'.join(c['task_id'] for c in cells))
    config={'allowlist':str(ids),'model':'authored','tokenizer':'authored'};seen=[]
    tokenizer=SimpleNamespace(encode=lambda text:[12,13],decode=lambda *a,**k:pytest.fail('historical rendering must use output.text'))
    monkeypatch.setitem(sys.modules,'transformers',SimpleNamespace(AutoTokenizer=SimpleNamespace(from_pretrained=lambda *a,**k:tokenizer)))
    monkeypatch.setattr(m,'check_lease',lambda _:None)
    monkeypatch.setattr(m,'sampling_parameters',lambda tok,index:seen.append(index) or {'sample':index})
    class Engine:
        def generate(self,texts,params,**kw):
            assert texts==[text]*8
            outputs=[]
            for index in range(8):
                out=SimpleNamespace(text='exact historical text',token_ids=[14,15],finish_reason='stop')
                outputs.append(SimpleNamespace(prompt_token_ids=[12,13],outputs=[] if index==bad_index else [out]))
            return outputs
    monkeypatch.setattr(m,'build_engine',lambda _:Engine())
    return config,manifest,seen


def test_historical_text_and_shared_sample_seed_preserved(tmp_path,monkeypatch):
    config,manifest,seen=fixture(tmp_path,monkeypatch)
    result=m.generate(config,manifest,list(range(8)),root=tmp_path/'out')
    assert result['completed']==8 and result['generated_tokens']==16 and seen==[0]*8
    row=json.loads((tmp_path/'out/00000.generation.json').read_text())
    assert row['completion']=='exact historical text' and row['seed']==91*100003
    with pytest.raises(FileExistsError):m.generate(config,manifest,list(range(8)),root=tmp_path/'out')


def test_invalid_neighbor_retains_all_other_receipts_without_retry(tmp_path,monkeypatch):
    config,manifest,seen=fixture(tmp_path,monkeypatch,bad_index=2)
    with pytest.raises(ValueError,match='invalid receipts'):m.generate(config,manifest,list(range(8)),root=tmp_path/'out')
    assert len(list((tmp_path/'out').glob('*.generation.json')))==7
    assert json.loads((tmp_path/'out/error.json').read_text())['completed']==7
    assert not (tmp_path/'out/result.json').exists()


def test_cost_probe_cannot_include_validation_or_change_seed(tmp_path,monkeypatch):
    config,manifest,seen=fixture(tmp_path,monkeypatch);manifest['cells'][0]['split']='validation'
    with pytest.raises(ValueError,match='train tasks'):m.generate(config,manifest,list(range(8)),root=tmp_path/'out')
    assert not (tmp_path/'out').exists()
    manifest['cells'][0]['split']='train';manifest['cells'][0]['seed']+=1
    with pytest.raises(ValueError,match='seed changed'):m.generate(config,manifest,list(range(8)),root=tmp_path/'out')


def test_full_validation_manifest_is_required_even_for_small_segment(tmp_path,monkeypatch):
    config,manifest,seen=fixture(tmp_path,monkeypatch)
    manifest.update(purpose='validation',arm='A',run_seed=13011,boundary=1)
    with pytest.raises(ValueError,match='complete evaluation task manifest'):m.generate(config,manifest,[0],root=tmp_path/'out')


def test_S2_engine_explicit_resource_contract_preserves_historical_auto_config(tmp_path,monkeypatch):
    seen=[];monkeypatch.setitem(sys.modules,'vllm',SimpleNamespace(LLM=lambda **kw:seen.append(kw)))
    monkeypatch.setattr(m,'numerical_dtype',lambda _: 'float16')
    config={'batch_size':32,'max_model_len':32768,'model':'authored','tokenizer':'authored','gpu_memory_utilization':.85}
    m.build_engine(config)
    assert seen[0]['dtype']=='float16' and seen[0]['generation_config']=='auto' and seen[0]['seed']==91
    assert seen[0]['max_model_len']==32768 and seen[0]['max_num_seqs']==32
