"""TLDR: Execute pinned NeMo rollout/flatten code with actual Qwen tokens and deterministic transport doubles."""
import sys
from pathlib import Path
from types import SimpleNamespace

import pytest

torch = pytest.importorskip('torch')
pytest.importorskip('nemo_rl')
E = Path(__file__).resolve().parents[1] / 'experiments/09_qwen3_1p7b_grpo_scsc_scalar_vs_factor_feedback_vbv1_d013/expt_v1'
sys.path.insert(0, str(E))
from two_turn_env import TwoTurnLeanEnvironment, MeasuredAnswer, qwen_continuation, RequiredFSCMissing
from rl4cv.rewards import ScoredResponse
from nemo_rl.experience import rollouts
from nemo_rl.distributed.batched_data_dict import BatchedDataDict
from nemo_rl.data.llm_message_utils import batched_message_log_to_flat_message


@pytest.fixture(scope='module')
def tokenizer():
    from transformers import AutoTokenizer
    model = Path('/lfs/skampere1/0/brando9/rl4cv_e08/ckpt/1.7B/hf/step_658')
    if not model.exists():
        pytest.skip('native checkpoint tokenizer absent')
    return AutoTokenizer.from_pretrained(model, local_files_only=True)


class Generator:
    def __init__(self, tokenizer, closed):
        self.tokenizer, self.closed, self.seeds = tokenizer, closed, []

    def generate(self, data, greedy=False):
        self.seeds.extend(data['e09_seeds'])
        answer = ('first' if len(self.seeds) == 1 else 'final')
        ids = self.tokenizer.encode(answer + ('<|im_end|>' if self.closed else ''), add_special_tokens=False)
        prompt = data['input_ids'][0, :int(data['input_lengths'][0])]
        output = torch.cat((prompt, torch.tensor(ids))).unsqueeze(0)
        return {'output_ids': output, 'generation_lengths': torch.tensor([len(ids)]),
                'unpadded_sequence_lengths': torch.tensor([output.shape[1]]),
                'logprobs': torch.zeros_like(output, dtype=torch.float32)}


def execute(monkeypatch, tokenizer, closed, root, *, missing=False, max_seq_len=24576):
    monkeypatch.setenv('E09_FILTERED_POLICY', '1')
    seen = []
    def score(meta, candidate):
        seen.append(candidate)
        return MeasuredAnswer(ScoredResponse(True, True, 1, 1, 1, None if missing else .5), 'ok', 'fixture')
    subject = TwoTurnLeanEnvironment('C', score, tokenizer=tokenizer, receipt_dir=root)
    pending = {}
    def remote(*args):
        key = object()
        pending[key] = subject.step(*args)
        return key
    actor = SimpleNamespace(step=SimpleNamespace(remote=remote))
    monkeypatch.setattr(rollouts.ray, 'get', lambda keys: [pending[k] for k in keys])
    prompt = tokenizer.apply_chat_template([{'role': 'user', 'content': 'Lean code please.'}],
                tokenize=False, add_generation_prompt=True, enable_thinking=False)
    tokens = torch.tensor(tokenizer.encode(prompt, add_special_tokens=False))
    batch = BatchedDataDict({'message_log': [[{'role': 'user', 'content': prompt, 'token_ids': tokens}]],
            'length': torch.tensor([len(tokens)]), 'extra_env_info': [{'seed': 20261008, 'schedule_index': 0, 'task_id': 'fixture'}],
            'task_name': ['fixture'], 'loss_multiplier': torch.ones(1), 'idx': torch.tensor([0])})
    generator = Generator(tokenizer, closed)
    output, metrics = rollouts.run_multi_turn_rollout(generator, batch, tokenizer,
                                                    {'fixture': actor}, max_seq_len, 2)
    return output, metrics, seen, generator


@pytest.mark.parametrize('closed', [True, False])
def test_real_rollout_preserves_boundaries_terminal_metadata_and_final_file(monkeypatch, tokenizer, tmp_path, closed):
    output, metrics, seen, generator = execute(monkeypatch, tokenizer, closed, tmp_path)
    assert seen == ['first', 'final']
    assert output['extra_env_info'][0]['turn'] == 2
    assert output['extra_env_info'][0]['final_response'] == 'final'
    assert output['total_reward'].item() == pytest.approx(.5**(1/3))
    assert metrics['total_turns'] == 2 and len(set(generator.seeds)) == 2
    messages = output['message_log'][0]
    assert [m['role'] for m in messages] == ['user', 'assistant', 'user', 'assistant', 'user']
    assert messages[2]['content'].startswith('\n<|im_start|>user\n' if closed else '<|im_end|>\n<|im_start|>user\n')
    assert messages[2]['content'].endswith('<|im_start|>assistant\n<think>\n\n</think>\n\n')
    assert torch.equal(messages[2]['token_ids'], torch.tensor(tokenizer.encode(messages[2]['content'], add_special_tokens=False)))
    for m in messages:
        m['token_loss_mask'] = torch.full_like(m['token_ids'], int(m['role'] == 'assistant'))
    flat, lengths = batched_message_log_to_flat_message([messages], pad_value_dict={'token_ids': tokenizer.pad_token_id})
    assert int(flat['token_loss_mask'].sum()) == sum(len(m['token_ids']) for m in messages if m['role'] == 'assistant')
    assert len(list(tmp_path.glob('*.json'))) == 2


def test_actual_rollout_missing_rating_blocks(monkeypatch, tokenizer, tmp_path):
    with pytest.raises(RequiredFSCMissing):
        execute(monkeypatch, tokenizer, True, tmp_path, missing=True)


def test_actual_rollout_context_truncation_blocks(monkeypatch, tokenizer, tmp_path):
    with pytest.raises(RuntimeError, match='incomplete two-turn'):
        execute(monkeypatch, tokenizer, True, tmp_path, max_seq_len=48)
