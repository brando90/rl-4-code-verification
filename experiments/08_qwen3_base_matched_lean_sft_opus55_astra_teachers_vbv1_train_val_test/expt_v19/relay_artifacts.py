"""Relay the single frozen artifact stream through two encrypted SSH connections without a local weight copy."""
import argparse
import json
from pathlib import Path
import shlex
import subprocess
import time

HERE=Path(__file__).resolve().parent
LOCAL=Path('/Users/lethan3/Documents/veribench-projects/tmp/rl4cv-gx10-transfer-v19')
CONTROL='/Users/lethan3/Documents/veribench-projects/tmp/ssh-tiny-training/control'
SNAPROOT='/lfs/skampere1/0/eth127/rl4cv_tiny_training/gx10_port_v19'
GXROOT='/home/lethan3/workspace/rl4cv-gx10/experiment-v19'


def write(path,value):
    tmp=path.with_suffix('.tmp');tmp.write_text(json.dumps(value,indent=2,sort_keys=True)+'\n');tmp.replace(path)


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--identity',default='initial');args=parser.parse_args()
    assert args.identity in ('initial','evaluation','final')
    identity=args.identity
    LOCAL.mkdir(parents=True,exist_ok=True)
    assert Path(CONTROL).exists(),'Wait for the authorized SNAP master; do not fall back to fresh gateway connections'
    started=time.time()
    receive='python3 '+shlex.quote(GXROOT+'/code/stream_artifacts.py')+' receive --output '+shlex.quote(GXROOT)
    manifest={'initial':'transfer_manifest_initial.json','evaluation':'transfer_evaluation.json','final':'transfer_final.json'}[identity]
    send='python3 '+shlex.quote(SNAPROOT+'/stream_artifacts.py')+' send --manifest '+shlex.quote(SNAPROOT+'/'+manifest)
    with (LOCAL/f'sender_{identity}.log').open('a') as serr,(LOCAL/f'receiver_{identity}.log').open('a') as rout:
        source=subprocess.Popen(['ssh','-S',CONTROL,'-o','BatchMode=yes','-o','ConnectTimeout=10','-o','ProxyCommand=/usr/bin/false','eth127@skampere1.stanford.edu',send],stdout=subprocess.PIPE,stderr=serr)
        dest=subprocess.Popen(['ssh','-o','BatchMode=yes','-o','ConnectTimeout=15','cactushacks-gx10',receive],stdin=source.stdout,stdout=rout,stderr=rout)
        source.stdout.close()
        while source.poll() is None or dest.poll() is None:
            write(LOCAL/f'progress_{identity}.json',dict(state='STREAMING',sender_pid=source.pid,receiver_pid=dest.pid,
                elapsed_seconds=time.time()-started,observed_unix=time.time(),local_weight_copy_created=False))
            if time.time()-started>3600:
                source.terminate();dest.terminate();break
            time.sleep(5)
        src=source.wait(timeout=20);dst=dest.wait(timeout=20)
    result=dict(state='DONE' if src==dst==0 else 'FAILED',sender_exit=src,receiver_exit=dst,
        elapsed_seconds=time.time()-started,observed_unix=time.time(),local_weight_copy_created=False,
        remote_completion=GXROOT+'/transfer_completion_'+identity+'.json')
    write(LOCAL/f'completion_{identity}.json',result);write(HERE/f'results/transfer_relay_{identity}.json',result);print(json.dumps(result,sort_keys=True))
    raise SystemExit(0 if result['state']=='DONE' else 1)


if __name__=='__main__':main()
