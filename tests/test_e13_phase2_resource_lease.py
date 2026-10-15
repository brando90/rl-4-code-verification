"""Keep scientific allocations separate while enforcing live canonical reservations and real idle inventory."""
import importlib.util,json,sys
from pathlib import Path
import pytest

PHASE=Path(__file__).resolve().parents[1]/'experiments/13_irt_scsc_factor_guided_vs_direct_pass1_rl_sft_qwen3_vbv1_d013/expt_v2/phase2'
sys.path.insert(0,str(PHASE));spec=importlib.util.spec_from_file_location('e13_phase2_resource_lease',PHASE/'resource_lease.py')
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)


def fixture(tmp_path):
 root=tmp_path/'registry';root.mkdir();(root/'registry.json').write_text(json.dumps({'owner':'e13v2','device_hours':144.2,
  'leases':[{'id':'historical','phase':'v2-S2-anchors','status':'RELEASED','device_hours':144.}]}))
 inventory={'inventory_complete':True,'host':'authored-host','idle_device_indices':[0,1],
  'devices':[{'index':i,'uuid':f'authored-device-{i}','memory_mib':80000,'processes':[]} for i in range(2)],
  'local_storage':{'available_bytes':10**12},'host_memory':{'available_bytes':10**12}}
 allocation={'phase':'v2-S2-technical','cumulative_device_hours':2.,'maximum_lease_seconds':3600,'maximum_active_devices':2,
  'routes':{'authored-host':{'minimum_device_memory_mib':75000,'minimum_free_storage_bytes':10**9,'minimum_host_available_bytes':10**9}},
  'reservation_bindings':[],'reservation_inventory':{'roots':[],'paths':[]},'foreign_registries':[]}
 return root,inventory,allocation


def claim(root,inventory,allocation,index=0,key='T1',sha='fixed'):
 return m.claim(root,inventory,index,allocation=allocation,allocation_sha=sha,seconds=3600,run_key=key,now=1000.)


def test_new_phase_does_not_reset_history_and_active_reservations_consume_budget(tmp_path):
 root,inventory,a=fixture(tmp_path);one=claim(root,inventory,a);two=claim(root,inventory,a,1,'T2')
 registry=json.loads((root/'registry.json').read_text());assert registry['device_hours']==144.2
 assert m.accounting(registry,a['phase'],'fixed')==(0.,2.)
 m.release(root,one['id'],cleanup_verified=True,now=1900.)
 with pytest.raises(RuntimeError,match='limit exhausted'):claim(root,inventory,a,0,'T3')
 registry=json.loads((root/'registry.json').read_text());assert m.accounting(registry,a['phase'],'fixed')==(.25,1.)
 assert registry['device_hours']==pytest.approx(144.45)


def test_changed_allocation_cannot_reset_previously_spent_budget(tmp_path):
 root,inventory,a=fixture(tmp_path);r=claim(root,inventory,a);m.release(root,r['id'],cleanup_verified=True,now=1900.)
 with pytest.raises(ValueError,match='cannot reset'):claim(root,inventory,a,sha='changed')


def test_busy_device_or_existing_other_phase_requires_wait(tmp_path):
 root,inventory,a=fixture(tmp_path);inventory['devices'][0]['processes']=[{'pid':999,'owner':'foreign'}]
 with pytest.raises(RuntimeError,match='compute process'):claim(root,inventory,a)
 inventory['devices'][0]['processes']=[];registry=json.loads((root/'registry.json').read_text())
 registry['leases'].append({'phase':'v2-S2-anchors','status':'ACTIVE','expires_unix':5000.})
 (root/'registry.json').write_text(json.dumps(registry))
 with pytest.raises(RuntimeError,match='adoption or cleanup'):claim(root,inventory,a)


def test_foreign_expired_but_unreleased_lease_still_blocks(tmp_path):
 root,inventory,a=fixture(tmp_path);foreign=tmp_path/'foreign.json';foreign.write_text(json.dumps([{
  'owner':'another-user','host':'authored-host','devices':[0],'expires_unix':1.,'status':'ACTIVE'}]))
 a['foreign_registries']=[{'path':str(foreign)}]
 with pytest.raises(RuntimeError,match='foreign lease'):claim(root,inventory,a)
 assert len(json.loads((root/'registry.json').read_text())['leases'])==1
