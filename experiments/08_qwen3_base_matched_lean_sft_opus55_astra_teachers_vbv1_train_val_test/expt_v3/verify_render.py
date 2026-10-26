"""Check every admitted example against the pinned NeMo formatter and four tokenizers."""
import hashlib
import json
import os
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
WORK = Path('/lfs/skampere1/0/brando9/rl4cv_e08')
sys.path.insert(0, str(HERE.parent / 'expt_v1/scripts'))
from prepare_sft_nemo_e08 import nemo_render, eval_prefix, THINK_PREFIX
from template_check import load_tokenizers


def main():
    toks = load_tokenizers(['1.7B', '4B', '8B', '14B'])
    rows = [json.loads(l) for l in (WORK / 'sft_v3/s_v3_candidates.jsonl').read_text().splitlines()]
    for i, row in enumerate(rows):
        reference = None
        messages = {m['role']: m['content'] for m in row['messages']}
        for size, item in toks.items():
            tok = item['tokenizer']
            nr = nemo_render(tok, row['messages'], True, True, True)
            _, prefix = eval_prefix(tok, messages['system'], messages['user'])
            assert nr['prompt_ids'] == prefix
            assert nr['assistant_chunk'] == THINK_PREFIX + messages['assistant'] + '<|im_end|>\n' + tok.eos_token
            assert len(prefix) == row['n_prompt_tokens']
            assert len(nr['assistant_ids']) == row['n_assistant_tokens'] + 1
            assert len(prefix) + len(nr['assistant_ids']) <= 16384
            ids = prefix + nr['assistant_ids']
            if reference is None:
                reference = ids
            assert ids == reference, (row['example_id'], size)
        if i % 100 == 0:
            print('verified', i + 1, flush=True)
    receipt = {'status': 'PASS', 'examples': len(rows), 'sizes': list(toks),
               'formatter': 'NeMo RL c751f811 get_formatted_message_log',
               'corpus_sha256': hashlib.sha256((WORK / 'sft_v3/s_v3_candidates.jsonl').read_bytes()).hexdigest(),
               'checks': ['four-size token identity', 'prompt prefix', 'loss span', 'manifest loss count plus EOS', 'length cap']}
    (HERE / 'results/render_verification_v3.json').write_text(json.dumps(receipt, indent=2) + '\n')
    print(json.dumps(receipt), flush=True)


if __name__ == '__main__':
    main()
