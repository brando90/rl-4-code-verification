import json
R=json.load(open('../repos.json'))
GB=1e9
for r in R:
    lic=r.get('license')
    if r['id'].startswith('marin-community/'):
        r['license_text_source']='README front matter license: apache-2.0 + tag research-only + "research artifact" sentence; no LICENSE file in repo'
        r['license_verdict']='PERMISSIVE (Apache-2.0 declared); research-only tag compatible with research use; ok to use'
        r['intermediate_step_branches']=False if r['refs']['branches']==['main'] else True
    else:
        r['license_text_source']='none: no README license text, no license_name/license_link in cardData, no LICENSE file' if lic=='other' else 'none: repo has no README/model card and no license field at all'
        r['license_verdict']='UNCLEAR -> NOT USED (default rule); upstream: base Apache-2.0, SFT data wildchat_386k (nyu-dice-lab/wildchat50m-rewild-sft-385700, license:other) + delphi_warmup' if lic=='other' else 'NO LICENSE DECLARED -> NOT USED (default rule); upstream chain base Apache-2.0 -> midtrain/SFT (license other) -> RL'
        r['intermediate_step_branches']=False if r['refs']['branches']==['main'] else True
    r['arch_summary']=f"{(r.get('config') or {}).get('architectures')} vocab={(r.get('config') or {}).get('vocab_size')} dtype_in_config={(r.get('config') or {}).get('torch_dtype') or (r.get('config') or {}).get('dtype')} weights_dtype={list((r.get('safetensors_params_by_dtype') or {}).keys())}"
    r['safetensors_total_bytes']=r.pop('safetensors_file_bytes')
json.dump(R,open('../repos.json','w'),indent=1)
# disk per arm
arms={}
for r in R: arms.setdefault(r['arm'],[]).append(r)
def s(ids): 
    d={r['id']:r['safetensors_total_bytes'] for r in R}
    return sum(d[i] for i in ids)
q1=[r['id'] for r in R if r['arm'].startswith('Q1')]
q2a=['marin-community/delphi-1e21-3.4Bparams-46.3Btokens','marin-community/delphi-1e22-9.7Bparams-160Btokens','marin-community/delphi-1e23-25Bparams-628Btokens']
q2b=[r['id'] for r in R if r['arm']=='Q2b_3.4B_fixedN']
q2c=[r['id'] for r in R if r['arm']=='Q2c_laion_sft_base']
q4=[r['id'] for r in R if r['arm'].startswith('Q4')]
D={'Q1_all_6_repos':s(q1),'Q1_3.4B_x3':s([i for i in q1 if '3.4B' in i]),'Q1_9.7B_x3':s([i for i in q1 if '9.7B' in i]),
'Q2a':s(q2a),'Q2b':s(q2b),'Q2c':s(q2c),'Q4_start_plus_4':s(q4),
'Q2a_union_Q2b':s(set(q2a)|set(q2b)),
'Q1_union_Q2a_union_Q2b':s(set(q1)|set(q2a)|set(q2b)),
'all_arms_union':s(set(q1)|set(q2a)|set(q2b)|set(q2c)|set(q4)),
'max_single_repo_25B':s(q2a[2:]),'max_single_repo_9.7B_marin_fp32':s(['marin-community/delphi-1e22-9.7Bparams-160Btokens']),
'Q2b_unique_beyond_Q2a':s(set(q2b)-set(q2a)),
'Q2a_unique_beyond_Q1':s(set(q2a)-set(q1))}
D={k:{'bytes':v,'GB':round(v/1e9,2),'GiB':round(v/2**30,2)} for k,v in D.items()}
json.dump(D,open('../disk_need.json','w'),indent=1)
for k,v in D.items(): print(k,v)
