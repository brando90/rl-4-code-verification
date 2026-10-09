"""TLDR: Owned collect-only service lifecycle for exact six-rating online batches."""
from __future__ import annotations

import json
from pathlib import Path
import subprocess

import owned_processes as children


class RegisteredSubprocess:
    """Preserve the frozen deployment implementation; register children before exec."""
    def __getattr__(self, name):
        return getattr(subprocess, name)

    def Popen(self, args, **kwargs):
        kind = 'e09_judge_tunnel' if 'cloudflared' in str(args[0]) else 'e09_judge_service'
        return children.spawn(args, kind=kind, **kwargs)


class JudgeService:
    def __init__(self):
        self.records = []

    def deploy(self, manifest):
        from deploy_judge_e09 import service
        assert (children.ROOT / 'private/valkyrie.yaml').is_file(), 'Existing approved private route required'
        service.HOST_CONFIG = children.ROOT / 'private/valkyrie.yaml'
        service.LAKE_DIR = children.ROOT / 'lean_runtime'
        service.PACK = Path(manifest['pack_abs'])
        service.BENCHMARK = manifest['benchmark']
        service.PORT = 9741
        service.NAME = 'e09_' + manifest['batch_id'][:16]
        service.EXPECTED_TASKS = manifest['n_tasks']
        service.PUBLIC_RECEIPT = children.ROOT / 'receipts/judge_online/service.json'
        service.subprocess = RegisteredSubprocess()
        with children.registry() as data:
            before = {(r['pid'], r['start_ticks']) for r in data.get('processes', [])}
        try:
            assert service.cmd_deploy(None) == 0
        finally:
            with children.registry() as data:
                self.records = [r for r in data.get('processes', [])
                                if (r['pid'], r['start_ticks']) not in before
                                and r['kind'] in ('e09_judge_service', 'e09_judge_tunnel')]
        self.receipt = children.ROOT / 'private' / f'deployment_{service.NAME}.json'
        assert len(self.records) == 2 and all(children.alive(r) for r in self.records)

    def finish(self, manifest):
        # Called only once both native rating runs are terminal. A coordinator
        # interruption or partially admitted batch preserves the healthy service.
        for record in reversed(self.records):
            children.stop(record)
        from datetime import datetime, timezone
        receipt = json.loads(self.receipt.read_text())
        receipt.update(torn_down_utc=datetime.now(timezone.utc).isoformat(),
                       identity_checked_cleanup=True)
        temp = self.receipt.with_suffix('.tmp')
        temp.write_text(json.dumps(receipt, indent=2, sort_keys=True) + '\n')
        temp.replace(self.receipt)
