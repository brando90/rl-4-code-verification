import json,urllib.request,urllib.error,time
def get(url,raw=False):
    for i in range(3):
        try:
            r=urllib.request.urlopen(urllib.request.Request(url,headers={'User-Agent':'audit0e'}),timeout=60)
            b=r.read()
            return (b if raw else json.loads(b)),r.status
        except urllib.error.HTTPError as e:
            return None,e.code
        except Exception as e:
            time.sleep(2)
    return None,-1
M=json.load(open('../raw/list_marin-community.json'))
L=json.load(open('../raw/list_laion.json'))
mids=[x['id'] for x in M]
lids=[x['id'] for x in L]
def mar(pred): return [i for i in mids if pred(i)]
want={}
want['Q1_3.4B']=[i for i in mids if i.startswith('marin-community/delphi-1e21-3.4B')]
want['Q1_9.7B']=[i for i in mids if i.startswith('marin-community/delphi-1e22-9.7B')]
want['Q2a_25B']=['marin-community/delphi-1e23-25Bparams-628Btokens']
want['Q2b_3.4B_fixedN']=['marin-community/delphi-3e19-3.4Bparams-1.4Btokens','marin-community/delphi-9e19-3.4Bparams-4.2Btokens','marin-community/delphi-2e20-3.4Bparams-8.3Btokens','marin-community/delphi-3e20-3.4Bparams-13.9Btokens','marin-community/delphi-1e21-3.4Bparams-46.3Btokens']
want['Q2c_laion_sft_base']=[f'laion/delphi-{a}-base-wc386k_lr1e5-sft' for a in ['3e18-447Mparams-1.2Btokens','9e18-550Mparams-2.9Btokens','2e19-837Mparams-3.6Btokens','3e19-998Mparams-5Btokens','9e19-1.4Bparams-10.6Btokens','2e20-1.9Bparams-14.8Btokens','3e20-2.5Bparams-18.6Btokens','1e21-3.4Bparams-46.3Btokens','1e22-9_7Bparams-160Btokens']]
want['Q4_start']=['laion/delphi-1e22-p33m67-32p07b-lr0_67-54770ae7-wc386k_lr1e5-sft']
want['Q4_endpoints']=[f'laion/delphi-1e22-p33m67-wc386k_sft-rl-{a}-9_7B' for a in ['D1rlvrmath-60','D2ifeval-60','D3dapomath-20','D4math500-80']]
out=[]
for arm,ids in want.items():
    for rid in ids:
        d,st=get(f'https://huggingface.co/api/models/{rid}?blobs=true')
        rec={'arm':arm,'id':rid,'api_status':st}
        if d:
            cd=d.get('cardData') or {}
            rec['license']=cd.get('license'); rec['license_name']=cd.get('license_name'); rec['license_link']=cd.get('license_link')
            rec['tags']=[t for t in d.get('tags',[]) if not t.startswith('dataset:')]
            rec['gated']=d.get('gated'); rec['private']=d.get('private'); rec['sha']=d.get('sha'); rec['lastModified']=d.get('lastModified'); rec['createdAt']=d.get('createdAt')
            st_=d.get('safetensors') or {}
            rec['safetensors_total_params']=st_.get('total'); rec['safetensors_params_by_dtype']=st_.get('parameters')
            sib=d.get('siblings',[])
            rec['files']=[(s['rfilename'],s.get('size')) for s in sib]
            rec['safetensors_file_bytes']=sum(s.get('size') or 0 for s in sib if s['rfilename'].endswith('.safetensors'))
            rec['total_repo_bytes']=sum(s.get('size') or 0 for s in sib)
            rec['has_license_file']=[s['rfilename'] for s in sib if 'licen' in s['rfilename'].lower()]
            c,cs=get(f'https://huggingface.co/{rid}/resolve/main/config.json',raw=True)
            if c:
                try:
                    cj=json.loads(c)
                    rec['config']={k:cj.get(k) for k in ['architectures','model_type','vocab_size','torch_dtype','dtype','hidden_size','num_hidden_layers','num_attention_heads','num_key_value_heads','max_position_embeddings','tie_word_embeddings','rope_theta']}
                except Exception as e: rec['config_err']=str(e)
            else: rec['config_status']=cs
            r,rs=get(f'https://huggingface.co/api/models/{rid}/refs')
            if r:
                rec['refs']={k:[x['name'] for x in v] for k,v in r.items()}
            else: rec['refs_status']=rs
        out.append(rec); print(arm,rid,st,rec.get('license'),rec.get('safetensors_file_bytes'),flush=True)
json.dump(out,open('../repos.json','w'),indent=1)
