"""Run one isolated S2 technical stage with bound inputs; admission statistics remain in the driver."""
from __future__ import annotations

import argparse
import importlib.metadata
import json
import math
from pathlib import Path
import sys

HERE=Path(__file__).resolve().parent
PHASE1=HERE.parent/'phase1'
if str(PHASE1) not in sys.path:sys.path.insert(0,str(PHASE1))
from training_checkpoint import digest,write_new
from runtime import check_lease,numerical_dtype
from generation_core import validate_cells

STAGES=('preflight','generate','probabilities','update','replay','export','evaluation_preflight','evaluation_generate')


def bound(config,path):
    path=Path(path).resolve()
    found=[b for b in config['bindings'] if Path(b['path']).resolve()==path]
    if len(found)!=1 or digest(path)!=found[0]['sha256']:
        raise ValueError('missing, duplicate or changed runtime binding: '+str(path))
    return path


def verify(config,stage):
    if stage not in STAGES or config.get('condition')!='v2-S2':raise ValueError('unregistered S2 stage')
    if config.get('stage')!=stage:raise ValueError('stage differs from the bound execution request')
    paths=[str(Path(b['path']).resolve()) for b in config['bindings']]
    if not paths or len(paths)!=len(set(paths)):raise ValueError('duplicate or empty runtime binding list')
    for b in config['bindings']:bound(config,b['path'])
    # Every authored runtime dependency must be explicit, including the unchanged
    # admitted device binding, probability and common-tokenizer engine paths.
    for name in ('technical_runtime.py','generation_core.py','trainer_core.py','training_checkpoint.py',
                 'training_data.py','worker_state.py','ray_paths.py'):
        bound(config,HERE/name)
    for name in ('runtime.py','device_binding.py','anchor_runtime.py','panel.py','probability.py'):
        bound(config,PHASE1/name)
    for name in ('policy_config','train_ids'):bound(config,config[name])
    for package,version in config['runtime_versions'].items():
        if importlib.metadata.version(package)!=version:raise ValueError('installed version changed: '+package)
    if numerical_dtype(config)!='float16' or config['batch_size']!=32:
        raise ValueError('S2 precision or generator batch setting changed')
    if config['terminal_token_ids']!=[151643,151645]:raise ValueError('frozen terminal token IDs changed')
    if type(config.get('run_seed')) is not int or not 0<=config['run_seed']<2**63:
        raise ValueError('fixed technical run seed missing')
    # An execution request is produced only by the prospective LP driver; this
    # primitive does not acquire a device or create an experiment admission.
    if stage in ('preflight','generate','probabilities'):
        bound(config,config['cells_path'])
        cells=json.loads(Path(config['cells_path']).read_text())
        validate_cells(cells,Path(config['train_ids']).read_text().splitlines())
    if stage=='preflight':
        manifest=json.loads(bound(config,config['manifest']).read_text())
        if manifest['max_model_len']!=15945 or manifest['terminal_token_ids']!=config['terminal_token_ids']:
            raise ValueError('health preflight context or terminal mask changed')
    if stage in ('evaluation_preflight','evaluation_generate'):
        from evaluation_generation import validate_manifest
        for name in ('evaluation_generation.py','evaluation_contract.py'):bound(config,HERE/name)
        manifest=json.loads(bound(config,config['manifest']).read_text())
        if manifest.get('purpose')!='T4_train_cost' or config['allowlist']!=config['train_ids']:
            raise ValueError('technical evaluation must remain a frozen train-only cost probe')
        if config['max_model_len']!=32768:raise ValueError('evaluation context changed')
        validate_manifest(manifest,Path(config['train_ids']).read_text().splitlines())
    if stage=='update':bound(config,config['groups_path'])
    if stage=='replay':bound(config,Path(config['source_update'])/'result.json')
    if config.get('checkpoint'):
        bound(config,Path(config['checkpoint'])/'receipt.json')
    for key in ('model','initial_model','tokenizer'):
        directory=Path(config[key])
        files=[p for p in directory.iterdir() if p.is_file()]
        if not files:raise ValueError('empty frozen model/tokenizer directory')
        if key!='tokenizer' and not any(p.suffix in ('.bin','.safetensors') for p in files):
            raise ValueError('frozen weights missing')
        for p in files:
            if p.name!='export_receipt.json':bound(config,p)
    check_lease(config)


def generation_rows(config,cells):
    """Reject incomplete or changed generation before any trainer operation."""
    root=Path(config['generation_root'])
    terminal=json.loads(bound(config,root/'result.json').read_text())
    declared=json.loads(bound(config,root/'cells.json').read_text())
    if declared!=cells or terminal.get('status')!='COMPLETE' or terminal.get('condition')!='v2-S2':
        raise ValueError('incomplete generation or changed declared cells')
    if terminal.get('declared')!=len(cells) or terminal.get('completed')!=len(cells):
        raise ValueError('generation denominator changed')
    from panel import validate_generation
    rows=[]
    for index,cell in enumerate(cells):
        row=json.loads(bound(config,root/f'{index:05d}.generation.json').read_text())
        if any(row.get(k)!=cell[k] for k in ('cell_id','task_id','split','seed')):
            raise ValueError('generation identity changed')
        validate_generation(cell,row,{'max_model_len':15945,'terminal_token_ids':config['terminal_token_ids']})
        rows.append(row)
    if terminal['generated_tokens']!=sum(len(r['output_token_ids']) for r in rows):
        raise ValueError('generation token accounting changed')
    return rows


