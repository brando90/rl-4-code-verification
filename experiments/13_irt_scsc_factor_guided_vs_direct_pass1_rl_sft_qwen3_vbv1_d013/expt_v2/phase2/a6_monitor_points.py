"""Retain B's ten-update monitoring through the sole published A6 extension to 60."""
from technical_ledger import published


def valid_checkpoint(arm,seed,update):
    return (arm=='B' and type(seed)is int and seed==1301 and type(update)is int
        and update in (0,10,20,30,40,50,60))


def require_extension(update,reference,repository,execution_sha):
    if update<=30:return
    if reference is None:raise ValueError('B monitor extension requires the published T5 decision')
    result=published(reference,repository)
    expected={'condition':'v2-S2','gate':'T5','arm':'B','seeds':[1301],
        'metric':'own train reward','horizon':30,'status':'EXTEND_TO_60',
        'admission_statistics_computed':True,'pilot_execution_sha256':execution_sha}
    if any(result.get(k)!=v for k,v in expected.items()):
        raise ValueError('B monitor extension differs from the published T5 decision')
