"""Exercise missing cost counters, tampered evidence and physical storage boundaries before resource allocation."""
from pathlib import Path
import json,os,sys
import pytest
PHASE=Path(__file__).resolve().parents[1]/'experiments/13_irt_scsc_factor_guided_vs_direct_pass1_rl_sft_qwen3_vbv1_d013/expt_v2/phase2'
sys.path.insert(0,str(PHASE))
import cost_profiles as m


def ref(path):return {'path':str(path),'sha256':m.digest(path)}

def put(path,value):path.write_text(json.dumps(value));return ref(path)

def cost(path,**changes):return put(path,{'condition':'v2-S2','device_hours':.5,'accounted_cpu_hours':.1,'wall_seconds':1800,**changes})

def test_resumed_or_unreported_usage_stays_unknown(tmp_path):
    a=cost(tmp_path/'a',cumulative_timing_complete=False);b=cost(tmp_path/'b',device_hours=None)
    result=m.closed_stages([a,b]);assert result['status']=='INCOMPLETE' and all(v is None for v in result['totals'].values())
    assert len(result['missing'])==3


def test_duplicate_tampered_or_negative_receipts_are_rejected(tmp_path):
    a=cost(tmp_path/'a')
    with pytest.raises(ValueError,match='unique'):m.closed_stages([a,a])
    Path(a['path']).write_text('{}')
    with pytest.raises(ValueError,match='changed'):m.closed_stages([a])
    a=cost(tmp_path/'a',device_hours=-1)
    with pytest.raises(ValueError,match='nonnegative'):m.closed_stages([a])


def test_storage_keeps_copy_footprint_and_does_not_follow_borrowed_links(tmp_path):
    root=tmp_path/'owned';root.mkdir();p=root/'one';p.write_bytes(b'weights'*1000)
    os.link(p,root/'two');external=tmp_path/'external';external.write_bytes(b'x'*50000)
    (root/'borrowed').symlink_to(external)
    report=m.retained_files(root)
    assert report['files']==2 and report['logical_copy_bytes']==14000 and report['unique_inodes']==1
    assert report['allocated_unique_inode_bytes']==p.stat().st_blocks*512
    assert all(Path(v['path']).parent==root for v in report['inventory'])


def timing(tmp_path):
    p=tmp_path/'time.txt';p.write_text('User time (seconds): 360\nSystem time (seconds): 36\nElapsed (wall clock) time (h:mm:ss or m:ss): 1:02:03.50\nExit status: 0\n');return ref(p)


def test_actual_timed_processor_receipt_requires_success(tmp_path):
    r=timing(tmp_path);v=m.timed_processor(r);assert v['cpu_hours']==.11 and v['wall_hours']==3723.5/3600
    p=Path(r['path']);p.write_text(p.read_text().replace('Exit status: 0','Exit status: 1'))
    with pytest.raises(ValueError,match='successful'):m.timed_processor(ref(p))


def test_mandatory_costs_use_full_probe_and_disjoint_retained_storage(tmp_path):
    a=cost(tmp_path/'stage');g=put(tmp_path/'generation',{'condition':'v2-S2','status':'COMPLETE','declared':256,'completed':256,'generated_tokens':3600})
    folders=[]
    for name,size in [('raw',11),('before',20),('after',30),('export',17)]:
        root=tmp_path/name;root.mkdir();(root/'artifact').write_bytes(b'x'*size);folders.append(root)
    updated=put(tmp_path/'updated',{'condition':'v2-S2','status':'MEASURED','optimizer_updates':1,'counts':{'declared_slots':256}})
    kwargs=dict(update_costs=[a],update_result=updated,generation_costs=[a],generation_result=g,score_costs=[a],raw_roots=folders[:1],native_roots=folders[1:3],export_root=folders[3],calibration_timing=timing(tmp_path),evaluation_costs=[a])
    values,evidence=m.mandatory_measurements(**kwargs)
    assert values['generated_tokens_per_device_second']==2 and values['native_checkpoint_bytes']==30
    assert values['raw_storage_growth_bytes']==11 and values['export_bytes']==17 and values['calibration_cpu_hours']==.11
    with pytest.raises(ValueError,match='overlap'):m.mandatory_measurements(**{**kwargs,'raw_roots':[tmp_path]})
    failed=put(tmp_path/'failed_update',{'condition':'v2-S2','status':'UNMEASURED','optimizer_updates':0,'counts':{'declared_slots':256}})
    with pytest.raises(ValueError,match='actual complete'):m.mandatory_measurements(**{**kwargs,'update_result':failed})
    kwargs['generation_result']=put(tmp_path/'generation',{'condition':'v2-S2','status':'INCOMPLETE','declared':256,'completed':255,'generated_tokens':3600})
    with pytest.raises(ValueError,match='256-response'):m.mandatory_measurements(**kwargs)
