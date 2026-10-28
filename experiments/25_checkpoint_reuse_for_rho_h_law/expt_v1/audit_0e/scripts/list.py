import json,urllib.request,sys,re
def get(url):
    req=urllib.request.Request(url,headers={'User-Agent':'audit0e'})
    r=urllib.request.urlopen(req,timeout=60)
    return r.read(), r.headers
def listall(author):
    url=f"https://huggingface.co/api/models?author={author}&search=delphi&limit=100&full=false"
    out=[]
    while url:
        b,h=get(url)
        out+=json.loads(b)
        link=h.get('Link')
        url=None
        if link:
            m=re.search(r'<([^>]+)>; rel="next"',link)
            if m:url=m.group(1)
    return out
for a in ['marin-community','laion']:
    L=listall(a)
    json.dump(L,open(f'../raw/list_{a}.json','w'))
    print(a,len(L))
