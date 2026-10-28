import re,json,sys,csv,ast
base='../q4_endpoints/'
res={}
for d in ['D1rlvrmath-60','D2ifeval-60','D3dapomath-20','D4math500-80']:
    rows=[]
    for line in open(base+d+'/train.out',errors='replace'):
        m=re.search(r'WANDB_MIRROR kind=(\w+) step=(\d+) metrics=(\{.*\})',line)
        if m:
            try: met=json.loads(m.group(3))
            except Exception: continue
            rows.append((m.group(1),int(m.group(2)),met))
    kinds={}
    for k,s,met in rows: kinds.setdefault(k,[]).append((s,met))
    res[d]={k:len(v) for k,v in kinds.items()}
    tr=sorted(kinds.get('train',[]))
    with open(base+d+'/train_steps.csv','w',newline='') as f:
        keys=['step','reward/avg_raw_reward','reward/avg_pass_at_8','generate/avg_num_tokens','generate/max_num_tokens','policy/entropy','loss/avg_final_rewards','loss/avg_raw_advantages_abs']
        w=csv.writer(f); w.writerow(keys)
        for s,met in tr: w.writerow([s]+[met.get(k) for k in keys[1:]])
    if tr:
        print(d,'train steps',len(tr),'first/last',tr[0][0],tr[-1][0],'keys',list(tr[0][1].keys())[:40])
        rr=[met.get('reward/avg_raw_reward') for s,met in tr]
        print('  reward first5',[round(x,3) for x in rr[:5]],'last5',[round(x,3) for x in rr[-5:]], 'max',round(max(rr),3),'argmax step',tr[rr.index(max(rr))][0])
    for k in kinds:
        if k!='train': print('  kind',k,len(kinds[k]),list(kinds[k][0][1].items())[:6])
print(res)
