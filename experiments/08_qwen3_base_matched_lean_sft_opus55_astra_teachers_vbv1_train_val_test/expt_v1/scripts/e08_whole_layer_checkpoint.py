"""Change only checkpoint granularity in a hash-verified runtime copy of pinned NeMo."""
import hashlib,inspect,json,os,pathlib
EXPECTED='366965e7d9b6360fdd845b559f8b46ce17845088dbf4e12626c0e23192dd37bd'
def install():
    import nemo_rl.models.dtensor.parallelize as par
    import nemo_rl.models.policy.dtensor_policy_worker as worker
    path=pathlib.Path(par.__file__)
    assert hashlib.sha256(path.read_bytes()).hexdigest()==EXPECTED, 'unrecognized pinned parallelizer'
    source=inspect.getsource(par._parallelize_model)
    start=source.index('    if activation_checkpointing:\n')
    end=source.index('    mp_policy = MixedPrecisionPolicy(',start)
    old=source[start:end]
    assert old.count('checkpoint_wrapper(')==4
    replacement='    if activation_checkpointing:\n        for i in range(len(layers)):\n            layers[i] = checkpoint_wrapper(layers[i])\n\n'
    revised=source[:start]+replacement+source[end:]
    ns=dict(par.__dict__);exec(compile(revised,'<e08_whole_decoder_checkpoint>','exec'),ns)
    implementation=ns['_parallelize_model']; signature=inspect.signature(implementation)
    def admitted(*args,**kwargs):
        bound=signature.bind(*args,**kwargs);bound.apply_defaults();v=bound.arguments
        assert v['tp_mesh'].size()==8 and v['cpu_offload'] and v['activation_checkpointing']
        print('E08_WHOLE_LAYER_CHECKPOINT '+json.dumps({'pinned_source_sha256':EXPECTED,'runtime_function_sha256':hashlib.sha256(revised.encode()).hexdigest(),'tp':8,'preserve_rng_state':True}),flush=True)
        os.environ['E08_WHOLE_LAYER_ACTIVE'] = '1'
        return implementation(*args,**kwargs)
    par._parallelize_model=admitted;worker._parallelize_model=admitted
