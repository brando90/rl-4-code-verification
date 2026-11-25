import json,sys
R=sys.argv[1]
runs={'B_s0':R+'/full_run_at1788/full/B_s0/log.jsonl','B_s1':R+'/full_run_at1788/full/B_s1/log.jsonl','B_s2':'B_s2_log.jsonl','A_s0':R+'/full_run_at1788/full/A_s0/log.jsonl','A_s1':R+'/full_run_at1788/full/A_s1/log.jsonl','A_s2':'A_s2_log.jsonl'}
keys=['mean_strict','mean_smooth','active_fraction','train_loss','train_max_scaled_grad','truncated','no_lean']
data={}
for k,p in runs.items():
    rows=[json.loads(l) for l in open(p) if l.strip()]
    d={}
    for r in rows: d[r['update']]=r   # last entry per update
    data[k]=d
print('runs updates:',{k:len(v) for k,v in data.items()})
def agg(k,a,b,key):
    xs=[data[k][u].get(key) for u in range(a,b+1) if u in data[k] and data[k][u].get(key) is not None]
    return sum(xs)/len(xs) if xs else float('nan')
print('%-5s %-10s'%('run','window')+' '.join('%11s'%x[:11] for x in keys))
for k in data:
    for a,b in [(1,8),(9,24),(25,48)]:
        print('%-5s %2d-%-2d     '%(k,a,b)+' '.join('%11.4f'%agg(k,a,b,x) for x in keys))
# first update where mean_strict drops: per update B_s2
print('B_s2 per update mean_strict/smooth/loss/grad:')
for u in sorted(data['B_s2']):
    r=data['B_s2'][u]; print(u,round(r['mean_strict'],3),round(r['mean_smooth'],3),round(r['train_loss'],3),r.get('train_max_scaled_grad'),r['truncated'],r.get('train_nonfinite_sequences'))
