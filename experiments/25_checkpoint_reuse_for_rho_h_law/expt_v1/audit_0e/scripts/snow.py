import json,urllib.request
def get(u):
    return json.loads(urllib.request.urlopen(urllib.request.Request(u,headers={'User-Agent':'a'}),timeout=60).read())
ids=set()
for a in ['open-athena','marin-community','penfever','laion']:
    for kind in ['datasets','models']:
        for q in ['snowball','grug']:
            try:
                for x in get(f'https://huggingface.co/api/{kind}?author={a}&search={q}&limit=200'): ids.add((kind,x['id']))
            except Exception as e: print('err',a,kind,q,e)
out=[]
for kind,i in sorted(ids):
    try: d=get(f'https://huggingface.co/api/{kind}/{i}?blobs=true')
    except Exception as e: print(kind,i,'ERR',e); continue
    sib=d.get('siblings',[]); tot=sum(s.get('size') or 0 for s in sib)
    out.append({'kind':kind,'id':i,'gated':d.get('gated'),'license':(d.get('cardData') or {}).get('license'),'nfiles':len(sib),'total_bytes':tot,'files':[(s['rfilename'],s.get('size')) for s in sib],'tags':d.get('tags')})
    print(kind,i,d.get('gated'),(d.get('cardData') or {}).get('license'),len(sib),round(tot/1e9,3),'GB',flush=True)
json.dump(out,open('../raw/snowball_survey.json','w'))
