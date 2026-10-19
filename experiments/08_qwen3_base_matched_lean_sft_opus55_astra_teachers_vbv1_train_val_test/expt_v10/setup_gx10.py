"""Install the pinned native ARM Lean release and matching Mathlib cache on the authorized GX10."""
from pathlib import Path
import hashlib
import json
import os
import subprocess
import time
import urllib.request

ROOT=Path.home()/'workspace/rl4cv-gx10/lean-v4.22.0'
ROOT.mkdir(parents=True,exist_ok=True)

def write(name,data):
    (ROOT/name).write_text(json.dumps(data,indent=2)+'\n')
def stage(name):
    write('setup_status.json',dict(state='DONE' if name=='DONE' else 'RUNNING',stage=name,pid=os.getpid(),observed_unix=time.time()))
    print(name,flush=True)
def command(args,**kwargs):
    print('RUN',args,flush=True)
    return subprocess.run(args,check=True,**kwargs)

try:
    stage('download_native_lean')
    release=json.load(urllib.request.urlopen('https://api.github.com/repos/leanprover/lean4/releases/tags/v4.22.0',timeout=60))
    asset=next(a for a in release['assets'] if a['name']=='lean-4.22.0-linux_aarch64.tar.zst')
    archive=ROOT/asset['name']
    if not archive.exists() or archive.stat().st_size!=asset['size']:
        temporary=archive.with_suffix('.part')
        command(['curl','--fail','--location','--retry','2','--output',str(temporary),asset['browser_download_url']])
        assert temporary.stat().st_size==asset['size']
        temporary.replace(archive)
    digest=hashlib.sha256(archive.read_bytes()).hexdigest()
    if asset.get('digest'):assert asset['digest']=='sha256:'+digest
    write('lean_asset.json',dict(name=asset['name'],url=asset['browser_download_url'],bytes=asset['size'],sha256=digest,release_digest=asset.get('digest')))
    toolchain=ROOT/'lean-4.22.0-linux_aarch64'
    if not (toolchain/'bin/lean').exists():command(['tar','--zstd','-xf',str(archive),'-C',str(ROOT)])
    env=dict(os.environ,PATH=str(toolchain/'bin')+':'+os.environ['PATH'],CUDA_VISIBLE_DEVICES='')
    version=subprocess.check_output([str(toolchain/'bin/lean'),'--version'],text=True,env=env)
    assert 'version 4.22.0' in version;print(version,flush=True)
    stage('checkout_pinned_mathlib')
    mathlib=ROOT/'mathlib4'
    if not (mathlib/'.git').exists():command(['git','clone','--depth','1','--branch','v4.22.0','https://github.com/leanprover-community/mathlib4.git',str(mathlib)])
    revision=subprocess.check_output(['git','-C',str(mathlib),'rev-parse','HEAD'],text=True).strip()
    assert revision=='79e94a093aff4a60fb1b1f92d9681e407124c2ca',revision
    stage('download_mathlib_cache')
    command([str(toolchain/'bin/lake'),'exe','cache','get'],cwd=mathlib,env=env)
    stage('test_mathlib_import')
    source=ROOT/'ImportControl.lean';source.write_text('import Mathlib\ntheorem gx10NativeLean422Control : (1+1 : Nat) = 2 := by rfl\n')
    result=command([str(toolchain/'bin/lake'),'env','lean','-j','1',str(source)],cwd=mathlib,env=env,capture_output=True,text=True)
    print(result.stdout,flush=True)
    write('setup_completion.json',dict(state='DONE',lean_version=version.strip(),mathlib_revision=revision,lean_archive_sha256=digest,import_control='PASS',observed_unix=time.time()))
    stage('DONE')
except Exception as exc:
    write('setup_status.json',dict(state='FAILED',error=repr(exc),observed_unix=time.time()))
    raise
