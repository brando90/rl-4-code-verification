"""Verify additional frozen start weights/configs before enabling a remote training size."""
import argparse
import hashlib
from pathlib import Path
import shutil
import subprocess
import time
from recovery_watch import read, write

HERE = Path(__file__).resolve().parent
WORK = Path('/lfs/skampere1/0/brando9/rl4cv_e08')
SHARED = Path('/dfs/scratch0/brando9/rl4cv_e08_v3_remote')
SIZES = {'1p7b': '1.7B', '4b': '4B', '8b': '8B', '14b': '14B'}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('sizes', nargs='+', choices=SIZES)
    args = parser.parse_args()
    hashes = {}
    for short in args.sizes:
        size = SIZES[short]
        src = WORK / f'ckpt/{size}/hf/step_658'
        dest = SHARED / f'ckpt/{size}/hf/step_658'
        if not (dest / 'SHA256SUMS').exists():
            temp = dest.with_name('.transfer_step_658'); temp.mkdir(parents=True, exist_ok=True)
            subprocess.run(['rsync', '-a', str(src) + '/', str(temp) + '/'], check=True)
            subprocess.run(['sha256sum', '--check', '--quiet', 'SHA256SUMS'], cwd=temp, check=True)
            temp.rename(dest)
        assert (src / 'SHA256SUMS').read_bytes() == (dest / 'SHA256SUMS').read_bytes()
        subprocess.run(['sha256sum', '--check', '--quiet', 'SHA256SUMS'], cwd=dest, check=True)
        for condition in ('E', 'R'):
            name = f'configs/e08_v3_{condition}_{size}.yaml'
            target = SHARED / 'code/expt_v3' / name
            temp = target.with_suffix('.staging'); temp.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(HERE / name, temp); temp.replace(target)
            hashes[name] = hashlib.sha256(target.read_bytes()).hexdigest()
        print(f'{size}: exact start weights and configs verified', flush=True)
    path = SHARED / 'sft_v3/remote_ready.json'
    ready = read(path); assert ready['status'] == 'PASS'
    ready['verified_sizes'] = sorted(set(ready.get('verified_sizes', ['14b'])) | set(args.sizes))
    ready['input_hashes'].update(hashes)
    ready['size_extension_unix'] = time.time()
    write(path, ready); write(HERE / 'results/remote_preparation_v3.json', ready)


if __name__ == '__main__':
    main()
