"""Run the single authorized, ledger-bounded Astra code port in an isolated SNAP micro-repository."""
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import time

RUN=Path('/lfs/skampere1/0/eth127/rl4cv_tiny_training')
EXP=RUN/'repo/experiments/08_qwen3_base_matched_lean_sft_opus55_astra_teachers_vbv1_train_val_test'
ROOT=RUN/'gx10_port_v19/astra'


def write(path,value):
    path.parent.mkdir(parents=True,exist_ok=True);tmp=path.with_suffix(path.suffix+'.tmp')
    tmp.write_text(json.dumps(value,indent=2,sort_keys=True)+'\n');tmp.replace(path)


def main():
    sys.path.insert(0,str(EXP/'expt_v15'));import campaign_budget as budget
    ROOT.mkdir(parents=True,exist_ok=True);assert not (ROOT/'completion.json').exists(),'Port run already completed'
    work=ROOT/'work';profile=ROOT/'profile';work.mkdir(exist_ok=True);profile.mkdir(exist_ok=True)
    assert not (ROOT/'cli.jsonl').exists(),'Preserve existing port attempt'
    subprocess.run(['git','init','-q',str(work)],check=True)
    for name in ('train.py','assemble.py','PROTOCOL.md'):shutil.copyfile(EXP/'expt_v12'/name,work/name)
    context=dict(gx10_root='/home/lethan3/workspace/rl4cv-gx10/experiment-v19',
        python='/home/lethan3/workspace/rl4cv-gx10/training-v14/.venv/bin/python',torch='2.9.1+cu130',
        transformers='4.55.4',cpu_cores=20,memory_gib=119,gpu='GB10',compute_capability='12.1',
        original_torch='2.7.1+cu128',optimizer_launch_allowed=False,production_condition='final_v18_only')
    write(work/'runtime_context.json',context)
    (work/'AGENTS.md').write_text('Implement the supplied code-port assignment only. No GPU runs, provider calls, model downloads, external edits or messages. Preserve frozen scientific settings and source checks.\n')
    template=RUN/'lean_corpus_v13/runtime/lane_00/config.toml';config=template.read_text()
    assert 'api.openai.com' in config and 'TINY_OPENAI_API_KEY' in config
    import tomllib
    assert tomllib.loads(config).get('service_tier') in (None,'default'),'No fast/priority tier authorized'
    (profile/'config.toml').write_text(config)
    prompt=(Path(__file__).with_name('astra_port_prompt.md')).read_text();(ROOT/'prompt.md').write_text(prompt)
    env=dict(os.environ,CODEX_HOME=str(profile),CUDA_VISIBLE_DEVICES='',TOKENIZERS_PARALLELISM='false')
    env['TINY_OPENAI_API_KEY']=(RUN/'.private/lab-openai.key').read_text().strip()
    command=['/usr/local/bin/codex','exec','--dangerously-bypass-approvals-and-sandbox','--skip-git-repo-check',
        '-m','gpt-6-astra','-c','model_reasoning_effort="high"','-c','model_context_window=64000',
        '-c','model_auto_compact_token_limit=50000','--json','-o',str(ROOT/'final.txt'),'-']
    helptext=subprocess.check_output(['/usr/local/bin/codex','exec','--help'],text=True)
    if '--service-tier' in helptext:command[2:2]=['--service-tier','default']
    def started(pid,when):write(ROOT/'running.json',dict(pid=pid,started_unix=when,model='gpt-6-astra',effort='high',
        reserve_usd=40,observed_stop_usd=3,context_window=64000,timeout_seconds=900,scope='code port only',
        official_rates_source='https://developers.openai.com/api/docs/models/gpt-6-astra',
        official_max_context=1050000,official_max_output=128000,max_single_request_upper_usd=35.85))
    result=budget.run_cli(command,env,prompt,purpose='adaptation',identity='astra_gx10_codeport_v19',profile=profile,
        cwd=work,stdout_path=ROOT/'cli.jsonl',reservation=40,stop_at=3,timeout=900,on_start=started,model='gpt-6-astra')
    write(ROOT/'completion.json',dict(result,finished_unix=time.time(),model='gpt-6-astra',effort='high',
        output_files=[p.name for p in work.iterdir() if p.is_file()],scientific_condition_changed=False))
    print(json.dumps(result,sort_keys=True),flush=True)


if __name__=='__main__':main()
