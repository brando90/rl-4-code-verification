import json,re,csv
out={}
sha=json.load(open('../repos.json'))
start=[r for r in sha if r['arm']=='Q4_start'][0]
out['start_repo_in_plan']='laion/delphi-1e22-p33m67-32p07b-lr0_67-54770ae7-wc386k_lr1e5-sft'
out['start_repo_sha_now']=start['sha']; out['start_repo_snapshot_used_by_authors_log']='511c4ea0e57973b890a542eb70f3b4429dea1d74'
for d in ['D1rlvrmath-60','D2ifeval-60','D3dapomath-20','D4math500-80']:
    txt=open(f'../q4_endpoints/{d}/train.out',errors='replace').read()
    g=lambda k: sorted(set(re.findall(r'^\+ (?:export )?'+k+r'=(.*)$',txt,flags=re.M)))
    cmd=re.search(r'main_base (.*)',txt)
    args=cmd.group(1) if cmd else ''
    def a(k):
        m=re.search(re.escape(k)+r'=(\S+)',args); return m.group(1).strip("'") if m else None
    rows=list(csv.DictReader(open(f'../q4_endpoints/{d}/train_steps.csv')))
    rew=[float(x['reward/avg_raw_reward']) for x in rows]; ntok=[float(x['generate/avg_num_tokens']) for x in rows]
    out[d]={'MODEL_PATH_in_log':g('MODEL_PATH'),'DATASET':g('DATASET'),'ENV_CLASS':g('ENV_CLASS'),
     'lr':a('trainer.policy.optimizer_config.lr'),'G_n_samples_per_prompt':a('generator.n_samples_per_prompt'),
     'train_batch_size_prompts':a('trainer.train_batch_size'),'rollouts_per_step':int(a('trainer.train_batch_size'))*int(a('generator.n_samples_per_prompt')),
     'max_steps':a('trainer.max_steps'),'epochs':a('trainer.epochs'),'temperature':a('generator.sampling_params.temperature'),
     'max_generate_length':a('generator.sampling_params.max_generate_length'),'max_prompt_length':a('trainer.max_prompt_length'),
     'use_kl_loss':a('trainer.algorithm.use_kl_loss'),'entropy_coef':a('trainer.algorithm.entropy_loss_coef'),'ckpt_interval':a('trainer.ckpt_interval'),
     'advantage_estimator':a('trainer.algorithm.advantage_estimator'),'train_data':re.search(r"data.train_data=\[?'?\\?'?([^\s']+)",args).group(1) if re.search(r"data.train_data=\[?'?\\?'?([^\s']+)",args) else None,
     'n_train_steps_logged':len(rows),'reward_step1':rew[0],'reward_max':max(rew),'reward_argmax_step':rows[rew.index(max(rew))]['step'],'reward_last':rew[-1],
     'mean_tokens_step1':ntok[0],'mean_tokens_last':ntok[-1]}
json.dump(out,open('../q4_summary.json','w'),indent=1)
print(json.dumps(out,indent=1)[:5000])
