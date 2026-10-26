"""TLDR: Compute engine context from complete prompt inventories and reject retired lengths."""
import argparse
import json
from pathlib import Path
from common import digest, object_digest, write_new

CAP = 12288
COUNTS = {'train':539,'validation':135,'test':222}


def compute_context(engine_prompts, maximum_position_embeddings):
    if set(engine_prompts) != {'generator','trainer'}:
        raise ValueError('both engine prompt inventories required')
    engines = {}
    for engine, splits in engine_prompts.items():
        if set(splits) != set(COUNTS):raise ValueError('every used split is required')
        maxima = {}
        for split, expected in COUNTS.items():
            prompts=splits[split]
            if len(prompts)!=expected:raise ValueError('incomplete prompt inventory')
            lengths=[len(p) for p in prompts]
            if not all(lengths) or any(type(t) is not int or t<0 for p in prompts for t in p):
                raise ValueError('invalid prompt tokens')
            maxima[split]=max(lengths)
        length=max(maxima.values())+CAP
        if length>maximum_position_embeddings:raise ValueError('context exceeds model maximum positions')
        engines[engine]={'maximum_prompt_tokens':maxima,'context':length,
                         'counts':dict(COUNTS),'prompt_inventory_sha256':object_digest(splits)}
    return {'response_cap':CAP,'maximum_position_embeddings':maximum_position_embeddings,'engines':engines}


def validate_lengths(response_cap, context, receipt, engine):
    if response_cap!=CAP or context in (8192,15945) or context != receipt['engines'][engine]['context']:
        raise ValueError('retired or mismatched length contract')
    if context>receipt['maximum_position_embeddings']:raise ValueError('model position limit exceeded')


def prepare(*, train_prompts, validation_pack, test_pack, tokenizer_path, veribench_root, output):
    """Render prompts locally for length measurement only; return no held-out text or identity."""
    from transformers import AutoTokenizer
    from rl4cv.veribench.exp103 import build_prompt
    tokenizer=AutoTokenizer.from_pretrained(tokenizer_path,local_files_only=True)
    train=json.loads(Path(train_prompts).read_text())
    if len(train)!=539 or any(v['split']!='train' for v in train.values()):
        raise ValueError('invalid inherited train prompts')
    inventories={'train':[v['prompt_token_ids'] for _,v in sorted(train.items())]}
    bindings=[{'path':str(Path(train_prompts).resolve()),'sha256':digest(train_prompts)}]
    # Only instruction.md is read; no held-out reference, output, score or outcome.
    for split,root in [('validation',validation_pack),('test',test_pack)]:
        files=sorted(Path(root).glob('*/instruction.md'))
        if len(files)!=COUNTS[split]:raise ValueError('held-out prompt inventory incomplete')
        tokens=[]; input_hashes=[]
        for path in files:
            prompt=build_prompt(path.read_text(),addendum='vbv1',root=Path(veribench_root))
            text=tokenizer.apply_chat_template(prompt.messages(),tokenize=False,add_generation_prompt=True,enable_thinking=True)
            tokens.append(list(tokenizer.encode(text)))
            input_hashes.append(digest(path))
        inventories[split]=tokens
        bindings.append({'split':split,'instruction_hashes_sha256':object_digest(sorted(input_hashes)),
                         'count':len(files),'pack_root':str(root)})
    model_config=Path(tokenizer_path)/'config.json'
    maximum=json.loads(model_config.read_text())['max_position_embeddings']
    result=compute_context({'generator':inventories,'trainer':inventories},maximum)
    result.update(tldr='All-split prompt lengths computed on CPU without outcomes or model calls.',
                  sources=bindings, model_config_sha256=digest(model_config),
                  tokenizer_files=[{'name':p.name,'sha256':digest(p)} for p in sorted(Path(tokenizer_path).iterdir())
                    if p.is_file() and ('token' in p.name or p.name in ('config.json','chat_template.jinja'))],
                  heldout_content_exposed=False,model_calls=0)
    write_new(output,result)
    return result


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    for name in ('train-prompts','validation-pack','test-pack','tokenizer-path','veribench-root','output'):
        p.add_argument('--'+name,required=True,type=Path)
    args=p.parse_args()
    result=prepare(**vars(args))
    print(json.dumps({'engines':result['engines'],'maximum_position_embeddings':result['maximum_position_embeddings']}))
