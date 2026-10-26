"""TLDR: Fence v4 stages, bind all inputs and outputs, and recover only proven infrastructure failures."""
from contextlib import contextmanager
import fcntl
import json
import os
from pathlib import Path
import time
from common import digest, object_digest, write_new
from effect_receipts import record_failure, verified_failure, retryable_empty


class RecoveryRequired(RuntimeError):
    """Incomplete effects are retained; a new sample or optimizer step is forbidden."""


def read(path):
    return json.loads(Path(path).read_text())


def tree_bindings(root):
    from retention import tensor_payload
    return {str(p.relative_to(root)):digest(p) for p in sorted(Path(root).rglob('*'))
            if p.is_file() and not tensor_payload(p,root) and not p.name.endswith('.retired.json')}


@contextmanager
def fence(root):
    Path(root).mkdir(parents=True, exist_ok=True)
    with (Path(root)/'controller.lock').open('a') as stream:
        fcntl.flock(stream, fcntl.LOCK_EX | fcntl.LOCK_NB)
        yield


class Ledger:
    def __init__(self, root, admission, *, synthetic):
        self.root=Path(root); self.admission=str(Path(admission).resolve())
        self.identity={'condition':'e13v4','admission_sha256':digest(admission),'synthetic':synthetic}

    def readmitted(self, path, intent):
        from readmission import accepts
        return accepts(self.admission, self.root, path, intent)

    def completed(self, stage):
        path=self.root/stage/'receipt.json'
        if not path.exists(): return None
        r=read(path)
        if any(r.get(k)!=v for k,v in self.identity.items()): raise ValueError('receipt admission or mode changed')
        for name, sha in r['artifacts'].items():
            if digest(path.parent/name)!=sha: raise ValueError('stage artifact changed: '+name)
        for name, sha in r['predecessors'].items():
            if digest(self.root/name/'receipt.json')!=sha: raise ValueError('predecessor receipt changed')
            self.completed(name)
        return r

    def begin(self, stage, predecessors):
        prior=self.completed(stage)
        if prior: return prior
        bindings={}
        for name in predecessors:
            receipt=self.completed(name)
            if receipt is None or receipt['status']!='PASS': raise ValueError('predecessor PASS required: '+name)
            bindings[name]=digest(self.root/name/'receipt.json')
        root=self.root/stage;root.mkdir(parents=True,exist_ok=True)
        intent={**self.identity,'stage':stage,'predecessors':bindings}
        if (root/'intent.json').exists():
            if read(root/'intent.json')!=intent and not self.readmitted(root/'intent.json',intent): raise ValueError('stage identity changed')
        else: write_new(root/'intent.json',intent)
        return None

    def operation(self, stage, name, payload, action, *, recover=False):
        """Reuse a finished operation; at most 3 starts, with no unknown side effect retried."""
        root=self.root/stage/name;root.mkdir(parents=True,exist_ok=True)
        intent={**self.identity,'payload':payload,'payload_sha256':object_digest(payload)}
        if (root/'intent.json').exists():
            if read(root/'intent.json')!=intent and not self.readmitted(root/'intent.json',intent): raise ValueError('operation inputs changed')
        else: write_new(root/'intent.json',intent)
        attempts=sorted(root.glob('attempt_*'))
        if attempts:
            last=attempts[-1]
            if (last/'complete.json').exists():
                record=read(last/'complete.json')
                for name,sha in record['bindings'].items():
                    if digest(last/name)!=sha:raise ValueError('operation evidence changed')
                return read(last/'output.json')
            refused=verified_failure(last,refused=True)
            if not refused:
                if not recover:raise RecoveryRequired('partial operation requires explicit recovery')
                if not retryable_empty(last):
                    raise RecoveryRequired('unknown or partial effects; retain without resampling')
            consumed=sum(not verified_failure(p,refused=True) for p in attempts)
            if consumed>=3:raise RecoveryRequired('A4 infrastructure cap of 3 exhausted')
            from recovery import refusal_count
            if refusal_count(root)>=120:raise RecoveryRequired('lease refusal cap of 120 exhausted')
        attempt=root/f'attempt_{len(attempts)+1:02d}';attempt.mkdir()
        write_new(attempt/'started.json',{**self.identity,'pid':os.getpid(),'started_unix':time.time()})
        try:
            output=action(attempt,payload)
        except BaseException:
            record_failure(attempt)
            raise
        write_new(attempt/'output.json',output)
        write_new(attempt/'complete.json',{'bindings':tree_bindings(attempt)})
        return output

    def statistic(self, stage, callback):
        root=self.root/stage
        if (root/'statistic.json').exists(): return read(root/'statistic.json')
        # Reservation intentionally survives a crash before the result is durable.
        write_new(root/'statistics_reserved.json',{**self.identity,'started_unix':time.time()})
        result=callback();write_new(root/'statistic.json',result);return result

    def finish(self, stage, result):
        root=self.root/stage;intent=read(root/'intent.json')
        record={**intent,**self.identity,'status':result['status'],'result':result,'artifacts':tree_bindings(root)}
        write_new(root/'receipt.json',record)
        return record
