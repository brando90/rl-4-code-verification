"""Verify completed staging, relocate copied environments, and prepare frozen TP8 inputs."""
from __future__ import annotations
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import time
import argparse
from recovery_watch import write

HERE = Path(__file__).resolve().parent
SOURCE = Path('/lfs/skampere1/0/brando9/rl4cv_e08')
TARGET = Path('/dfs/scratch0/brando9/rl4cv_e08_v3_remote')
PIN = 'c751f811217db7df0d4c94abdeaada6626cfc150'


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--archive-local', action='store_true')
    args = parser.parse_args()
    exit_path = SOURCE / 'sft_v3/remote_stage_nemo_recovery-01.exit'
    if args.archive_local:
        archive = TARGET / 'nemo_rl_env.tar.zst'
        subprocess.run(['sha256sum', '--check', '--quiet', str(archive) + '.sha256'], check=True)
    else:
        assert exit_path.read_text().strip() == '0', 'Staging must finish before relocation'
        assert subprocess.check_output(['git', '-C', str(TARGET / 'nemo_rl'), 'rev-parse', 'HEAD'], text=True).strip() == PIN
        dry = subprocess.check_output(['rsync', '-aHn', '--stats', str(SOURCE / 'nemo_rl') + '/',
                                       str(TARGET / 'nemo_rl') + '/'], text=True)
        assert 'Number of regular files transferred: 0\n' in dry, dry
    replacements = []
    old, new = str(SOURCE).encode(), str(TARGET).encode()
    # Only copied environment launchers and install metadata are relocated.
    for envroot in (() if args.archive_local else (TARGET / 'nemo_rl/.venv', TARGET / 'nemo_rl/venvs')):
        for directory, _, files in os.walk(envroot):
            for name in files:
                path = Path(directory) / name
                if path.is_symlink():
                    dest = os.readlink(path)
                    if str(SOURCE) in dest:
                        path.unlink(); path.symlink_to(dest.replace(str(SOURCE), str(TARGET)))
                        replacements.append(str(path.relative_to(TARGET)))
                    continue
                if path.parent.name != 'bin' and not (name.endswith('.pth') or name.endswith('_finder.py') or name == 'direct_url.json'):
                    continue
                if path.stat().st_size > 2_000_000:
                    continue
                data = path.read_bytes()
                if b'\0' not in data and old in data:
                    path.write_bytes(data.replace(old, new)); replacements.append(str(path.relative_to(TARGET)))
    if not args.archive_local:
        assert not subprocess.check_output(['git', '-C', str(TARGET / 'nemo_rl'), 'status', '--porcelain'], text=True).strip()
    code = TARGET / 'code/expt_v3'; (code / 'results').mkdir(parents=True, exist_ok=True)
    paths = ['train_continuation.sh', 'remote_training.py', 'job_process.py', 'recovery_watch.py', 'PROTOCOL.md',
             'results/dry_run_v3.json', 'results/sft_schedule_v3_E.json', 'results/sft_schedule_v3_R.json',
             'configs/e08_v3_E_14B.yaml', 'configs/e08_v3_R_14B.yaml']
    hashes = {}
    for name in paths:
        (code / name).parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(HERE / name, code / name)
        hashes[name] = hashlib.sha256((code / name).read_bytes()).hexdigest()
        assert hashes[name] == hashlib.sha256((HERE / name).read_bytes()).hexdigest()
    for condition in ('E', 'R'):
        for suffix in ('nemo', 'val_dummy'):
            name = f's_v3_{condition}_{suffix}.jsonl'
            shutil.copy2(SOURCE / 'sft_v3' / name, TARGET / 'sft_v3' / name)
            digest = hashlib.sha256((TARGET / 'sft_v3' / name).read_bytes()).hexdigest()
            assert digest == hashlib.sha256((SOURCE / 'sft_v3' / name).read_bytes()).hexdigest()
            hashes[name] = digest
    subprocess.run(['sha256sum', '--check', '--quiet', 'SHA256SUMS'], cwd=TARGET / 'ckpt/14B/hf/step_658', check=True)
    # Ray's worker environments are already copied; import checks spend no GPU/model budget.
    probe = 'import sys,torch,ray,nemo_rl; print(sys.version); print(torch.__version__); print(torch.cuda.get_arch_list()); print(nemo_rl.__file__)'
    hosts = []
    evidence = {}
    environments = {}
    import shlex
    for host in ('skampere2', 'skampere3'):
        environment = TARGET / 'nemo_rl'
        if args.archive_local:
            local_root = Path(f'/lfs/{host}/0/brando9/rl4cv_e08_v3_env')
            remote_code = '''import os,pathlib,subprocess,sys,json
root=pathlib.Path(sys.argv[1]); archive=sys.argv[2]; source=sys.argv[3]; pin=sys.argv[4]
root.mkdir(parents=True,exist_ok=True)
if not (root/'EXTRACTED').exists():
 assert os.statvfs(root).f_bavail*os.statvfs(root).f_frsize > 30*1024**3
 subprocess.run(['tar','--zstd','-xf',archive,'-C',str(root)],check=True)
 (root/'EXTRACTED').write_text(archive)
assert subprocess.check_output(['git','-C',str(root/'nemo_rl'),'rev-parse','HEAD'],text=True).strip()==pin
changed=[]
for env in [root/'nemo_rl/.venv',root/'nemo_rl/venvs']:
 for directory,_,files in os.walk(env):
  for name in files:
   p=pathlib.Path(directory)/name
   if p.is_symlink():
    dest=os.readlink(p)
    if source in dest:p.unlink();p.symlink_to(dest.replace(source,str(root)));changed.append(str(p))
   elif p.parent.name=='bin' or name.endswith(('.pth','_finder.py')) or name=='direct_url.json':
    if p.stat().st_size > 2000000:continue
    data=p.read_bytes()
    if b'\\0' not in data and source.encode() in data:p.write_bytes(data.replace(source.encode(),str(root).encode()));changed.append(str(p))
assert not subprocess.check_output(['git','-C',str(root/'nemo_rl'),'status','--porcelain'],text=True).strip()
print(json.dumps({'environment':str(root/'nemo_rl'),'relocated_files':changed}))
'''
            staged = subprocess.run(['ssh', '-o', 'BatchMode=yes', '-o', 'ConnectTimeout=10', host,
                                     shlex.join(['/usr/bin/python3', '-', str(local_root), str(archive), str(SOURCE), PIN])],
                                    input=remote_code, capture_output=True, text=True, timeout=1800)
            if staged.returncode:
                evidence[host] = {'stage_exit': staged.returncode, 'stderr': staged.stderr[-2000:]}
                continue
            replacements.extend(json.loads(staged.stdout)['relocated_files'])
            environment = local_root / 'nemo_rl'
        result = subprocess.run(['ssh', '-o', 'BatchMode=yes', '-o', 'ConnectTimeout=10', host,
                                 shlex.join(['env', 'CUDA_VISIBLE_DEVICES=', str(environment / '.venv/bin/python'), '-c', probe])],
                                capture_output=True, text=True, timeout=90)
        evidence[host] = {'returncode': result.returncode, 'stdout': result.stdout, 'stderr': result.stderr[-1500:]}
        if result.returncode == 0 and str(environment) in result.stdout:
            hosts.append(host)
            environments[host] = str(environment)
    ready = {'status': 'PASS' if hosts else 'FAILED', 'verified_hosts': hosts, 'nemo_pin': PIN,
             'input_hashes': hashes, 'relocated_files': replacements, 'cpu_imports': evidence,
             'host_environments': environments, 'transfer': 'compressed archive to local environment; checkpoints stay shared' if args.archive_local else 'shared rsync',
             'baseline_sha256_check': 'PASS', 'prepared_unix': time.time(), 'scientific_changes': False}
    write(TARGET / 'sft_v3/remote_ready.json', ready)
    write(HERE / 'results/remote_preparation_v3.json', ready)
    print(json.dumps(ready, indent=2))
    return 0 if hosts else 1


if __name__ == '__main__':
    raise SystemExit(main())
