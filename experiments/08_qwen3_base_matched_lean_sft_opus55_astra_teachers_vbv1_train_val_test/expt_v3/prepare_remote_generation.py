"""Copy the exact generator environment and validation-only prompt inputs remotely."""
from __future__ import annotations
import hashlib
import json
import os
from pathlib import Path
import shlex
import shutil
import subprocess
import sys
import time
from recovery_watch import write

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[2]
WORK = Path('/lfs/skampere1/0/brando9/rl4cv_e08')
SHARED = Path('/dfs/scratch0/brando9/rl4cv_e08_v3_remote')
EXP = HERE.parent.name
VB103 = 'experiments/103_single_call_baselines_all_models_vbv1_vbv2_valkyrie_validated_fsc_judge'


def digest(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as stream:
        for chunk in iter(lambda: stream.read(4 * 1024**2), b''):
            h.update(chunk)
    return h.hexdigest()


def main():
    sys.path.insert(0, str(REPO / 'src'))
    from rl4cv.veribench.exp103 import build_prompt
    ids_source = HERE.parent / 'expt_v1/results/split/vbv1_validation_task_ids.txt'
    ids = ids_source.read_text().splitlines()
    assert len(ids) == len(set(ids)) == 135
    source_pack = Path('/lfs/skampere1/0/brando9/veribench_vb103') / VB103 / 'private/packs/vbv1_896'
    source_vb = WORK / 'rl-4-code-verification/external/veribench'
    repo = SHARED / 'generation_repo'
    pack = SHARED / 'validation_prompt_pack'
    vb = SHARED / 'generation_veribench'
    hashes, prompts = {}, {}

    def copy(source, destination):
        destination.parent.mkdir(parents=True, exist_ok=True)
        temp = destination.with_name(destination.name + '.staging')
        shutil.copy2(source, temp)
        assert digest(source) == digest(temp)
        os.replace(temp, destination)
        hashes[str(destination.relative_to(SHARED))] = digest(destination)

    for relative in ('rl4cv/__init__.py', 'rl4cv/veribench/__init__.py',
                     'rl4cv/veribench/generate.py', 'rl4cv/veribench/exp103.py', 'rl4cv/veribench/pack.py'):
        copy(REPO / 'src' / relative, repo / 'src' / relative)
    copy(ids_source, repo / 'experiments' / EXP / 'expt_v1/results/split' / ids_source.name)
    for name in ('single_call.py', 'prompts/addendum_vbv1.md'):
        relative = Path(VB103) / 'scripts/valkyrie_single_call_agent' / name
        copy(source_vb / relative, vb / relative)
    for task in ids:
        copy(source_pack / task / 'instruction.md', pack / task / 'instruction.md')
        p = build_prompt((source_pack / task / 'instruction.md').read_text(), root=source_vb)
        prompts[task] = {name: getattr(p, name) for name in (
            'instruction_sha256', 'addendum_sha256', 'prompt_sha256', 'system_prompt_sha256')}
    assert {p.name for p in pack.iterdir()} == set(ids)
    for name in ('run_validation.sh', 'remote_generation.py', 'remote_training.py', 'job_process.py', 'recovery_watch.py'):
        copy(HERE / name, SHARED / 'code/expt_v3' / name)
    copy(HERE / 'results/ladder_manifest_v3.json', SHARED / 'code/expt_v3/results/ladder_manifest_v3.json')
    write(SHARED / 'sft_v3/generation_prompt_hashes.json', prompts)
    write(HERE / 'results/generation_prompt_hashes_v3.json', prompts)
    archive = SHARED / 'generation_env.tar.zst'
    python_runtime = (WORK / 'venv_gen/bin/python').resolve().parents[1]
    if not archive.exists():
        temp = archive.with_name(archive.name + '.staging')
        subprocess.run(['tar', '--zstd', '-cf', str(temp),
                        '--transform', f's|^{python_runtime.name}|python_runtime|',
                        '-C', str(WORK), 'venv_gen', '-C', str(python_runtime.parent), python_runtime.name], check=True)
        os.replace(temp, archive)
    archive_sha = digest(archive)
    (archive.with_suffix('.zst.sha256')).write_text(f'{archive_sha}  {archive}\n')
    probe = '''import importlib.metadata as m,json,sys,torch,vllm,transformers,flashinfer
print(json.dumps({'python':sys.version,'versions':{p:m.version(p) for p in ['vllm','torch','transformers','flashinfer-python']}}))'''
    source = json.loads(subprocess.check_output([str(WORK / 'venv_gen/bin/python'), '-c', probe], text=True))
    evidence = {}
    for host in ('skampere3', 'skampere2'):
        local = Path(f'/lfs/{host}/0/brando9/rl4cv_e08_v3_gen')
        code = '''import os,pathlib,subprocess,sys,json
root=pathlib.Path(sys.argv[1]); archive=sys.argv[2]; source=sys.argv[3]; expected=sys.argv[4]
root.mkdir(parents=True,exist_ok=True)
marker=root/'EXTRACTED'
if not marker.exists():
 assert os.statvfs(root).f_bavail*os.statvfs(root).f_frsize > 12*1024**3
 subprocess.run(['tar','--zstd','-xf',archive,'-C',str(root)],check=True)
 marker.write_text(expected)
assert marker.read_text()==expected
env=root/'venv_gen'
for directory,_,files in os.walk(env):
 for name in files:
  p=pathlib.Path(directory)/name
  if p.is_symlink():
   dest=os.readlink(p)
   if name=='python' and p.parent.name=='bin':p.unlink();p.symlink_to(root/'python_runtime/bin/python3.12')
   elif source in dest:p.unlink();p.symlink_to(dest.replace(source,str(root)))
  elif p.parent.name=='bin' or name.endswith(('.pth','_finder.py')) or name in ('direct_url.json','pyvenv.cfg'):
   if p.stat().st_size>2000000:continue
   data=p.read_bytes()
   if b'\\0' not in data and source.encode() in data:p.write_bytes(data.replace(source.encode(),str(root).encode()))
cfg=env/'pyvenv.cfg'
cfg.write_text('\\n'.join('home = '+str(root/'python_runtime/bin') if line.startswith('home = ') else line for line in cfg.read_text().splitlines())+'\\n')
print(json.dumps({'python':str(env/'bin/python')}))
'''
        result = subprocess.run(['ssh', '-o', 'BatchMode=yes', host, shlex.join([
            '/usr/bin/python3', '-', str(local), str(archive), str(WORK), archive_sha])],
            input=code, capture_output=True, text=True, timeout=900)
        assert result.returncode == 0, (host, result.stderr[-2000:])
        env = json.loads(result.stdout)
        checked = subprocess.run(['ssh', '-o', 'BatchMode=yes', host, shlex.join([
            'env', 'CUDA_VISIBLE_DEVICES=', env['python'], '-c', probe])], capture_output=True, text=True, timeout=120)
        assert checked.returncode == 0, (host, checked.stderr[-2000:])
        observed = json.loads(checked.stdout)
        assert observed == source, (host, observed, source)
        evidence[host] = {'root': str(local), 'python': env['python'], 'runtime': observed}
        print(f'{host}: exact generator environment verified', flush=True)
    ready = {'status': 'PASS', 'prepared_unix': time.time(), 'archive_sha256': archive_sha,
             'verified_hosts': list(evidence), 'host_environments': evidence, 'input_hashes': hashes,
             'task_count': 135, 'task_ids_sha256': digest(ids_source), 'prompt_hashes_sha256': digest(SHARED / 'sft_v3/generation_prompt_hashes.json'),
             'test_split_opened': False, 'scientific_changes': False, 'repo': str(repo), 'pack': str(pack), 'veribench_root': str(vb)}
    write(SHARED / 'sft_v3/remote_generation_ready.json', ready)
    write(HERE / 'results/remote_generation_preparation_v3.json', ready)
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
