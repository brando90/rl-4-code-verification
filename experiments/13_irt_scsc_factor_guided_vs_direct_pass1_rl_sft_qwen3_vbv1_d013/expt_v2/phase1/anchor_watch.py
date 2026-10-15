"""Poll hardware and launch published independent anchor controllers under their own locks."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import subprocess
import sys

from device_watch import poll
from anchor_storage import write_new,mkdir


def run(root):
    root=Path(root);mkdir(root)
    receipt=poll(root/'observations')
    children=[]
    for plan in sorted(root.glob('*.plan.json')):
        with (root/(plan.stem+'.log')).open('a') as output:
            child=subprocess.Popen([sys.executable,str(Path(__file__).with_name('anchor_dispatch.py')),
                                    '--plan',str(plan)],stdout=output,stderr=subprocess.STDOUT,
                                    stdin=subprocess.DEVNULL,start_new_session=True)
        children.append({'plan':str(plan),'pid':child.pid})
    return {'checked_utc':receipt['checked_utc'],'controllers':children,
            'device_claims_by_poller':0,'publication_and_lease_checks':'in each controller'}


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--root',type=Path,required=True)
    print(json.dumps(run(parser.parse_args().root)))
