"""Check exact pinned 1.7B and 8B token identities and warm-start loss-span formatting."""
import json
import sys
from pathlib import Path
from transformers import AutoTokenizer

ROOT=Path(__file__).parent
sys.path.insert(0,str(ROOT))
from check_example import get_tokenizer
sys.path.insert(0,'/lfs/skampere1/0/brando9/rl4cv_e08/rl-4-code-verification/experiments/08_qwen3_base_matched_lean_sft_opus55_astra_teachers_vbv1_train_val_test/expt_v1/scripts')
from template_check import render

small=AutoTokenizer.from_pretrained('Qwen/Qwen3-1.7B-Base',revision='ea980cb0a6c2ae4b936e82123acc929f1cec04c1',cache_dir=str(ROOT/'runtime/huggingface'))
big=get_tokenizer();rows=[]
paths=list((ROOT/'prototype_checks').glob('*/training.json'))
paths+=list((ROOT/'workers').glob('*/examples/*/training.json'))
for path in paths:
    d=json.loads(path.read_text());m={x['role']:x['content'] for x in d['messages']}
    a=render(small,m['system'],m['user'],m['assistant']);b=render(big,m['system'],m['user'],m['assistant'])
    keys=['prefix_ids_sha256','full_ids_sha256','assistant_ids_sha256','n_assistant_tokens']
    rows.append({'task_id':d['task_id'],'path':str(path),'exact_ids_match':all(a[k]==b[k] for k in keys),'format_pass':all(a[k] for k in ['byte_prefix_ok','token_prefix_ok','span_matches_expected','within_cap']),'assistant_tokens':a['n_assistant_tokens']})
out={'tokenizer':'Qwen/Qwen3-1.7B-Base','revision':'ea980cb0a6c2ae4b936e82123acc929f1cec04c1','rows':rows,'passed':len(rows)>=4 and all(x['exact_ids_match'] and x['format_pass'] for x in rows)}
(ROOT/'runtime/format_1p7_verification.json').write_text(json.dumps(out,indent=2))
print(json.dumps({'passed':out['passed'],'examples':len(rows),'assistant_tokens':[x['assistant_tokens'] for x in rows]}))
