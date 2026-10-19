"""Freeze the minimal byte-checked prompt, extraction, scoring and summary bundle for native GX10 evaluation."""
import argparse
import hashlib
import json
from pathlib import Path
import time

RUN=Path('/lfs/skampere1/0/eth127/rl4cv_tiny_training')
REPO=RUN/'repo'
EXP=Path('experiments/08_qwen3_base_matched_lean_sft_opus55_astra_teachers_vbv1_train_val_test')
E103=Path('external/veribench/experiments/103_single_call_baselines_all_models_vbv1_vbv2_valkyrie_validated_fsc_judge/scripts/valkyrie_single_call_agent')
FROZEN={'scripts/scsc/run_real_eval.py':'6e82b3d1cd6d3686aaec3d45f273cd902b03b962c0c2eca48f2c2b4f25f41fa9','scripts/scsc/kernel_axioms.py':'5dbbdcae75ba8b22911fcb43ab1fcde45a1475cf92742a39a29ebe41116de287','experiments/71_E2_valkyrie_harbor_vals_ai_eval_code/scripts/score_scsc.py':'b3713c48e0fdb24adec93b77be8785d20e48897ee8d1fd8ce31fdf37101e81d6'}

def digest(path):return hashlib.sha256(path.read_bytes()).hexdigest()

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--output',required=True,type=Path);args=parser.parse_args();entries=[];seen=set()
    def add(source,destination,wanted=None):
        assert source.is_file() and not source.is_symlink(),str(source)
        assert destination not in seen,destination
        h=digest(source);assert wanted is None or h==wanted,(str(source),h,wanted)
        entries.append(dict(source=str(source),destination=destination,bytes=source.stat().st_size,sha256=h));seen.add(destination)
    def tree(relative,pattern='*'):
        for source in sorted((REPO/relative).rglob(pattern)):
            if source.is_file() and '__pycache__' not in source.parts and source.suffix not in ('.pyc','.olean','.ilean'):
                add(source,'repo/'+str(source.relative_to(REPO)))
    for rel,h in FROZEN.items():assert digest(REPO/'external/veribench_scorer'/rel)==h
    ids=(REPO/EXP/'expt_v1/results/split/vbv1_validation_task_ids.txt').read_text().splitlines();assert len(ids)==len(set(ids))==135
    for tid in ids:
        for name in ['instruction.md','task.toml']:add(RUN/'validation_pack'/tid/name,'validation_pack/'+tid+'/'+name)
    for name in ['validation_preflight.json','scoring_preflight.json']:add(RUN/name,'evaluation/'+name)
    tree(Path('src/rl4cv'),'*.py')
    for name in ['single_call.py','prompts/addendum_vbv1.md']:add(REPO/E103/name,'repo/'+str(E103/name))
    tree(Path('external/veribench_scorer/scripts/scsc'),'*.py')
    tree(Path('external/veribench_scorer/experiments/71_E2_valkyrie_harbor_vals_ai_eval_code/scripts'),'*.py')
    tree(Path('external/veribench_scorer/veribench_dataset/lean_src/veribench'),'*.lean')
    for rel in [EXP/'expt_v1/results/split/vbv1_validation_task_ids.txt',EXP/'expt_v1/results/split/vbv1_split_manifest.csv',EXP/'expt_v1/scripts/score_teacher_files.py',EXP/'expt_v6/analyze.py']:
        add(REPO/rel,'repo/'+str(rel))
    value=dict(identity='evaluation',declared_files=len(entries),total_bytes=sum(r['bytes'] for r in entries),entries=entries,frozen_scorer_sha256=FROZEN,validation_tasks=135,declared_cells=1080,test_split_evaluated=False,intended_use='Frozen validation prompts/extractor/scorer plus unchanged V6 binary/nonvacuity summary; no teacher/training ingestion.',observed_unix=time.time())
    assert not args.output.exists(),'Preserve the immutable transfer manifest';args.output.parent.mkdir(parents=True,exist_ok=True);args.output.write_text(json.dumps(value,indent=2,sort_keys=True)+'\n')
    print(json.dumps({k:v for k,v in value.items() if k!='entries'}),flush=True)

if __name__=='__main__':main()
