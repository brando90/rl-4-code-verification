"""Keep declared slot receipts, unsupported probabilities and terminal-token failures explicit."""
from pathlib import Path
from types import SimpleNamespace
import importlib.util,json,sys
import pytest

PHASE=Path(__file__).resolve().parents[1]/'experiments/13_irt_scsc_factor_guided_vs_direct_pass1_rl_sft_qwen3_vbv1_d013/expt_v2/phase2'
sys.path.insert(0,str(PHASE))
spec=importlib.util.spec_from_file_location('e13_phase2_generation',PHASE/'generation_core.py');module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)


def setup(tmp_path,monkeypatch,*,bad_terminal=False):
    allow=tmp_path/'train.txt';allow.write_text('authored_task\n')
    cells=[{'cell_id':f'fixture/{i}','task_id':'authored_task','split':'train','sample':i,
            'seed':100+i,'prompt_token_ids':[3,4]} for i in range(3)]
    config={'train_ids':str(allow),'batch_size':32,'terminal_token_ids':[1],
            'model':'fixture_model','tokenizer':'fixture_tokenizer'}
    requests_seen=[]
    class Engine:
        def generate(self,prompts,sampling,use_tqdm):
            requests_seen.extend(zip(prompts,sampling));out=[]
            for i,p in enumerate(prompts):
                tokens=[5,2 if bad_terminal and i==1 else 1]
                probabilities=[{5:SimpleNamespace(logprob=-.2)},{} if i==1 else {1:SimpleNamespace(logprob=-.1)}]
                out.append(SimpleNamespace(prompt_token_ids=p['prompt_token_ids'],outputs=[SimpleNamespace(
                    token_ids=tokens,logprobs=probabilities,finish_reason='stop')]))
            return out
    monkeypatch.setattr(module,'check_lease',lambda config:None)
    monkeypatch.setattr(module,'numerical_dtype',lambda config:'float16')
    monkeypatch.setattr(module,'build_engine',lambda config,contract:Engine())
    monkeypatch.setitem(sys.modules,'vllm',SimpleNamespace(SamplingParams=lambda **kwargs:kwargs))
    tokenizer=SimpleNamespace(decode=lambda tokens,skip_special_tokens:'authored fixture')
    monkeypatch.setitem(sys.modules,'transformers',SimpleNamespace(AutoTokenizer=SimpleNamespace(from_pretrained=lambda *a,**k:tokenizer)))
    return config,cells,requests_seen


def test_unsupported_selected_token_is_retained_for_gate_and_no_rerun(tmp_path,monkeypatch):
    config,cells,seen=setup(tmp_path,monkeypatch);root=tmp_path/'outputs'
    result=module.generate(config,cells,root=root)
    assert result['completed']==3 and result['unsupported_selected_tokens']==1
    missing=json.loads((root/'00001.generation.json').read_text())
    assert missing['generation_logprobs']==[-.2,None]
    assert [s['seed'] for p,s in seen]==[100,101,102]
    assert all(s['max_tokens']==8192 and s['temperature']==1. and s['top_p']==1. and s['top_k']==-1 for p,s in seen)
    with pytest.raises(FileExistsError):module.generate(config,cells,root=root)
    assert len(seen)==3


def test_invalid_response_preserves_other_slots_and_never_refills(tmp_path,monkeypatch):
    config,cells,seen=setup(tmp_path,monkeypatch,bad_terminal=True);root=tmp_path/'outputs'
    with pytest.raises(ValueError,match='invalid generation'):module.generate(config,cells,root=root)
    assert (root/'00000.generation.json').exists() and (root/'00002.generation.json').exists()
    assert not (root/'00001.generation.json').exists() and (root/'00001.error.json').exists()
    error=json.loads((root/'error.json').read_text())
    assert error['completed']==2 and error['declared']==3 and not error['rerun_admitted']
    assert len(seen)==3


def test_heldout_manifest_refused_before_attempt_or_engine(tmp_path,monkeypatch):
    config,cells,seen=setup(tmp_path,monkeypatch);cells[0]['split']='test'
    with pytest.raises(ValueError,match='held-out'):module.generate(config,cells,root=tmp_path/'outputs')
    assert not (tmp_path/'outputs').exists() and not seen


def test_context_headroom_and_unique_ids_are_required(tmp_path,monkeypatch):
    config,cells,seen=setup(tmp_path,monkeypatch)
    cells[0]['prompt_token_ids']=[3]*7754
    with pytest.raises(ValueError,match='context'):module.validate_cells(cells,['authored_task'])
    cells[0]['prompt_token_ids']=[3];cells[1]['cell_id']=cells[0]['cell_id']
    with pytest.raises(ValueError,match='unique'):module.validate_cells(cells,['authored_task'])