def probabilities(config,cells):
    """Keep full token alignment and unsupported values as receipts, without gate comparison."""
    import torch
    from nemo_rl.distributed.batched_data_dict import BatchedDataDict
    from trainer_core import policy_session
    rows=generation_rows(config,cells)
    root=Path(config['stage_root']);root.mkdir(parents=True,exist_ok=False)
    write_new(root/'attempt.json',{'condition':'v2-S2','stage':'probabilities','declared':len(cells),
                                  'admission_statistics_computed':False})
    try:
        checkpoint=config.get('checkpoint')
        with policy_session(config,checkpoint=checkpoint,init_optimizer=bool(checkpoint)) as (policy,_):
            policy.prepare_for_lp_inference()
            for index,row in enumerate(rows):
                check_lease(config)
                tokens=row['prompt_token_ids']+row['output_token_ids']
                mask=[0]*len(row['prompt_token_ids'])+[1]*len(row['output_token_ids'])
                data=BatchedDataDict({'input_ids':torch.tensor([tokens],dtype=torch.long),
                    'input_lengths':torch.tensor([len(tokens)],dtype=torch.long),
                    'token_mask':torch.tensor([mask],dtype=torch.float32),
                    'sample_mask':torch.ones(1,dtype=torch.float32)})
                values=policy.get_logprobs(data)['logprobs'][0,:len(tokens)].detach().cpu().tolist()
                if len(values)!=len(tokens):raise ValueError('trainer probability alignment changed')
                write_new(root/f'{index:05d}.probability.json',{**row,'trainer_input_ids':tokens,
                    'trainer_token_mask':mask,'trainer_logprobs':[v if math.isfinite(v) else None for v in values]})
        result={'condition':'v2-S2','status':'COMPLETE','declared':len(cells),'completed':len(cells),
                'optimizer_updates':0,'admission_statistics_computed':False}
        write_new(root/'result.json',result);return result
    except Exception as exc:
        write_new(root/'error.json',{'condition':'v2-S2','status':'INCOMPLETE','error_type':type(exc).__name__,
            'error':str(exc),'admission_statistics_computed':False,'rerun_admitted':False})
        raise


def run(config,stage):
    verify(config,stage)
    if stage in ('preflight','evaluation_preflight'):
        from ray_paths import preflight as socket_preflight
        write_new(Path(config['attempt_root'])/'ray_socket_preflight.json',
                  socket_preflight(config['ray_temp']))
    if stage=='evaluation_preflight':
        import runtime,evaluation_generation
        runtime.build_engine=lambda c,m:evaluation_generation.build_engine(c)
        runtime.preflight(config);return
    if stage=='evaluation_generate':
        from evaluation_generation import generate
        manifest=json.loads(Path(config['manifest']).read_text())
        return generate(config,manifest,list(range(8)),root=config['stage_root'])
    if stage=='preflight':
        import runtime,anchor_runtime
        runtime.build_engine=anchor_runtime.build_engine
        # Frozen non-probe engine construction checks the physical device, then
        # generates one health token. It precedes the outer technical attempt.
        runtime.preflight(config);return
    if stage in ('generate','probabilities'):
        cells=json.loads(Path(config['cells_path']).read_text())
        if stage=='generate':
            from generation_core import generate
            return generate(config,cells,root=config['stage_root'])
        return probabilities(config,cells)
    if stage=='export':
        from training_checkpoint import export
        return export(config['checkpoint'],config['stage_root'],
                      model_config=config['initial_model'],tokenizer=config['tokenizer'])
    from trainer_core import policy_session,update,replay_saved
    with policy_session(config,checkpoint=config.get('checkpoint')) as (policy,tokenizer):
        if stage=='update':
            return update(policy,json.loads(Path(config['groups_path']).read_text()),
                pad_token_id=tokenizer.pad_token_id,terminal_token_ids=config['terminal_token_ids'],
                loss_config=config['loss_config'],root=config['stage_root'],provenance=config['provenance'],
                lease_check=lambda:check_lease(config),replay=False)
        return replay_saved(policy,config['source_update'],root=config['stage_root'],
                            loss_config=config['loss_config'],lease_check=lambda:check_lease(config))


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--config',type=Path,required=True)
    parser.add_argument('--stage',choices=STAGES,required=True)
    args=parser.parse_args();run(json.loads(args.config.read_text()),args.stage)


if __name__=='__main__':main()
