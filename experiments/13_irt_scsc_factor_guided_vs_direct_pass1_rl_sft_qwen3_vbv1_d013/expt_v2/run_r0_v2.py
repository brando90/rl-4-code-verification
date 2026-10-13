#!/usr/bin/env python3
"""Run frozen R0 once with durable per-fixture reservations and a registered process identity."""
from pathlib import Path
import json
import os
import sys

HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE))
import r0_fixtures_v2 as gate
import watchdog_e13v2 as watchdog


def main():
    wr=Path(os.environ['WR'])
    root=wr/'watchdog'
    with watchdog.locked(root):
        db=watchdog.database(root)
        watchdog.register(db,'e13v2','r0_gate',os.getpid())
        db.close()
    measure=gate.inspect_source

    def recorded(source, **kwargs):
        cell='R0/'+Path(source).stem
        with watchdog.locked(root):
            db=watchdog.database(root)
            attempt=watchdog.begin(db,'e13v2',cell,kwargs['expected_sha256'])
            db.close()
        try:
            result=measure(source,**kwargs)
        except Exception:
            # Failed measurement is not a typed scientific exclusion and is never retried.
            with watchdog.locked(root):
                db=watchdog.database(root)
                db.execute('UPDATE attempts SET status=?,finished=? WHERE run=? AND cell=? AND attempt=?',
                           ('unresolved_measurement',watchdog.now(),'e13v2',cell,attempt))
                db.commit();db.close()
            raise
        with watchdog.locked(root):
            db=watchdog.database(root)
            watchdog.finish(db,'e13v2',cell,attempt,'measured')
            db.close()
        return result
    gate.inspect_source=recorded
    return gate.run(wr/'r0',Path(os.environ['E13_LAKE_DIR']),Path(os.environ['E13_SCORER_ROOT']))


if __name__=='__main__':
    raise SystemExit(main())
